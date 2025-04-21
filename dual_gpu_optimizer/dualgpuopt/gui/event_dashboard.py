"""
Event-driven dashboard that uses the enhanced event bus.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import time
import threading
import logging
from typing import Dict, List, Optional, Set

from dualgpuopt.gpu_info import GPU, probe_gpus
from dualgpuopt.services.event_bus import event_bus, GPUMetricsEvent, EventPriority


class EventDrivenDashboard(ttk.Frame):
    """
    GPU Dashboard that subscribes to GPU metrics events.

    This dashboard automatically updates when it receives GPU metrics events
    through the event bus, removing the need for polling.
    """

    def __init__(self, parent: ttk.Frame, gpu_colors: List[str]) -> None:
        """
        Initialize the dashboard tab.

        Args:
            parent: Parent frame
            gpu_colors: List of colors for GPU visualization
        """
        super().__init__(parent, padding=8)
        self.parent = parent
        self.gpu_colors = gpu_colors
        self.columnconfigure(0, weight=1)
        self.logger = logging.getLogger("dualgpuopt.gui.event_dashboard")

        # Mutex for updates to prevent race conditions
        self._update_lock = threading.RLock()

        # Canvas for GPU usage history
        history_frame = ttk.LabelFrame(self, text="GPU Usage History")
        history_frame.grid(row=0, column=0, sticky="news", padx=8, pady=(0, 8))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)

        self.chart_canvas = tk.Canvas(history_frame, height=150, bg="#1a2327")
        self.chart_canvas.grid(row=0, column=0, sticky="news", padx=4, pady=4)

        # Metrics panel
        metrics_frame = ttk.LabelFrame(self, text="Real-time GPU Metrics")
        metrics_frame.grid(row=1, column=0, sticky="news", padx=8, pady=(0, 8))
        metrics_frame.columnconfigure(0, weight=0)  # Label column
        metrics_frame.columnconfigure(1, weight=1)  # Progress bar column
        metrics_frame.columnconfigure(2, weight=0)  # Value column

        # Status bar
        status_frame = ttk.Frame(self)
        status_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        status_frame.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(status_frame, text="Waiting for GPU data...")
        self.status_label.grid(row=0, column=0, sticky="e")

        # UI component dictionaries
        self.gpu_frames: List[ttk.LabelFrame] = []
        self.gpu_progress: Dict[str, ttk.Progressbar] = {}
        self.gpu_labels: Dict[str, ttk.Label] = {}
        self.temp_progress: Dict[str, ttk.Progressbar] = {}
        self.temp_labels: Dict[str, ttk.Label] = {}
        self.power_progress: Dict[str, ttk.Progressbar] = {}
        self.power_labels: Dict[str, ttk.Label] = {}

        # Data storage
        self.gpu_history: Dict[int, List[float]] = {}  # GPU index -> list of utilization percentages
        self.max_history_points = 60  # Store 60 data points (1 minute at 1 sample/sec)
        self.seen_gpus: Set[int] = set()  # Track which GPUs we've seen

        # Subscribe to GPU metrics events with high priority
        event_bus.subscribe_typed(
            GPUMetricsEvent,
            self._handle_gpu_metrics,
            priority=EventPriority.HIGH
        )

        # Initialize with available GPUs from system
        try:
            gpus = probe_gpus()
            if gpus:
                self.initialize_ui_for_gpus(gpus)
            else:
                self.logger.info("No GPUs detected during initialization")
        except Exception as e:
            self.logger.error(f"Error detecting GPUs: {e}")

    def _handle_gpu_metrics(self, event: GPUMetricsEvent) -> None:
        """
        Handle incoming GPU metrics events.

        Args:
            event: The GPU metrics event
        """
        with self._update_lock:
            # Add GPU to seen list if new
            if event.gpu_index not in self.seen_gpus:
                self.seen_gpus.add(event.gpu_index)
                self.logger.info(f"New GPU detected: {event.gpu_index}")

                # Ensure the UI has been initialized for this GPU
                if not self.gpu_frames:
                    # No UI initialized yet, get all GPUs and initialize
                    try:
                        gpus = probe_gpus()
                        self.initialize_ui_for_gpus(gpus)
                    except Exception as e:
                        self.logger.error(f"Error initializing UI for new GPU: {e}")
                        return
                elif not any(f"gpu_{event.gpu_index}" in key for key in self.gpu_progress.keys()):
                    # UI exists but not for this GPU
                    try:
                        self._add_gpu_to_ui(event.gpu_index)
                    except Exception as e:
                        self.logger.error(f"Error adding new GPU to UI: {e}")
                        return

            # Update history data
            if event.gpu_index not in self.gpu_history:
                self.gpu_history[event.gpu_index] = []

            self.gpu_history[event.gpu_index].append(event.utilization)

            # Limit history to max_history_points
            if len(self.gpu_history[event.gpu_index]) > self.max_history_points:
                self.gpu_history[event.gpu_index] = self.gpu_history[event.gpu_index][-self.max_history_points:]

            # Update UI components
            self._update_ui_for_gpu(event)

            # Update status
            self.status_label["text"] = f"Last update: {time.strftime('%H:%M:%S')}"

            # Render history graph
            self.render_history_graph()

    def initialize_ui_for_gpus(self, gpus: List[GPU]) -> None:
        """
        Initialize UI components for the given GPUs.

        Args:
            gpus: List of GPUs to initialize UI for
        """
        with self._update_lock:
            metrics_frame = self.winfo_children()[1]  # Get the metrics frame

            # Clear existing frames if any
            for child in list(metrics_frame.winfo_children()):
                child.destroy()

            self.gpu_frames = []
            self.gpu_progress = {}
            self.gpu_labels = {}
            self.temp_progress = {}
            self.temp_labels = {}
            self.power_progress = {}
            self.power_labels = {}

            # Initialize for each GPU
            for gpu in gpus:
                self._add_gpu_to_ui(gpu.index, gpu.short_name)

    def _add_gpu_to_ui(self, gpu_index: int, gpu_name: Optional[str] = None) -> None:
        """
        Add a single GPU to the UI.

        Args:
            gpu_index: Index of the GPU
            gpu_name: Name of the GPU, or None to use a generic name
        """
        metrics_frame = self.winfo_children()[1]  # Get the metrics frame

        # Use generic name if none provided
        if gpu_name is None:
            gpu_name = f"GPU {gpu_index}"

        # Create frame for this GPU
        frame_title = f"GPU {gpu_index}: {gpu_name}"
        gpu_frame = ttk.LabelFrame(metrics_frame, text=frame_title)
        gpu_frame.grid(row=len(self.gpu_frames), column=0, sticky="ew", padx=4, pady=4)
        gpu_frame.columnconfigure(1, weight=1)

        # GPU utilization
        ttk.Label(gpu_frame, text="Utilization:").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        gpu_prog = ttk.Progressbar(gpu_frame, mode="determinate", maximum=100)
        gpu_prog.grid(row=0, column=1, sticky="ew", padx=4, pady=2)
        gpu_label = ttk.Label(gpu_frame, text="0%", width=8)
        gpu_label.grid(row=0, column=2, sticky="e", padx=4, pady=2)

        # Memory usage
        ttk.Label(gpu_frame, text="Memory:").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        mem_prog = ttk.Progressbar(gpu_frame, mode="determinate", maximum=100)
        mem_prog.grid(row=1, column=1, sticky="ew", padx=4, pady=2)
        mem_label = ttk.Label(gpu_frame, text="0 MB", width=8)
        mem_label.grid(row=1, column=2, sticky="e", padx=4, pady=2)

        # Temperature
        ttk.Label(gpu_frame, text="Temperature:").grid(row=2, column=0, sticky="w", padx=4, pady=2)
        temp_prog = ttk.Progressbar(gpu_frame, mode="determinate", maximum=100)
        temp_prog.grid(row=2, column=1, sticky="ew", padx=4, pady=2)
        temp_label = ttk.Label(gpu_frame, text="0°C", width=8)
        temp_label.grid(row=2, column=2, sticky="e", padx=4, pady=2)

        # Power usage
        ttk.Label(gpu_frame, text="Power:").grid(row=3, column=0, sticky="w", padx=4, pady=2)
        power_prog = ttk.Progressbar(gpu_frame, mode="determinate", maximum=100)
        power_prog.grid(row=3, column=1, sticky="ew", padx=4, pady=2)
        power_label = ttk.Label(gpu_frame, text="0W", width=8)
        power_label.grid(row=3, column=2, sticky="e", padx=4, pady=2)

        # Store references
        self.gpu_frames.append(gpu_frame)
        self.gpu_progress[f"gpu_{gpu_index}"] = gpu_prog
        self.gpu_labels[f"gpu_{gpu_index}"] = gpu_label
        self.gpu_progress[f"mem_{gpu_index}"] = mem_prog
        self.gpu_labels[f"mem_{gpu_index}"] = mem_label
        self.temp_progress[f"temp_{gpu_index}"] = temp_prog
        self.temp_labels[f"temp_{gpu_index}"] = temp_label
        self.power_progress[f"power_{gpu_index}"] = power_prog
        self.power_labels[f"power_{gpu_index}"] = power_label

        # Initialize history for this GPU
        if gpu_index not in self.gpu_history:
            self.gpu_history[gpu_index] = []

    def _update_ui_for_gpu(self, event: GPUMetricsEvent) -> None:
        """
        Update UI components for a specific GPU based on metrics event.

        Args:
            event: GPU metrics event with updated values
        """
        idx = event.gpu_index

        # Update GPU utilization
        if f"gpu_{idx}" in self.gpu_progress:
            self.gpu_progress[f"gpu_{idx}"]["value"] = event.utilization
            self.gpu_labels[f"gpu_{idx}"]["text"] = f"{event.utilization:.1f}%"

        # Update memory usage
        if f"mem_{idx}" in self.gpu_progress:
            # Calculate memory percentage
            mem_pct = 0
            if event.memory_total > 0:
                mem_pct = (event.memory_used / event.memory_total) * 100

            self.gpu_progress[f"mem_{idx}"]["value"] = mem_pct

            # Format memory usage nicely (MB or GB)
            if event.memory_used < 1024:
                mem_text = f"{event.memory_used} MB"
            else:
                mem_text = f"{event.memory_used / 1024:.1f} GB"

            self.gpu_labels[f"mem_{idx}"]["text"] = mem_text

        # Update temperature
        if f"temp_{idx}" in self.temp_progress:
            self.temp_progress[f"temp_{idx}"]["value"] = min(event.temperature, 100)
            self.temp_labels[f"temp_{idx}"]["text"] = f"{event.temperature:.0f}°C"

        # Update power usage
        if f"power_{idx}" in self.power_progress:
            # Scale power to percentage (assume 400W max)
            power_pct = min((event.power_draw / 400) * 100, 100)
            self.power_progress[f"power_{idx}"]["value"] = power_pct
            self.power_labels[f"power_{idx}"]["text"] = f"{event.power_draw:.1f}W"

    def render_history_graph(self) -> None:
        """Render the GPU usage history graph with the latest data."""
        if not self.gpu_history:
            return

        canvas = self.chart_canvas
        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width <= 1 or height <= 1:  # Not yet properly sized
            # Use a default size for initial rendering
            width = max(width, 300)
            height = max(height, 150)

        # Clear canvas
        canvas.delete("all")

        # Draw grid lines
        for y in range(0, 101, 20):  # 0%, 20%, 40%, 60%, 80%, 100%
            y_pos = height - (y / 100 * height)
            canvas.create_line(0, y_pos, width, y_pos, fill="#555555", dash=(1, 2))
            canvas.create_text(5, y_pos, text=f"{y}%", anchor="w", fill="#aaaaaa", font=("Helvetica", 7))

        # Plot data for each GPU
        for gpu_index, history in self.gpu_history.items():
            if not history:
                continue

            # Determine color for this GPU
            if gpu_index < len(self.gpu_colors):
                color = self.gpu_colors[gpu_index]
            else:
                # Generate a color if we don't have one assigned
                color = f"#{hash(str(gpu_index)) % 0xFFFFFF:06x}"

            # Create points for the line
            points = []
            for i, value in enumerate(history):
                x = i * (width / max(len(history) - 1, 1))
                y = height - (value / 100 * height)
                points.append((x, y))

            # Draw the line
            if len(points) > 1:
                canvas.create_line(points, fill=color, width=2, smooth=True)

                # Add a label at the end of the line
                canvas.create_text(
                    points[-1][0] + 5, points[-1][1],
                    text=f"GPU {gpu_index}",
                    fill=color,
                    anchor="w",
                    font=("Helvetica", 8)
                )

    def destroy(self) -> None:
        """Clean up resources when widget is destroyed."""
        # Unsubscribe from events
        try:
            event_bus.unsubscribe(GPUMetricsEvent, self._handle_gpu_metrics)
        except Exception as e:
            self.logger.error(f"Error unsubscribing from events: {e}")
        super().destroy()