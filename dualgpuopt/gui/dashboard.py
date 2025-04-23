"""
GPU monitoring dashboard for real-time metrics visualization
"""
import logging
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict

from ..telemetry import GPUMetrics, get_telemetry_service

# Try to import VRAM reset functionality
try:
    from ..vram_reset import reset_vram

    VRAM_RESET_AVAILABLE = True
except ImportError:
    VRAM_RESET_AVAILABLE = False

# Try to import memory profiler tab
try:
    from .memory_profile_tab import MemoryProfileTab

    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False

# Initialize logger
logger = logging.getLogger("DualGPUOpt.Dashboard")


class GPUMonitorFrame(ttk.Frame):
    """Frame showing metrics for a single GPU"""

    def __init__(self, parent, gpu_id: int, gpu_name: str):
        """
        Initialize GPU monitor frame

        Args:
        ----
            parent: Parent widget
            gpu_id: GPU identifier
            gpu_name: GPU name to display
        """
        super().__init__(parent, padding=10, relief="ridge", borderwidth=1, style="Inner.TFrame")
        self.gpu_id = gpu_id
        self.gpu_name = gpu_name

        # Configure grid layout
        self.columnconfigure(0, weight=0)  # Label column
        self.columnconfigure(1, weight=1)  # Value/progress column
        self.columnconfigure(2, weight=0)  # Units column

        # Header with GPU name
        self.header = ttk.Label(
            self,
            text=f"GPU {self.gpu_id}: {self.gpu_name}",
            font=("Arial", 12, "bold"),
            style="Inner.TLabel",
        )
        self.header.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        # Create monitoring metrics
        metrics = [
            ("Utilization", "%", 0, 100),
            ("Memory", "%", 0, 100),
            ("Temperature", "°C", 30, 90),
            ("Power", "W", 0, 350),
            ("Fan", "%", 0, 100),
        ]

        self.progress_bars = {}
        self.value_labels = {}
        self.metric_frames = {}

        for i, (name, unit, _min_val, max_val) in enumerate(metrics):
            # Create frame for this metric
            frame = ttk.Frame(self, style="Inner.TFrame")
            frame.grid(row=i + 1, column=0, columnspan=3, sticky="ew", pady=(0, 5))
            self.metric_frames[name.lower()] = frame

            # Metric label
            ttk.Label(frame, text=f"{name}:", width=12, anchor="e", style="Inner.TLabel").pack(
                side=tk.LEFT, padx=(0, 5)
            )

            # Progress bar
            progress = ttk.Progressbar(frame, length=180, maximum=max_val)
            progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
            self.progress_bars[name.lower()] = progress

            # Value label
            value_label = ttk.Label(
                frame, text=f"0 {unit}", width=8, anchor="w", style="Inner.TLabel"
            )
            value_label.pack(side=tk.LEFT)
            self.value_labels[name.lower()] = value_label

        # Additional metrics (without progress bars)
        self.clock_label = ttk.Label(self, text="Clocks: 0 MHz / 0 MHz", style="Inner.TLabel")
        self.clock_label.grid(row=len(metrics) + 1, column=0, columnspan=3, sticky="w", pady=(5, 0))

        self.pcie_label = ttk.Label(self, text="PCIe: 0 MB/s TX, 0 MB/s RX", style="Inner.TLabel")
        self.pcie_label.grid(row=len(metrics) + 2, column=0, columnspan=3, sticky="w")

    def update_metrics(self, metrics: GPUMetrics) -> None:
        """
        Update displayed metrics

        Args:
        ----
            metrics: New GPU metrics to display
        """
        # Update utilization
        self.progress_bars["utilization"]["value"] = metrics.utilization
        self.value_labels["utilization"].config(text=f"{metrics.utilization}%")

        # Update memory
        mem_percent = metrics.memory_percent
        self.progress_bars["memory"]["value"] = mem_percent
        self.value_labels["memory"].config(text=f"{mem_percent:.1f}%")

        # Update temperature with color coding
        self.progress_bars["temperature"]["value"] = metrics.temperature
        self.value_labels["temperature"].config(text=f"{metrics.temperature}°C")

        if metrics.temperature >= 80:
            self.value_labels["temperature"].config(foreground="red")
        elif metrics.temperature >= 70:
            self.value_labels["temperature"].config(foreground="orange")
        else:
            self.value_labels["temperature"].config(foreground="green")

        # Update power
        self.progress_bars["power"]["value"] = metrics.power_usage
        self.value_labels["power"].config(text=f"{metrics.power_usage:.1f}W")

        # Update fan
        self.progress_bars["fan"]["value"] = metrics.fan_speed
        self.value_labels["fan"].config(text=f"{metrics.fan_speed}%")

        # Update clock speeds
        self.clock_label.config(
            text=f"Clocks: {metrics.clock_sm} MHz / {metrics.clock_memory} MHz",
        )

        # Update PCIe bandwidth
        tx_mb = metrics.pcie_tx / 1024  # Convert to MB/s
        rx_mb = metrics.pcie_rx / 1024  # Convert to MB/s
        self.pcie_label.config(
            text=f"PCIe: {tx_mb:.1f} MB/s TX, {rx_mb:.1f} MB/s RX",
        )


