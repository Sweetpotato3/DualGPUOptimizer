"""
Memory Profiler for GPU memory usage analysis during inference.

This module provides memory usage tracking, pattern analysis, timeline visualization,
and memory leak detection during LLM inference sessions.
"""

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable

# Try to import matplotlib for visualization, but provide fallbacks
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from dualgpuopt.memory.metrics import GPUMemoryStats, MemoryUnit
from dualgpuopt.memory.monitor import get_memory_monitor
from dualgpuopt.error_handler import ErrorCategory, ErrorHandler, ErrorSeverity, handle_exceptions

# Initialize module-level logger
logger = logging.getLogger("DualGPUOpt.MemoryProfiler")

# Type aliases
TimePoint = float
MemoryValue = int
ProfilerCallback = Callable[[Dict[str, Any]], None]


class MemoryEventType(Enum):
    """Types of memory events to track"""
    ALLOCATION = "allocation"       # Memory allocation
    DEALLOCATION = "deallocation"   # Memory release
    GROWTH_SPIKE = "growth_spike"   # Rapid memory growth
    LEAK_DETECTED = "leak_detected" # Potential memory leak
    SESSION_START = "session_start" # Start of profiling session
    SESSION_END = "session_end"     # End of profiling session
    INFERENCE_START = "inference_start" # Start of inference
    INFERENCE_END = "inference_end"     # End of inference


@dataclass
class MemoryEvent:
    """Memory event during inference"""
    timestamp: TimePoint
    event_type: MemoryEventType
    gpu_id: int
    value: MemoryValue = 0
    description: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemorySnapshot:
    """Memory state at a specific time point"""
    timestamp: TimePoint
    memory: Dict[int, GPUMemoryStats]


@dataclass
class MemorySession:
    """Tracking for a memory profiling session"""
    session_id: str
    start_time: TimePoint
    end_time: Optional[TimePoint] = None
    snapshots: List[MemorySnapshot] = field(default_factory=list)
    events: List[MemoryEvent] = field(default_factory=list)
    inference_count: int = 0
    token_count: int = 0


