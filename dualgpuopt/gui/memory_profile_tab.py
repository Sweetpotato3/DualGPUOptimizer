"""
Memory profiling visualization tab for the dashboard.

This module provides a tabbed interface for real-time memory profiling,
including usage timeline visualization and memory leak detection.
"""

import logging
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict

# Import memory profiling API
from dualgpuopt.memory import MemoryEventType, get_memory_profiler

# Initialize logger
logger = logging.getLogger("DualGPUOpt.MemoryProfileTab")


class MemoryProfileTab(ttk.Frame):
    """Memory profiling visualization tab for real-time memory analysis"""

    def __init__(self, parent):
        """
        Initialize memory profile visualization tab

        Args:
        ----
            parent: Parent widget

        """
        super().__init__(parent, padding=10)

        # Get memory profiler instance
        self.profiler = get_memory_profiler()

        # Configure grid layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Controls
        self.rowconfigure(1, weight=1)  # Visualization
        self.rowconfigure(2, weight=0)  # Status

        # Create controls section
        self._create_controls()

        # Create visualization section
        self._create_visualization()

        # Create events and status section
        self._create_status_section()

        # Register for profiler events
        self._register_events()

        # State tracking
        self._active_session = None
        self._inference_active = False
        self._last_update = time.time()
        self._event_count = 0
        self._token_count = 0

    def _create_controls(self):
        """Create control buttons and options"""
        control_frame = ttk.LabelFrame(self, text="Profiler Controls", padding=10)
        control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)
        control_frame.columnconfigure(2, weight=1)
        control_frame.columnconfigure(3, weight=1)
        control_frame.columnconfigure(4, weight=1)

        # Start/Stop profiling
        self.start_btn = ttk.Button(
            control_frame,
            text="Start Profiling",
            command=self._start_profiling,
            width=15,
        )
        self.start_btn.grid(row=0, column=0, padx=5)

        self.stop_btn = ttk.Button(
            control_frame,
            text="Stop Profiling",
            command=self._stop_profiling,
            width=15,
            state="disabled",
        )
        self.stop_btn.grid(row=0, column=1, padx=5)

        # Start/End inference tracking
        self.infer_start_btn = ttk.Button(
            control_frame,
            text="Start Inference",
            command=self._start_inference,
            width=15,
            state="disabled",
        )
        self.infer_start_btn.grid(row=0, column=2, padx=5)

        self.infer_end_btn = ttk.Button(
            control_frame,
            text="End Inference",
            command=self._end_inference,
            width=15,
            state="disabled",
        )
        self.infer_end_btn.grid(row=0, column=3, padx=5)

        # Export data
        self.export_btn = ttk.Button(
            control_frame,
            text="Export Data",
            command=self._export_timeline,
            width=15,
            state="disabled",
        )
        self.export_btn.grid(row=0, column=4, padx=5)

        # Token count entry for inference
        token_frame = ttk.Frame(control_frame)
        token_frame.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(10, 0))
        token_frame.columnconfigure(1, weight=1)

        ttk.Label(token_frame, text="Tokens processed:").grid(row=0, column=0, padx=(0, 5))

        # Token count variable and validation
        self.token_count_var = tk.StringVar(value="1000")
        vcmd = (self.register(self._validate_token_count), "%P")
        self.token_entry = ttk.Entry(
            token_frame,
            textvariable=self.token_count_var,
            validate="key",
            validatecommand=vcmd,
        )
        self.token_entry.grid(row=0, column=1, sticky="ew")

    def _create_visualization(self):
        """Create the visualization components"""
        # Create container for the visualization
        viz_frame = ttk.LabelFrame(self, text="Memory Timeline", padding=10)
        viz_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Create the matplotlib visualization
        try:
            # Check if matplotlib is available through the profiler
            from dualgpuopt.memory.profiler import MATPLOTLIB_AVAILABLE

            if MATPLOTLIB_AVAILABLE:
                self.canvas = self.profiler.create_visualization(viz_frame, width=800, height=400)
                self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

                # Add toolbar
                try:
                    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

                    toolbar = NavigationToolbar2Tk(self.canvas, viz_frame)
                    toolbar.update()
                    self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                except Exception as e:
                    logger.warning(f"Could not create matplotlib toolbar: {e}")
            else:
                # Use text-based visualization
                text_widget = self.profiler.create_visualization(viz_frame, width=800, height=400)
                text_widget.pack(fill=tk.BOTH, expand=True)
                self.canvas = None
                logger.info("Using text-based visualization (matplotlib not available)")

        except Exception as e:
            logger.error(f"Error creating visualization: {e}")
            error_label = ttk.Label(
                viz_frame,
                text=f"Error creating visualization: {e}\nMake sure matplotlib is installed.",
                foreground="red",
            )
            error_label.pack(fill=tk.BOTH, expand=True)
            self.canvas = None

    def _create_status_section(self):
        """Create the status and events section"""
        status_frame = ttk.LabelFrame(self, text="Memory Events", padding=10)
        status_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        status_frame.columnconfigure(0, weight=1)

        # Status line
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        # Create event list
        events_frame = ttk.Frame(status_frame)
        events_frame.grid(row=1, column=0, sticky="ew")
        events_frame.columnconfigure(0, weight=1)

        # Create a Text widget with scrollbar for events
        self.event_text = tk.Text(events_frame, height=8, width=80, wrap="word")
        scrollbar = ttk.Scrollbar(events_frame, command=self.event_text.yview)
        self.event_text.configure(yscrollcommand=scrollbar.set)

        self.event_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Configure text tags for different event types
        self.event_text.tag_configure("allocation", foreground="blue")
        self.event_text.tag_configure("deallocation", foreground="green")
        self.event_text.tag_configure("spike", foreground="orange")
        self.event_text.tag_configure("leak", foreground="red")
        self.event_text.tag_configure("inference", foreground="purple")
        self.event_text.tag_configure("session", foreground="black")

    def _register_events(self):
        """Register for profiler events"""
        # Register for all event types
        for event_type in MemoryEventType:
            self.profiler.register_callback(event_type, self._handle_event)

    def _handle_event(self, event_data: Dict[str, Any]):
        """
        Handle profiler events

        Args:
        ----
            event_data: Event data dictionary

        """
        # Throttle updates to avoid overwhelming the UI
        current_time = time.time()
        if current_time - self._last_update < 0.1:
            return

        self._last_update = current_time
        self._event_count += 1

        # Determine event type and style
        event_type = event_data.get("event_type", "")
        tag = "session"  # default

        if event_type in ["ALLOCATION", "DEALLOCATION"]:
            tag = "allocation" if event_type == "ALLOCATION" else "deallocation"
        elif event_type in ["GROWTH_SPIKE"]:
            tag = "spike"
        elif event_type in ["LEAK_DETECTED"]:
            tag = "leak"
        elif event_type in ["INFERENCE_START", "INFERENCE_END"]:
            tag = "inference"

        # Format timestamp
        if self._active_session:
            session_start = self.profiler._active_session.start_time
            elapsed = event_data.get("timestamp", 0) - session_start
            time_str = f"[{elapsed:.2f}s] "
        else:
            time_str = f"[{event_data.get('timestamp', 0):.2f}] "

        # Add event to text widget
        self.event_text.insert(
            "end", time_str + event_data.get("description", "Unknown event") + "\n", tag
        )
        self.event_text.see("end")  # Scroll to see latest event

        # Update status line with event count
        self.status_var.set(
            f"Events: {self._event_count} | Active session: {self._active_session or 'None'}"
        )

    def _validate_token_count(self, value):
        """Validate token count entry"""
        if value == "":
            return True

        try:
            count = int(value)
            return count >= 0
        except:
            return False

    def _start_profiling(self):
        """Start memory profiling session"""
        self._active_session = self.profiler.start_profiling()

        # Clear event log
        self.event_text.delete("1.0", "end")
        self._event_count = 0

        # Update button states
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.infer_start_btn.configure(state="normal")
        self.export_btn.configure(state="normal")

        # Update status
        self.status_var.set(f"Started profiling session: {self._active_session}")

    def _stop_profiling(self):
        """Stop memory profiling session"""
        if self._inference_active:
            self._end_inference()

        session_id = self.profiler.end_session()

        # Update button states
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.infer_start_btn.configure(state="disabled")
        self.infer_end_btn.configure(state="disabled")

        # Update status
        self.status_var.set(f"Ended profiling session: {session_id}")

        # Show summary dialog with report
        self._show_session_report(session_id)

    def _start_inference(self):
        """Start inference tracking"""
        if not self._active_session:
            messagebox.showerror("Error", "No active profiling session")
            return

        # Start inference in profiler
        self.profiler.start_inference()
        self._inference_active = True

        # Update button states
        self.infer_start_btn.configure(state="disabled")
        self.infer_end_btn.configure(state="normal")

        # Update status
        self.status_var.set(f"Inference tracking active - session: {self._active_session}")

    def _end_inference(self):
        """End inference tracking"""
        if not self._active_session or not self._inference_active:
            return

        # Get token count
        try:
            token_count = int(self.token_count_var.get())
        except:
            token_count = 0

        # End inference in profiler
        self.profiler.end_inference(token_count=token_count)
        self._inference_active = False
        self._token_count += token_count

        # Update button states
        self.infer_start_btn.configure(state="normal")
        self.infer_end_btn.configure(state="disabled")

        # Update status
        self.status_var.set(f"Inference completed - Total tokens: {self._token_count}")

    def _export_timeline(self):
        """Export memory timeline data to CSV"""
        if not self._active_session:
            messagebox.showerror("Error", "No active profiling session")
            return

        # Ask for file location
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Memory Timeline",
        )

        if not filepath:
            return

        # Export data
        success = self.profiler.export_timeline_data(filepath)

        if success:
            messagebox.showinfo("Export Successful", f"Memory timeline exported to {filepath}")
        else:
            messagebox.showerror("Export Failed", "Failed to export memory timeline")

    def _show_session_report(self, session_id):
        """Show session report dialog"""
        report = self.profiler.get_session_report(session_id)

        if not report or "error" in report:
            return

        # Create dialog
        dialog = tk.Toplevel(self)
        dialog.title(f"Memory Profile Report: {session_id}")
        dialog.minsize(500, 400)

        # Create report content
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Session info
        ttk.Label(frame, text="Session Summary", font=("Arial", 12, "bold")).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 10),
        )

        # Basic stats
        duration = report.get("duration", 0)
        minutes = int(duration // 60)
        seconds = int(duration % 60)

        ttk.Label(frame, text="Duration:").grid(row=1, column=0, sticky="w")
        ttk.Label(frame, text=f"{minutes}m {seconds}s").grid(row=1, column=1, sticky="w")

        ttk.Label(frame, text="Inference Count:").grid(row=2, column=0, sticky="w")
        ttk.Label(frame, text=str(report.get("inference_count", 0))).grid(
            row=2, column=1, sticky="w"
        )

        ttk.Label(frame, text="Token Count:").grid(row=3, column=0, sticky="w")
        ttk.Label(frame, text=str(report.get("token_count", 0))).grid(row=3, column=1, sticky="w")

        # Memory metrics
        ttk.Separator(frame, orient="horizontal").grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=10,
        )

        ttk.Label(frame, text="Memory Metrics", font=("Arial", 12, "bold")).grid(
            row=5,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 10),
        )

        row = 6
        for gpu_id, metrics in report.get("memory_metrics", {}).items():
            ttk.Label(frame, text=f"{gpu_id}:").grid(row=row, column=0, sticky="w")

            min_mb = metrics.get("min_mb", 0)
            max_mb = metrics.get("max_mb", 0)
            avg_mb = metrics.get("avg_mb", 0)

            ttk.Label(
                frame, text=f"Min: {min_mb:.1f} MB | Max: {max_mb:.1f} MB | Avg: {avg_mb:.1f} MB"
            ).grid(
                row=row,
                column=1,
                sticky="w",
            )
            row += 1

        # Potential leaks
        ttk.Separator(frame, orient="horizontal").grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=10,
        )
        row += 1

        ttk.Label(frame, text="Potential Memory Leaks", font=("Arial", 12, "bold")).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 10),
        )
        row += 1

        leaks = report.get("potential_leaks", [])
        if leaks:
            for i, leak in enumerate(leaks):
                ttk.Label(frame, text=f"Leak {i+1}:").grid(row=row, column=0, sticky="w")
                ttk.Label(
                    frame,
                    text=f"{leak.get('size_mb', 0):.1f} MB at {leak.get('timestamp', 0):.1f}s",
                ).grid(
                    row=row,
                    column=1,
                    sticky="w",
                )
                row += 1
        else:
            ttk.Label(frame, text="No memory leaks detected").grid(
                row=row,
                column=0,
                columnspan=2,
                sticky="w",
            )
            row += 1

        # Recommendations
        ttk.Separator(frame, orient="horizontal").grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=10,
        )
        row += 1

        ttk.Label(frame, text="Recommendations", font=("Arial", 12, "bold")).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 10),
        )
        row += 1

        recommendations = report.get("recommendations", [])
        if recommendations:
            for i, rec in enumerate(recommendations):
                ttk.Label(frame, text=f"{i+1}.").grid(row=row, column=0, sticky="nw")
                ttk.Label(frame, text=rec, wraplength=400).grid(row=row, column=1, sticky="w")
                row += 1
        else:
            ttk.Label(frame, text="No specific recommendations").grid(
                row=row,
                column=0,
                columnspan=2,
                sticky="w",
            )

        # Close button
        ttk.Button(frame, text="Close", command=dialog.destroy).grid(
            row=row + 1,
            column=0,
            columnspan=2,
            pady=20,
        )

    def destroy(self):
        """Clean up resources when tab is destroyed"""
        # End any active profiling session
        if self._active_session:
            try:
                self.profiler.end_session()
            except:
                pass

        super().destroy()


# Test function to run the memory profiler tab standalone
def run_memory_profile_tab():
    """Run the memory profile tab as a standalone application"""
    root = tk.Tk()
    root.title("Memory Profiler")
    root.geometry("800x700")

    # Set up the main frame
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Create profile tab
    profile_tab = MemoryProfileTab(main_frame)
    profile_tab.pack(fill=tk.BOTH, expand=True)

    # Start the main loop
    root.mainloop()


if __name__ == "__main__":
    run_memory_profile_tab()