class MetricsView(ttk.Frame):
    """GPU metrics dashboard frame"""

    def __init__(self, parent):
        """
        Initialize the metrics view widget

        Args:
        ----
            parent: Parent widget
        """
        super().__init__(parent, padding=10)

        # Header section
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header_frame,
            text="GPU Metrics Monitor",
            font=("Arial", 16, "bold"),
        ).pack(side=tk.LEFT)

        # Add VRAM reset button if available
        if VRAM_RESET_AVAILABLE:
            reset_btn = ttk.Button(
                header_frame,
                text="Reset VRAM",
                command=self._reset_vram,
            )
            reset_btn.pack(side=tk.RIGHT, padx=5)

        self.status_label = ttk.Label(
            header_frame,
            text="Status: Connecting...",
            foreground="gray",
        )
        self.status_label.pack(side=tk.RIGHT)

        # Main content area with a background frame - helps with theming
        content_container = ttk.LabelFrame(
            self, text="GPU Metrics", padding=10, style="TLabelframe"
        )
        content_container.pack(fill=tk.BOTH, expand=True)

        # Main content area - will hold GPU monitor frames
        self.content_frame = ttk.Frame(content_container, style="Inner.TFrame")
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # GPU monitor frames - will be populated when metrics arrive
        self.gpu_frames: Dict[int, GPUMonitorFrame] = {}

        # Start telemetry service
        self.telemetry = get_telemetry_service()
        self.telemetry.register_callback(self._on_metrics_update)

        # Last updated timestamp
        self.last_update = 0

        # Start telemetry if it's not already running
        if not self.telemetry.running:
            try:
                self.telemetry.start()
                self.status_label.config(text="Status: Connected", foreground="green")
            except Exception as e:
                logger.error(f"Failed to start telemetry: {e}")
                self.status_label.config(text="Status: Error", foreground="red")

    def _on_metrics_update(self, metrics: Dict[int, GPUMetrics]) -> None:
        """
        Callback for telemetry updates

        Args:
        ----
            metrics: Dictionary of GPU ID to metrics
        """
        # Update no more than once every 100ms to avoid overwhelming the UI
        current_time = time.time()
        if current_time - self.last_update < 0.1:
            return

        self.last_update = current_time

        # Create frames for any new GPUs
        for gpu_id, gpu_metrics in metrics.items():
            if gpu_id not in self.gpu_frames:
                # Create a new frame for this GPU
                frame = GPUMonitorFrame(
                    self.content_frame,
                    gpu_id=gpu_id,
                    gpu_name=gpu_metrics.name,
                )
                frame.pack(fill=tk.X, pady=(0, 10))
                self.gpu_frames[gpu_id] = frame

            # Update the metrics
            self.gpu_frames[gpu_id].update_metrics(gpu_metrics)

    def _reset_vram(self) -> None:
        """Reset VRAM on all GPUs"""
        if not VRAM_RESET_AVAILABLE:
            messagebox.showerror("Error", "VRAM reset functionality not available")
            return

        try:
            # Call reset_vram and get ResetResult object
            result = reset_vram()

            # Access the fields directly from the ResetResult object
            if result.success:
                if result.memory_reclaimed > 0:
                    messagebox.showinfo(
                        "VRAM Reset", f"Successfully reclaimed {result.memory_reclaimed} MB of VRAM"
                    )
                    self.status_label.config(
                        text=f"Status: Reclaimed {result.memory_reclaimed} MB", foreground="green"
                    )
                else:
                    messagebox.showinfo("VRAM Reset", "No VRAM was reclaimed")
                    self.status_label.config(text="Status: No VRAM reclaimed", foreground="orange")
            else:
                messagebox.showwarning("VRAM Reset", f"Reset operation failed: {result.message}")
                self.status_label.config(text="Status: Reset failed", foreground="red")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset VRAM: {e}")
            logger.error(f"VRAM reset error: {e}")
            self.status_label.config(text="Status: VRAM reset error", foreground="red")


class DashboardView(ttk.Frame):
    """GPU monitoring dashboard widget with tabbed interface"""

    def __init__(self, parent):
        """
        Initialize the dashboard widget

        Args:
        ----
            parent: Parent widget
        """
        super().__init__(parent, padding=10)

        # Header section
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header_frame,
            text="GPU Monitoring Dashboard",
            font=("Arial", 16, "bold"),
        ).pack(side=tk.LEFT)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create metrics tab
        self.metrics_tab = MetricsView(self.notebook)
        self.notebook.add(self.metrics_tab, text="GPU Metrics")

        # Create memory profiler tab if available
        if MEMORY_PROFILER_AVAILABLE:
            try:
                self.memory_profile_tab = MemoryProfileTab(self.notebook)
                self.notebook.add(self.memory_profile_tab, text="Memory Profiler")
                logger.info("Memory profiler tab added to dashboard")
            except Exception as e:
                logger.error(f"Failed to create memory profiler tab: {e}")
                MEMORY_PROFILER_AVAILABLE = False

    def destroy(self) -> None:
        """Clean up resources when widget is destroyed"""
        # Stop the telemetry service if we started it
        if self.metrics_tab.telemetry.running:
            self.metrics_tab.telemetry.stop()

        super().destroy()


# Test function to run the dashboard standalone
def run_dashboard():
    """Run the dashboard as a standalone application"""
    root = tk.Tk()
    root.title("GPU Monitoring Dashboard")
    root.geometry("800x700")

    # Set up the main frame
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Create dashboard
    dashboard = DashboardView(main_frame)
    dashboard.pack(fill=tk.BOTH, expand=True)

    # Start the main loop
    root.mainloop()


if __name__ == "__main__":
    run_dashboard()