class MemoryProfiler:
    """
    Memory profiling system for GPU memory usage analysis.

    Tracks memory usage patterns, detects anomalies, and provides
    visualizations for memory usage during model inference.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton implementation"""
        if cls._instance is None:
            cls._instance = super(MemoryProfiler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self,
                 sample_interval: float = 0.5,
                 history_size: int = 3600,  # 30 minutes at 0.5s interval
                 leak_detection_threshold: float = 0.05,
                 spike_detection_threshold: float = 0.1):
        """
        Initialize memory profiler

        Args:
            sample_interval: Interval between memory snapshots in seconds
            history_size: Maximum number of snapshots to keep in history
            leak_detection_threshold: Minimum steady growth rate to trigger leak alert
            spike_detection_threshold: Minimum growth rate to trigger spike alert
        """
        if self._initialized:
            return

        self._initialized = True

        # Configuration
        self._sample_interval = sample_interval
        self._history_size = history_size
        self._leak_threshold = leak_detection_threshold
        self._spike_threshold = spike_detection_threshold

        # Memory monitor reference
        self._monitor = get_memory_monitor()

        # Current active session
        self._active_session: Optional[MemorySession] = None
        self._session_history: Dict[str, MemorySession] = {}

        # Timeline data structures
        self._memory_timeline: Dict[int, List[Tuple[TimePoint, MemoryValue]]] = {}
        self._event_timeline: List[MemoryEvent] = []

        # Sliding window for analysis
        self._window_size = 20  # 10 seconds at 0.5s interval
        self._memory_windows: Dict[int, deque] = {}

        # Real-time visualization
        if MATPLOTLIB_AVAILABLE:
            self._figure: Optional[Figure] = None
            self._canvas: Optional[FigureCanvasTkAgg] = None
            self._text_widget = None
        else:
            self._figure = None
            self._canvas = None
            self._text_widget = None
            logger.warning("Matplotlib not available, visualization will be limited to text")

        # Callback registrations
        self._callbacks: Dict[MemoryEventType, List[ProfilerCallback]] = {
            event_type: [] for event_type in MemoryEventType
        }

        # Profiling control
        self._profiling_active = False
        self._profiling_thread = None
        self._stop_profiling = threading.Event()
        self._inference_mode = False

    def start_profiling(self, session_id: Optional[str] = None) -> str:
        """
        Start memory profiling session

        Args:
            session_id: Optional session identifier, auto-generated if not provided

        Returns:
            Session identifier
        """
        if self._profiling_active:
            # End existing session before starting a new one
            self.end_session()

        # Generate session ID if not provided
        if not session_id:
            session_id = f"session_{int(time.time())}"

        # Create new session
        self._active_session = MemorySession(
            session_id=session_id,
            start_time=time.time()
        )

        # Clear timeline data
        self._memory_timeline.clear()
        self._event_timeline.clear()
        self._memory_windows.clear()

        # Record session start event
        self._add_event(
            MemoryEventType.SESSION_START,
            -1,  # All GPUs
            description=f"Started profiling session: {session_id}"
        )

        # Start profiling thread
        self._stop_profiling.clear()
        self._profiling_thread = threading.Thread(
            target=self._profiling_loop,
            daemon=True,
            name="MemoryProfilerThread"
        )
        self._profiling_active = True
        self._profiling_thread.start()

        logger.info(f"Started memory profiling session: {session_id}")
        return session_id

    def end_session(self) -> Optional[str]:
        """
        End current profiling session

        Returns:
            Completed session ID or None if no active session
        """
        if not self._profiling_active or not self._active_session:
            return None

        # Record session end event
        self._add_event(
            MemoryEventType.SESSION_END,
            -1,  # All GPUs
            description=f"Ended profiling session: {self._active_session.session_id}"
        )

        # Stop profiling thread
        self._stop_profiling.set()
        if self._profiling_thread and self._profiling_thread.is_alive():
            self._profiling_thread.join(timeout=2.0)

        # Complete the session
        self._active_session.end_time = time.time()

        # Store in history
        session_id = self._active_session.session_id
        self._session_history[session_id] = self._active_session

        # Clean up
        self._profiling_active = False
        self._active_session = None
        self._inference_mode = False

        logger.info(f"Ended memory profiling session: {session_id}")
        return session_id

    def start_inference(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Mark the start of an inference session for focused analysis

        Args:
            context: Optional context information about the inference

        Returns:
            True if successfully started, False if no active session
        """
        if not self._profiling_active or not self._active_session:
            logger.warning("Cannot start inference - no active profiling session")
            return False

        self._inference_mode = True
        self._active_session.inference_count += 1

        # Track pre-inference memory baseline
        baseline = {}
        for gpu_id, stats in self._monitor.get_all_stats().items():
            baseline[gpu_id] = stats["used_memory_bytes"]

        # Create inference context if not provided
        if context is None:
            context = {}

        context["inference_id"] = self._active_session.inference_count
        context["baseline_memory"] = baseline

        # Record event
        self._add_event(
            MemoryEventType.INFERENCE_START,
            -1,  # All GPUs
            description=f"Started inference #{self._active_session.inference_count}",
            context=context
        )

        logger.debug(f"Started inference tracking #{self._active_session.inference_count}")
        return True

    def end_inference(self, token_count: int = 0, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Mark the end of an inference session and analyze memory changes

        Args:
            token_count: Number of tokens processed in this inference
            context: Optional context information about the inference

        Returns:
            True if successfully ended, False if no active session or not in inference mode
        """
        if not self._profiling_active or not self._active_session or not self._inference_mode:
            logger.warning("Cannot end inference - no active inference or profiling session")
            return False

        # Create inference context if not provided
        if context is None:
            context = {}

        inference_id = self._active_session.inference_count
        context["inference_id"] = inference_id

        # Track post-inference memory
        current_memory = {}
        memory_delta = {}
        baseline = {}

        # Find the matching start event to get baseline memory
        for event in reversed(self._event_timeline):
            if (event.event_type == MemoryEventType.INFERENCE_START and
                event.context.get("inference_id") == inference_id):
                baseline = event.context.get("baseline_memory", {})
                break

        # Calculate memory changes
        for gpu_id, stats in self._monitor.get_all_stats().items():
            current_memory[gpu_id] = stats["used_memory_bytes"]
            if gpu_id in baseline:
                delta = current_memory[gpu_id] - baseline[gpu_id]
                memory_delta[gpu_id] = delta

        context["end_memory"] = current_memory
        context["memory_delta"] = memory_delta

        # Track token count
        self._active_session.token_count += token_count
        context["token_count"] = token_count

        # Analyze for any leaks or unusual memory retention
        total_retained = sum(memory_delta.values())
        if total_retained > 0:
            # Memory retained after inference - potential leak
            retained_mb = total_retained / (1024 * 1024)
            if retained_mb > 10:  # Only report if more than 10 MB retained
                leak_event = self._add_event(
                    MemoryEventType.LEAK_DETECTED,
                    -1,  # All GPUs
                    value=total_retained,
                    description=f"Potential memory leak: {retained_mb:.2f} MB retained after inference",
                    context={"retained_memory": memory_delta, "inference_id": inference_id}
                )
                logger.warning(f"Potential memory leak detected: {retained_mb:.2f} MB retained")

        # Record inference end event
        self._add_event(
            MemoryEventType.INFERENCE_END,
            -1,  # All GPUs
            value=token_count,
            description=f"Ended inference #{inference_id} ({token_count} tokens)",
            context=context
        )

        self._inference_mode = False
        logger.debug(f"Ended inference tracking #{inference_id}")
        return True

    def register_callback(self, event_type: MemoryEventType, callback: ProfilerCallback) -> None:
        """
        Register callback for memory profiling events

        Args:
            event_type: Type of event to trigger callback
            callback: Function to call with event details
        """
        self._callbacks[event_type].append(callback)
        logger.debug(f"Registered callback for {event_type.name} events")

    def unregister_callback(self, event_type: MemoryEventType, callback: ProfilerCallback) -> bool:
        """
        Unregister callback for memory profiling events

        Args:
            event_type: Type of event for the callback
            callback: Function to unregister

        Returns:
            True if callback was found and removed, False otherwise
        """
        if callback in self._callbacks[event_type]:
            self._callbacks[event_type].remove(callback)
            logger.debug(f"Unregistered callback for {event_type.name} events")
            return True
        return False

    def create_visualization(self, parent_widget, width=600, height=400):
        """
        Create memory timeline visualization widget

        Args:
            parent_widget: Tkinter parent widget
            width: Visualization width
            height: Visualization height

        Returns:
            Matplotlib canvas widget or text widget if matplotlib is not available
        """
        # Return different visualization depending on matplotlib availability
        if MATPLOTLIB_AVAILABLE:
            return self._create_matplotlib_visualization(parent_widget, width, height)
        else:
            return self._create_text_visualization(parent_widget, width, height)

    def _create_matplotlib_visualization(self, parent_widget, width=600, height=400):
        """Create matplotlib-based visualization"""
        # Create figure and canvas if needed
        if self._figure is None:
            self._figure = Figure(figsize=(width/100, height/100), dpi=100)
            self._canvas = FigureCanvasTkAgg(self._figure, master=parent_widget)

        # Clear any existing plots
        self._figure.clear()

        # Setup subplot and empty plot
        self._ax = self._figure.add_subplot(111)
        self._ax.set_title("GPU Memory Usage Timeline")
        self._ax.set_xlabel("Time (seconds)")
        self._ax.set_ylabel("Memory Usage (MB)")

        # Initial empty plot with placeholder data
        self._lines = {}
        for gpu_id in range(self._monitor._gpu_count):
            line, = self._ax.plot([], [], label=f"GPU {gpu_id}")
            self._lines[gpu_id] = line

        # Add empty event markers
        self._inference_starts = self._ax.plot([], [], 'g^', markersize=8, label="Inference Start")[0]
        self._inference_ends = self._ax.plot([], [], 'rv', markersize=8, label="Inference End")[0]
        self._memory_spikes = self._ax.plot([], [], 'yo', markersize=8, label="Memory Spike")[0]
        self._memory_leaks = self._ax.plot([], [], 'rx', markersize=10, label="Potential Leak")[0]

        self._ax.legend(loc='upper left')
        self._figure.tight_layout()

        # Register callback to update the plot
        self.register_callback(MemoryEventType.ALLOCATION, self._update_visualization)

        return self._canvas

    def _create_text_visualization(self, parent_widget, width=600, height=400):
        """Create text-based visualization for when matplotlib is not available"""
        import tkinter as tk
        from tkinter import ttk

        # Create a Text widget to display memory data
        if self._text_widget is None:
            frame = ttk.Frame(parent_widget)

            # Create a Text widget with scrollbar
            self._text_widget = tk.Text(frame, width=80, height=20)
            scrollbar = ttk.Scrollbar(frame, command=self._text_widget.yview)
            self._text_widget.configure(yscrollcommand=scrollbar.set)

            # Format and tags
            self._text_widget.tag_configure("header", font=("Arial", 10, "bold"))
            self._text_widget.tag_configure("normal", font=("Courier", 9))
            self._text_widget.tag_configure("warning", foreground="orange")
            self._text_widget.tag_configure("error", foreground="red")
            self._text_widget.tag_configure("event", foreground="blue")

            # Introduction text
            self._text_widget.insert("end", "Memory Profile Timeline (text mode)\n", "header")
            self._text_widget.insert("end", "Install matplotlib for graphical visualization\n\n", "warning")

            # Layout
            self._text_widget.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns")

            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(0, weight=1)

            # Register callback to update the text display
            self.register_callback(MemoryEventType.ALLOCATION, self._update_text_visualization)
            self.register_callback(MemoryEventType.DEALLOCATION, self._update_text_visualization)
            self.register_callback(MemoryEventType.LEAK_DETECTED, self._update_text_visualization)
            self.register_callback(MemoryEventType.INFERENCE_START, self._update_text_visualization)
            self.register_callback(MemoryEventType.INFERENCE_END, self._update_text_visualization)

        return self._text_widget.master

    def _update_text_visualization(self, event_data: Dict[str, Any]) -> None:
        """Update text-based visualization with new memory data"""
        if not self._text_widget:
            return

        # Only update periodically to avoid overwhelming the text widget
        current_time = time.time()
        if not hasattr(self, '_last_text_update') or current_time - self._last_text_update > 1.0:
            self._last_text_update = current_time

            # Clear existing content
            self._text_widget.delete("1.0", "end")
            self._text_widget.insert("end", "Memory Profile Timeline (text mode)\n", "header")

            # Session info
            if self._active_session:
                elapsed = current_time - self._active_session.start_time
                self._text_widget.insert("end", f"Session: {self._active_session.session_id} - Running for {elapsed:.1f}s\n", "normal")
                self._text_widget.insert("end", f"Events: {len(self._event_timeline)}\n\n", "normal")

                # Current memory usage
                self._text_widget.insert("end", "Current Memory Usage:\n", "header")
                for gpu_id in range(self._monitor._gpu_count):
                    stats = self._monitor.get_memory_stats(gpu_id, MemoryUnit.MB)
                    usage_percent = (stats.get("used", 0) / stats.get("total", 1)) * 100

                    # Color code based on usage
                    tag = "normal"
                    if usage_percent > 90:
                        tag = "error"
                    elif usage_percent > 75:
                        tag = "warning"

                    self._text_widget.insert("end", f"GPU {gpu_id}: {stats.get('used', 0):.1f} MB / {stats.get('total', 0):.1f} MB ({usage_percent:.1f}%)\n", tag)

                # Recent events
                self._text_widget.insert("end", "\nRecent Events:\n", "header")

                # Show last 10 events in reverse chronological order
                for event in list(reversed(self._event_timeline))[:10]:
                    event_time = event.timestamp - self._active_session.start_time
                    if event.event_type in [MemoryEventType.LEAK_DETECTED]:
                        tag = "error"
                    elif event.event_type in [MemoryEventType.GROWTH_SPIKE]:
                        tag = "warning"
                    else:
                        tag = "event"

                    self._text_widget.insert("end", f"[{event_time:.1f}s] {event.description}\n", tag)

    def _update_visualization(self, event_data: Dict[str, Any]) -> None:
        """Update the memory timeline visualization"""
        if not MATPLOTLIB_AVAILABLE or not self._figure or not self._canvas:
            return

        # For each GPU, update the line data
        for gpu_id, line in self._lines.items():
            if gpu_id in self._memory_timeline:
                timestamps = [t - self._active_session.start_time for t, _ in self._memory_timeline[gpu_id]]
                memory_values = [m / (1024 * 1024) for _, m in self._memory_timeline[gpu_id]]  # Convert to MB

                line.set_data(timestamps, memory_values)

        # Update event markers
        infer_starts_x, infer_starts_y = [], []
        infer_ends_x, infer_ends_y = [], []
        spikes_x, spikes_y = [], []
        leaks_x, leaks_y = [], []

        # Find the most recent memory value for each event
        for event in self._event_timeline:
            event_time = event.timestamp - self._active_session.start_time

            # Find closest memory value
            memory_value = 0
            if event.gpu_id in self._memory_timeline and self._memory_timeline[event.gpu_id]:
                # Get closest memory value by time
                timeline = self._memory_timeline[event.gpu_id]
                for i, (t, m) in enumerate(timeline):
                    if t >= event.timestamp:
                        memory_value = m / (1024 * 1024)  # Convert to MB
                        break
                    if i == len(timeline) - 1:
                        memory_value = m / (1024 * 1024)  # Use last value

            # Add to appropriate marker list
            if event.event_type == MemoryEventType.INFERENCE_START:
                infer_starts_x.append(event_time)
                infer_starts_y.append(memory_value)
            elif event.event_type == MemoryEventType.INFERENCE_END:
                infer_ends_x.append(event_time)
                infer_ends_y.append(memory_value)
            elif event.event_type == MemoryEventType.GROWTH_SPIKE:
                spikes_x.append(event_time)
                spikes_y.append(memory_value)
            elif event.event_type == MemoryEventType.LEAK_DETECTED:
                leaks_x.append(event_time)
                leaks_y.append(memory_value)

        # Update marker data
        self._inference_starts.set_data(infer_starts_x, infer_starts_y)
        self._inference_ends.set_data(infer_ends_x, infer_ends_y)
        self._memory_spikes.set_data(spikes_x, spikes_y)
        self._memory_leaks.set_data(leaks_x, leaks_y)

        # Reset the view limits
        self._ax.relim()
        self._ax.autoscale_view()

        # Redraw the canvas
        self._canvas.draw_idle()

    def get_session_report(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive memory usage report for a session

        Args:
            session_id: Session to report on, or active session if None

        Returns:
            Dictionary with report data
        """
        # Determine which session to report on
        session = None
        if session_id and session_id in self._session_history:
            session = self._session_history[session_id]
        elif self._active_session:
            session = self._active_session
        else:
            logger.warning("No session available for report generation")
            return {"error": "No session available"}

        # Calculate statistics
        report = {
            "session_id": session.session_id,
            "start_time": session.start_time,
            "end_time": session.end_time if session.end_time else time.time(),
            "duration": (session.end_time if session.end_time else time.time()) - session.start_time,
            "inference_count": session.inference_count,
            "token_count": session.token_count,
            "events": {
                event_type.name: 0 for event_type in MemoryEventType
            },
            "memory_metrics": {},
            "potential_leaks": [],
            "recommendations": []
        }

        # Count events by type
        for event in session.events:
            report["events"][event.event_type.name] += 1

            # Track leak events
            if event.event_type == MemoryEventType.LEAK_DETECTED:
                leak_mb = event.value / (1024 * 1024)
                report["potential_leaks"].append({
                    "timestamp": event.timestamp - session.start_time,
                    "size_mb": leak_mb,
                    "description": event.description,
                    "inference_id": event.context.get("inference_id", "unknown")
                })

        # Memory usage statistics by GPU
        memory_by_gpu = {}
        for snapshot in session.snapshots:
            for gpu_id, stats in snapshot.memory.items():
                if gpu_id not in memory_by_gpu:
                    memory_by_gpu[gpu_id] = []
                memory_by_gpu[gpu_id].append(stats.used_memory)

        # Calculate min, max, avg for each GPU
        for gpu_id, values in memory_by_gpu.items():
            if not values:
                continue

            min_mem = min(values) / (1024 * 1024)
            max_mem = max(values) / (1024 * 1024)
            avg_mem = sum(values) / len(values) / (1024 * 1024)

            report["memory_metrics"][f"GPU_{gpu_id}"] = {
                "min_mb": min_mem,
                "max_mb": max_mem,
                "avg_mb": avg_mem,
                "range_mb": max_mem - min_mem
            }

        # Generate recommendations
        if report["potential_leaks"]:
            report["recommendations"].append(
                "Potential memory leaks detected. Consider reviewing code that runs after inference completes."
            )

        if session.inference_count > 0:
            avg_tokens = session.token_count / session.inference_count
            report["recommendations"].append(
                f"Average of {avg_tokens:.1f} tokens per inference."
            )

        return report

    def export_timeline_data(self, filepath: str, session_id: Optional[str] = None) -> bool:
        """
        Export memory timeline data to CSV file

        Args:
            filepath: Path to save the CSV file
            session_id: Session to export, or active session if None

        Returns:
            True if export successful, False otherwise
        """
        import csv

        # Determine which session to export
        if session_id and session_id in self._session_history:
            memory_timeline = self._session_history[session_id].snapshots
            session_start = self._session_history[session_id].start_time
        elif self._active_session:
            memory_timeline = self._memory_timeline
            session_start = self._active_session.start_time
        else:
            logger.warning("No session available for export")
            return False

        try:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                header = ["timestamp", "seconds_elapsed"]
                for gpu_id in range(self._monitor._gpu_count):
                    header.extend([f"gpu{gpu_id}_used_mb", f"gpu{gpu_id}_free_mb", f"gpu{gpu_id}_percent"])
                writer.writerow(header)

                # Write data based on what we have
                if isinstance(memory_timeline, dict):
                    # Using _memory_timeline structure
                    # First convert to a time-ordered list of snapshots
                    timestamps = set()
                    for gpu_id, data in memory_timeline.items():
                        timestamps.update([t for t, _ in data])

                    # Write each timestamp
                    for timestamp in sorted(timestamps):
                        row = [timestamp, timestamp - session_start]

                        # Placeholder values
                        values = [0] * (self._monitor._gpu_count * 3)

                        # Fill in values we have
                        for gpu_id, data in memory_timeline.items():
                            for t, value in data:
                                if t == timestamp:
                                    idx = gpu_id * 3
                                    values[idx] = value / (1024 * 1024)  # Used MB

                                    # We don't have other metrics in this format
                                    break

                        row.extend(values)
                        writer.writerow(row)
                else:
                    # Using the snapshot list structure
                    for snapshot in sorted(memory_timeline, key=lambda s: s.timestamp):
                        row = [snapshot.timestamp, snapshot.timestamp - session_start]

                        # Placeholder values
                        values = [0] * (self._monitor._gpu_count * 3)

                        # Fill in values from snapshot
                        for gpu_id, stats in snapshot.memory.items():
                            idx = gpu_id * 3
                            values[idx] = stats.used_memory / (1024 * 1024)  # Used MB
                            values[idx+1] = stats.free_memory / (1024 * 1024)  # Free MB
                            values[idx+2] = stats.usage_percent()  # Percent

                        row.extend(values)
                        writer.writerow(row)

            logger.info(f"Exported memory timeline to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to export timeline data: {e}")
            return False

    def _profiling_loop(self) -> None:
        """Main profiling loop that runs in background thread"""
        while not self._stop_profiling.is_set() and self._active_session:
            try:
                # Take a memory snapshot
                self._take_snapshot()

                # Analyze for anomalies
                self._analyze_memory_patterns()

                # Sleep until next sample
                time.sleep(self._sample_interval)
            except Exception as e:
                error_handler = ErrorHandler()
                error_handler.handle_error(
                    exception=e,
                    component="MemoryProfiler",
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.MEMORY_ERROR,
                    message=f"Error in memory profiling loop: {e}"
                )
                time.sleep(self._sample_interval)  # Sleep to avoid tight loop on errors

    @handle_exceptions(component="MemoryProfiler", severity=ErrorSeverity.ERROR)
    def _take_snapshot(self) -> None:
        """Take a snapshot of current memory state"""
        if not self._active_session:
            return

        # Get memory stats for all GPUs
        current_time = time.time()
        memory_stats = self._monitor.get_all_stats()

        # Create snapshot with proper field mappings
        snapshot_memory = {}
        for gpu_id, stats in memory_stats.items():
            # Map fields to match GPUMemoryStats constructor
            snapshot_memory[gpu_id] = GPUMemoryStats(
                gpu_id=gpu_id,
                total_memory=stats.get("total_memory_bytes", 0),
                used_memory=stats.get("used_memory_bytes", 0),
                free_memory=stats.get("free_memory_bytes", 0),
                reserved_memory=stats.get("reserved_memory_bytes", 0),
                cached_memory=stats.get("cached_memory_bytes", 0),
                process_memory=stats.get("process_memory", {}),
                timestamp=stats.get("timestamp", current_time)
            )

        # Create the snapshot
        snapshot = MemorySnapshot(
            timestamp=current_time,
            memory=snapshot_memory
        )

        # Add to session history
        if self._active_session:
            self._active_session.snapshots.append(snapshot)

        # Update timeline data
        for gpu_id, stats in memory_stats.items():
            if gpu_id not in self._memory_timeline:
                self._memory_timeline[gpu_id] = []

            # Add to timeline
            used_memory = stats.get("used_memory_bytes", 0)
            self._memory_timeline[gpu_id].append(
                (current_time, used_memory)
            )

            # Trim timeline if needed
            if len(self._memory_timeline[gpu_id]) > self._history_size:
                self._memory_timeline[gpu_id].pop(0)

            # Update sliding window
            if gpu_id not in self._memory_windows:
                self._memory_windows[gpu_id] = deque(maxlen=self._window_size)

            self._memory_windows[gpu_id].append(
                (current_time, used_memory)
            )

        # Trigger allocation event for each GPU with significant change
        prev_memory = {}
        if len(self._memory_timeline) > 0:
            for gpu_id, timeline in self._memory_timeline.items():
                if len(timeline) > 1:
                    prev_memory[gpu_id] = timeline[-2][1] if len(timeline) > 1 else 0

        for gpu_id, stats in memory_stats.items():
            current_memory = stats.get("used_memory_bytes", 0)
            previous = prev_memory.get(gpu_id, 0)

            # If significant change, record an allocation event
            delta = current_memory - previous
            delta_mb = abs(delta) / (1024 * 1024)

            # Only record if change is > 1 MB
            if delta_mb > 1:
                event_type = MemoryEventType.ALLOCATION if delta > 0 else MemoryEventType.DEALLOCATION
                self._add_event(
                    event_type,
                    gpu_id,
                    value=delta,
                    description=f"{'+' if delta > 0 else '-'}{delta_mb:.2f} MB on GPU {gpu_id}"
                )

    def _analyze_memory_patterns(self) -> None:
        """Analyze memory usage patterns for anomalies"""
        for gpu_id, window in self._memory_windows.items():
            if len(window) < self._window_size:
                continue  # Need full window for analysis

            # Calculate growth rate using linear regression
            timestamps = [(t - window[0][0]) for t, _ in window]  # Normalize times
            memory_values = [m for _, m in window]

            if not timestamps or not memory_values:
                continue

            # Simple linear regression for trend
            n = len(timestamps)
            sum_x = sum(timestamps)
            sum_y = sum(memory_values)
            sum_xx = sum(x*x for x in timestamps)
            sum_xy = sum(x*y for x, y in zip(timestamps, memory_values))

            # Avoid division by zero
            if n * sum_xx - sum_x * sum_x == 0:
                continue

            # Calculate slope (memory growth rate in bytes per second)
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)

            # Check if growth rate indicates potential leak
            if slope > 0:
                # Convert slope to MB/s
                slope_mb_s = slope / (1024 * 1024)

                # Check for spike (rapid growth)
                if slope_mb_s > self._spike_threshold:
                    self._add_event(
                        MemoryEventType.GROWTH_SPIKE,
                        gpu_id,
                        value=int(slope),
                        description=f"Memory growing at {slope_mb_s:.2f} MB/s on GPU {gpu_id}"
                    )

                # Check for leak (steady growth over time)
                elif (self._inference_mode and
                      slope_mb_s > self._leak_threshold and
                      window[-1][1] - window[0][1] > 5 * 1024 * 1024):  # > 5 MB change

                    # Don't report too frequently - check if we already reported recently
                    recent_leak = False
                    recent_time = time.time() - 30  # 30 seconds ago

                    for event in reversed(self._event_timeline[-10:]):
                        if (event.event_type == MemoryEventType.LEAK_DETECTED and
                            event.gpu_id == gpu_id and
                            event.timestamp > recent_time):
                            recent_leak = True
                            break

                    if not recent_leak:
                        self._add_event(
                            MemoryEventType.LEAK_DETECTED,
                            gpu_id,
                            value=int(slope),
                            description=f"Potential memory leak: {slope_mb_s:.2f} MB/s steady growth on GPU {gpu_id}"
                        )

    def _add_event(self, event_type: MemoryEventType, gpu_id: int,
                  value: int = 0, description: str = "",
                  context: Optional[Dict[str, Any]] = None) -> MemoryEvent:
        """
        Add an event to the timeline

        Args:
            event_type: Type of memory event
            gpu_id: GPU ID associated with event
            value: Numeric value for the event
            description: Human-readable description
            context: Additional context data

        Returns:
            Created event object
        """
        if context is None:
            context = {}

        # Create event
        event = MemoryEvent(
            timestamp=time.time(),
            event_type=event_type,
            gpu_id=gpu_id,
            value=value,
            description=description,
            context=context
        )

        # Add to timeline
        self._event_timeline.append(event)

        # Add to session if active
        if self._active_session:
            self._active_session.events.append(event)

        # Trigger callbacks
        event_data = {
            "timestamp": event.timestamp,
            "event_type": event.event_type.name,
            "gpu_id": event.gpu_id,
            "value": event.value,
            "description": event.description,
            "context": event.context
        }

        for callback in self._callbacks.get(event_type, []):
            try:
                callback(event_data)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")

        return event


# Singleton accessor
def get_memory_profiler() -> MemoryProfiler:
    """Get singleton memory profiler instance"""
    return MemoryProfiler()