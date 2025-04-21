"""
Dashboard tab for the DualGPUOptimizer GUI.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import time
from typing import Dict, List, Tuple, Any, Optional

# Try to import ttkbootstrap Tooltip
try:
    from ttkbootstrap.tooltip import ToolTip
    TOOLTIP_AVAILABLE = True
except ImportError:
    TOOLTIP_AVAILABLE = False

# Import constants from shared module
<<<<<<< HEAD
from dualgpuopt.gui.constants import (
    PAD,
    DEFAULT_CHART_BG,
    DEFAULT_CHART_FG,
    GPU_COLORS, # Use the dictionary mapping
    GRID_LINE_COLOR,
    LIGHT_FOREGROUND,
    PURPLE_PRIMARY,
    PURPLE_HIGHLIGHT,
    BLUE_ACCENT,
    PINK_ACCENT,
    CYAN_ACCENT,
    ORANGE_ACCENT
)
=======
from dualgpuopt.gui.constants import PAD, DEFAULT_CHART_BG
>>>>>>> 199829b (Update documentation for DualGPUOptimizer to provide a high-level overview of GPU optimization and model inference systems. Organized content into key components: Core GPU Management, Model Optimization Engine, Command System, Monitoring Dashboard, and State Management. Enhanced glob patterns for improved file matching and clarified key implementation files, ensuring comprehensive coverage of system functionalities and integration points.)
from dualgpuopt.gpu_info import GPU
from dualgpuopt.telemetry import GpuTelemetry # Use the specific type hint


class GpuDashboard(ttk.Frame):
    """GPU Dashboard tab that shows real-time GPU metrics."""

    def __init__(self, parent: ttk.Frame, gpu_info_service: Any, telemetry_service: GpuTelemetry) -> None:
        """
        Initialize the dashboard tab.

        Args:
            parent: Parent frame
            gpu_info_service: Service providing GPU information
            telemetry_service: Service providing telemetry data
        """
        super().__init__(parent, padding=PAD)
        self.parent = parent
        self.gpu_info = gpu_info_service
        self.telemetry = telemetry_service
        self.gpus = self.gpu_info.get_gpus() # Get initial GPU list
        self.columnconfigure(0, weight=1)
<<<<<<< HEAD

        # Use the GPU_COLORS dictionary from constants
        self.gpu_colors = GPU_COLORS
=======
>>>>>>> 199829b (Update documentation for DualGPUOptimizer to provide a high-level overview of GPU optimization and model inference systems. Organized content into key components: Core GPU Management, Model Optimization Engine, Command System, Monitoring Dashboard, and State Management. Enhanced glob patterns for improved file matching and clarified key implementation files, ensuring comprehensive coverage of system functionalities and integration points.)

        # Canvas for GPU usage history
        history_frame = ttk.LabelFrame(self, text="GPU Usage History")
        history_frame.grid(row=0, column=0, sticky="news", padx=PAD, pady=(0, PAD))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)

<<<<<<< HEAD
        # Use background color from constants
        self.chart_canvas = tk.Canvas(history_frame, height=150, bg=DEFAULT_CHART_BG)
=======
        self.chart_canvas = tk.Canvas(history_frame, height=150, bg=DEFAULT_CHART_BG)
>>>>>>> 199829b (Update documentation for DualGPUOptimizer to provide a high-level overview of GPU optimization and model inference systems. Organized content into key components: Core GPU Management, Model Optimization Engine, Command System, Monitoring Dashboard, and State Management. Enhanced glob patterns for improved file matching and clarified key implementation files, ensuring comprehensive coverage of system functionalities and integration points.)
        self.chart_canvas.grid(row=0, column=0, sticky="news", padx=PAD/2, pady=PAD/2)

        # GPU metrics grid
        metrics_frame = ttk.LabelFrame(self, text="Real-time GPU Metrics")
        metrics_frame.grid(row=1, column=0, sticky="news", padx=PAD, pady=(0, PAD))
        metrics_frame.columnconfigure(1, weight=1)  # Progress bar column takes weight
        # metrics_frame.columnconfigure(0, weight=0) # Label column (default)
        # metrics_frame.columnconfigure(2, weight=0) # Value column (default)

        # Create metric rows for each GPU
        self.gpu_frames = []
        self.gpu_progress = {}
        self.gpu_labels = {}

        # Create PCIe throughput frame
        pcie_frame = ttk.LabelFrame(self, text="PCIe Bandwidth")
        pcie_frame.grid(row=2, column=0, sticky="news", padx=PAD, pady=(0, PAD))
        pcie_frame.columnconfigure(1, weight=1)  # Value column takes weight

        self.pcie_labels = {}

        # Create temperature and power frame
        temp_power_frame = ttk.LabelFrame(self, text="Temperature & Power")
        temp_power_frame.grid(row=3, column=0, sticky="news", padx=PAD, pady=(0, PAD))
        temp_power_frame.columnconfigure(1, weight=1) # Progress bar column takes weight

        self.temp_progress = {}
        self.temp_labels = {}
        self.power_progress = {}
        self.power_labels = {}

        # Create clock speeds frame
        clock_frame = ttk.LabelFrame(self, text="Clock Speeds")
        clock_frame.grid(row=4, column=0, sticky="news", padx=PAD, pady=(0, PAD))
        clock_frame.columnconfigure(1, weight=1) # Progress bar column takes weight

        self.graphics_clock_progress = {}
        self.graphics_clock_labels = {}
        self.memory_clock_progress = {}
        self.memory_clock_labels = {}

        # Last update time
        status_frame = ttk.Frame(self)
        status_frame.grid(row=5, column=0, sticky="ew", padx=PAD, pady=(0, PAD))
        status_frame.columnconfigure(0, weight=1)

        self.last_update_label = ttk.Label(status_frame, text="Last update: Never")
        self.last_update_label.grid(row=0, column=0, sticky="e")

        # Initialize UI elements for detected GPUs
        self.initialize_gpu_metrics(self.gpus)

        # Initialize with empty data history
        self.tele_hist = []

    def initialize_gpu_metrics(self, gpus: List[GPU]) -> None:
        """
        Initialize the GPU metrics UI based on the provided list of GPUs.
        Clears existing widgets before creating new ones if called multiple times.

        Args:
            gpus: List of GPU objects
        """
        # --- Clear previous widgets if any ---
        metrics_frame = self.winfo_children()[1] # metrics_frame LabelFrame
        pcie_frame = self.winfo_children()[2]    # pcie_frame LabelFrame
        temp_power_frame = self.winfo_children()[3] # temp_power_frame LabelFrame
        clock_frame = self.winfo_children()[4]      # clock_frame LabelFrame

        for frame in self.gpu_frames: frame.destroy()
        for widget in pcie_frame.winfo_children(): widget.destroy()
        for widget in temp_power_frame.winfo_children(): widget.destroy()
        for widget in clock_frame.winfo_children(): widget.destroy()

        self.gpu_frames.clear()
        self.gpu_progress.clear()
        self.gpu_labels.clear()
        self.pcie_labels.clear()
        self.temp_progress.clear()
        self.temp_labels.clear()
        self.power_progress.clear()
        self.power_labels.clear()
        self.graphics_clock_progress.clear()
        self.graphics_clock_labels.clear()
        self.memory_clock_progress.clear()
        self.memory_clock_labels.clear()

        # --- Setup metrics frame for each GPU ---
        for i, gpu in enumerate(gpus):
            # Determine progress bar style based on GPU index
            # Cycle through defined accent colors for progress bars
            primary_color_key = i % len(self.gpu_colors) # Cycle through keys 0, 1, 2, 3...
            primary_style = self.get_progress_style(self.gpu_colors.get(primary_color_key, PURPLE_PRIMARY))
            memory_style = self.get_progress_style(self.gpu_colors.get("memory", PINK_ACCENT))

            gpu_frame = ttk.LabelFrame(metrics_frame, text=f"GPU {gpu.index}: {gpu.short_name}")
            gpu_frame.grid(row=i, column=0, columnspan=3, sticky="ew", padx=PAD/2, pady=PAD/2)
            gpu_frame.columnconfigure(1, weight=1)

            # GPU utilization
            ttk.Label(gpu_frame, text="GPU:").grid(row=0, column=0, sticky="w", padx=PAD/2, pady=PAD/4)
<<<<<<< HEAD
            gpu_prog = ttk.Progressbar(gpu_frame, mode="determinate", maximum=100, style=primary_style)
            gpu_prog.grid(row=0, column=1, sticky="ew", padx=PAD/2, pady=PAD/4)
            gpu_label = ttk.Label(gpu_frame, text="0%", width=8)
            gpu_label.grid(row=0, column=2, sticky="e", padx=PAD/2, pady=PAD/4)
            if TOOLTIP_AVAILABLE: ToolTip(gpu_prog, f"GPU {gpu.index} Utilization: {gpu.name}")

            # Memory utilization
            ttk.Label(gpu_frame, text="Memory:").grid(row=1, column=0, sticky="w", padx=PAD/2, pady=PAD/4)
            mem_prog = ttk.Progressbar(gpu_frame, mode="determinate", maximum=100, style=memory_style)
            mem_prog.grid(row=1, column=1, sticky="ew", padx=PAD/2, pady=PAD/4)
            mem_label = ttk.Label(gpu_frame, text="0%", width=8)
            mem_label.grid(row=1, column=2, sticky="e", padx=PAD/2, pady=PAD/4)
            if TOOLTIP_AVAILABLE: ToolTip(mem_prog, f"GPU {gpu.index} Memory: {gpu.mem_total} MiB total")
=======
            gpu_prog = ttk.Progressbar(gpu_frame, mode="determinate", maximum=100)
            gpu_prog.grid(row=0, column=1, sticky="ew", padx=PAD/2, pady=PAD/4)
            gpu_label = ttk.Label(gpu_frame, text="0%", width=8)
            gpu_label.grid(row=0, column=2, sticky="e", padx=PAD/2, pady=PAD/4)

            # Add tooltip to GPU utilization bar
            if TOOLTIP_AVAILABLE:
                ToolTip(gpu_prog, f"GPU {gpu.index} Utilization: {gpu.name}")

            # Memory utilization
            ttk.Label(gpu_frame, text="Memory:").grid(row=1, column=0, sticky="w", padx=PAD/2, pady=PAD/4)
            mem_prog = ttk.Progressbar(gpu_frame, mode="determinate", maximum=100)
            mem_prog.grid(row=1, column=1, sticky="ew", padx=PAD/2, pady=PAD/4)
            mem_label = ttk.Label(gpu_frame, text="0%", width=8)
            mem_label.grid(row=1, column=2, sticky="e", padx=PAD/2, pady=PAD/4)
>>>>>>> 199829b (Update documentation for DualGPUOptimizer to provide a high-level overview of GPU optimization and model inference systems. Organized content into key components: Core GPU Management, Model Optimization Engine, Command System, Monitoring Dashboard, and State Management. Enhanced glob patterns for improved file matching and clarified key implementation files, ensuring comprehensive coverage of system functionalities and integration points.)

            self.gpu_frames.append(gpu_frame)
            self.gpu_progress[f"gpu_{gpu.index}"] = gpu_prog
            self.gpu_labels[f"gpu_{gpu.index}"] = gpu_label
            self.gpu_progress[f"mem_{gpu.index}"] = mem_prog
            self.gpu_labels[f"mem_{gpu.index}"] = mem_label

        # --- Setup PCIe throughput labels ---
        for i, gpu in enumerate(gpus):
<<<<<<< HEAD
=======
            # RX throughput
>>>>>>> 199829b (Update documentation for DualGPUOptimizer to provide a high-level overview of GPU optimization and model inference systems. Organized content into key components: Core GPU Management, Model Optimization Engine, Command System, Monitoring Dashboard, and State Management. Enhanced glob patterns for improved file matching and clarified key implementation files, ensuring comprehensive coverage of system functionalities and integration points.)
            ttk.Label(pcie_frame, text=f"GPU {gpu.index} RX:").grid(row=i*2, column=0, sticky="w", padx=PAD/2, pady=PAD/4)
            rx_label = ttk.Label(pcie_frame, text="0 KB/s")
            rx_label.grid(row=i*2, column=1, sticky="w", padx=PAD/2, pady=PAD/4)

<<<<<<< HEAD
=======
            # TX throughput
>>>>>>> 199829b (Update documentation for DualGPUOptimizer to provide a high-level overview of GPU optimization and model inference systems. Organized content into key components: Core GPU Management, Model Optimization Engine, Command System, Monitoring Dashboard, and State Management. Enhanced glob patterns for improved file matching and clarified key implementation files, ensuring comprehensive coverage of system functionalities and integration points.)
            ttk.Label(pcie_frame, text=f"GPU {gpu.index} TX:").grid(row=i*2+1, column=0, sticky="w", padx=PAD/2, pady=PAD/4)
            tx_label = ttk.Label(pcie_frame, text="0 KB/s")
            tx_label.grid(row=i*2+1, column=1, sticky="w", padx=PAD/2, pady=PAD/4)

            if TOOLTIP_AVAILABLE:
                ToolTip(rx_label, f"GPU {gpu.index} PCIe RX bandwidth (receive)")
                ToolTip(tx_label, f"GPU {gpu.index} PCIe TX bandwidth (transmit)")

            self.pcie_labels[f"rx_{gpu.index}"] = rx_label
            self.pcie_labels[f"tx_{gpu.index}"] = tx_label

        # --- Setup temperature and power metrics ---
        temp_style = self.get_progress_style(self.gpu_colors.get("temp", ORANGE_ACCENT))
        power_style = self.get_progress_style(self.gpu_colors.get("power", CYAN_ACCENT))

        for i, gpu in enumerate(gpus):
            # Temperature
            ttk.Label(temp_power_frame, text=f"GPU {gpu.index} Temp:").grid(row=i*2, column=0, sticky="w", padx=PAD/2, pady=PAD/4)
<<<<<<< HEAD
            temp_prog = ttk.Progressbar(temp_power_frame, mode="determinate", maximum=100, style=temp_style)
            temp_prog.grid(row=i*2, column=1, sticky="ew", padx=PAD/2, pady=PAD/4)
            temp_label = ttk.Label(temp_power_frame, text="0°C")
            temp_label.grid(row=i*2, column=2, sticky="e", padx=PAD/2, pady=PAD/4)
            if TOOLTIP_AVAILABLE: ToolTip(temp_prog, f"GPU {gpu.index} Temperature (°C)")

            # Power usage
            ttk.Label(temp_power_frame, text=f"GPU {gpu.index} Power:").grid(row=i*2+1, column=0, sticky="w", padx=PAD/2, pady=PAD/4)
            # Max power limit can vary, use a sensible default like 400W or get from config/gpu_info if available
            max_power = gpu.power_limit or 400
            power_prog = ttk.Progressbar(temp_power_frame, mode="determinate", maximum=max_power, style=power_style)
            power_prog.grid(row=i*2+1, column=1, sticky="ew", padx=PAD/2, pady=PAD/4)
            power_label = ttk.Label(temp_power_frame, text="0W")
            power_label.grid(row=i*2+1, column=2, sticky="e", padx=PAD/2, pady=PAD/4)
            if TOOLTIP_AVAILABLE: ToolTip(power_prog, f"GPU {gpu.index} Power Consumption (Watts)")
=======
            temp_prog = ttk.Progressbar(temp_power_frame, mode="determinate", maximum=100)
            temp_prog.grid(row=i*2, column=1, sticky="ew", padx=PAD/2, pady=PAD/4)
            temp_label = ttk.Label(temp_power_frame, text="0°C")
            temp_label.grid(row=i*2, column=2, sticky="e", padx=PAD/2, pady=PAD/4)

            # Add tooltip to temperature bar
            if TOOLTIP_AVAILABLE:
                ToolTip(temp_prog, f"GPU {gpu.index} Temperature (°C)")

            # Power usage
            ttk.Label(temp_power_frame, text=f"GPU {gpu.index} Power:").grid(row=i*2+1, column=0, sticky="w", padx=PAD/2, pady=PAD/4)
            power_prog = ttk.Progressbar(temp_power_frame, mode="determinate", maximum=100)
            power_prog.grid(row=i*2+1, column=1, sticky="ew", padx=PAD/2, pady=PAD/4)
            power_label = ttk.Label(temp_power_frame, text="0W")
            power_label.grid(row=i*2+1, column=2, sticky="e", padx=PAD/2, pady=PAD/4)
>>>>>>> 199829b (Update documentation for DualGPUOptimizer to provide a high-level overview of GPU optimization and model inference systems. Organized content into key components: Core GPU Management, Model Optimization Engine, Command System, Monitoring Dashboard, and State Management. Enhanced glob patterns for improved file matching and clarified key implementation files, ensuring comprehensive coverage of system functionalities and integration points.)

            self.temp_progress[f"temp_{gpu.index}"] = temp_prog
            self.temp_labels[f"temp_{gpu.index}"] = temp_label
            self.power_progress[f"power_{gpu.index}"] = power_prog
            self.power_labels[f"power_{gpu.index}"] = power_label

        # --- Setup clock speeds ---
        # Using primary GPU color for clocks
        clock_style = self.get_progress_style(self.gpu_colors.get(0, PURPLE_PRIMARY))

        for i, gpu in enumerate(gpus):
            # Max clocks can vary greatly, use sensible defaults
            max_graphics_clock = 2500  # Default max graphics clock
            max_memory_clock = 12000   # Default max memory clock

            # Graphics clock
            ttk.Label(clock_frame, text=f"GPU {gpu.index} Graphics:").grid(row=i*2, column=0, sticky="w", padx=PAD/2, pady=PAD/4)
<<<<<<< HEAD
            graphics_prog = ttk.Progressbar(clock_frame, mode="determinate", maximum=max_graphics_clock, style=clock_style)
            graphics_prog.grid(row=i*2, column=1, sticky="ew", padx=PAD/2, pady=PAD/4)
            graphics_label = ttk.Label(clock_frame, text="0 MHz")
            graphics_label.grid(row=i*2, column=2, sticky="e", padx=PAD/2, pady=PAD/4)
            if TOOLTIP_AVAILABLE: ToolTip(graphics_prog, f"GPU {gpu.index} Graphics Clock Speed (MHz)")

            # Memory clock
            ttk.Label(clock_frame, text=f"GPU {gpu.index} Memory:").grid(row=i*2+1, column=0, sticky="w", padx=PAD/2, pady=PAD/4)
            memory_prog = ttk.Progressbar(clock_frame, mode="determinate", maximum=max_memory_clock, style=clock_style)
            memory_prog.grid(row=i*2+1, column=1, sticky="ew", padx=PAD/2, pady=PAD/4)
            memory_label = ttk.Label(clock_frame, text="0 MHz")
            memory_label.grid(row=i*2+1, column=2, sticky="e", padx=PAD/2, pady=PAD/4)
            if TOOLTIP_AVAILABLE: ToolTip(memory_prog, f"GPU {gpu.index} Memory Clock Speed (MHz)")
=======
            graphics_prog = ttk.Progressbar(clock_frame, mode="determinate", maximum=2500)  # Max reasonable clock
            graphics_prog.grid(row=i*2, column=1, sticky="ew", padx=PAD/2, pady=PAD/4)
            graphics_label = ttk.Label(clock_frame, text="0 MHz")
            graphics_label.grid(row=i*2, column=2, sticky="e", padx=PAD/2, pady=PAD/4)

            # Add tooltip
            if TOOLTIP_AVAILABLE:
                ToolTip(graphics_prog, f"GPU {gpu.index} Graphics Clock Speed (MHz)")

            # Memory clock
            ttk.Label(clock_frame, text=f"GPU {gpu.index} Memory:").grid(row=i*2+1, column=0, sticky="w", padx=PAD/2, pady=PAD/4)
            memory_prog = ttk.Progressbar(clock_frame, mode="determinate", maximum=12000)  # Max reasonable memory clock
            memory_prog.grid(row=i*2+1, column=1, sticky="ew", padx=PAD/2, pady=PAD/4)
            memory_label = ttk.Label(clock_frame, text="0 MHz")
            memory_label.grid(row=i*2+1, column=2, sticky="e", padx=PAD/2, pady=PAD/4)
>>>>>>> 199829b (Update documentation for DualGPUOptimizer to provide a high-level overview of GPU optimization and model inference systems. Organized content into key components: Core GPU Management, Model Optimization Engine, Command System, Monitoring Dashboard, and State Management. Enhanced glob patterns for improved file matching and clarified key implementation files, ensuring comprehensive coverage of system functionalities and integration points.)

            self.graphics_clock_progress[f"graphics_{gpu.index}"] = graphics_prog
            self.graphics_clock_labels[f"graphics_{gpu.index}"] = graphics_label
            self.memory_clock_progress[f"memory_{gpu.index}"] = memory_prog
            self.memory_clock_labels[f"memory_{gpu.index}"] = memory_label

    def get_progress_style(self, color_hex: str) -> str:
        """Maps a hex color to the corresponding themed progress bar style name."""
        # Map known theme colors to their style names
        if color_hex == PURPLE_PRIMARY: return "GPU.Horizontal.TProgressbar"
        if color_hex == PURPLE_HIGHLIGHT: return "GPUPurpleHighlight.Horizontal.TProgressbar"
        if color_hex == PINK_ACCENT: return "GPUPink.Horizontal.TProgressbar"
        if color_hex == CYAN_ACCENT: return "GPUCyan.Horizontal.TProgressbar"
        if color_hex == ORANGE_ACCENT: return "GPUOrange.Horizontal.TProgressbar"
        # Fallback to the default style if color doesn't match known accents
        return "GPU.Horizontal.TProgressbar"

    def update_telemetry(self, telemetry_data: Dict[str, Any]) -> None:
        """
        Update the dashboard with the latest telemetry data.

        Args:
            telemetry_data: Dictionary containing lists of GPU metrics.
        """
        # Add raw data to history for chart (ensure it's a list of load values)
        gpu_load_history = telemetry_data.get("load", [])
        if gpu_load_history:
            self.tele_hist.append(gpu_load_history)

        # Limit history
        max_hist = 60 # Corresponds to CHART_HISTORY_LENGTH from constants, maybe use that?
        if len(self.tele_hist) > max_hist:
            self.tele_hist = self.tele_hist[-max_hist:]

        # --- Update Utilization Metrics ---
        for i, load in enumerate(telemetry_data.get("load", [])):
            if f"gpu_{i}" in self.gpu_progress:
                self.gpu_progress[f"gpu_{i}"]["value"] = load
                self.gpu_labels[f"gpu_{i}"]["text"] = f"{load}%"

        # --- Update Memory Utilization ---
        for i, mem_util in enumerate(telemetry_data.get("memory_util", [])):
            if f"mem_{i}" in self.gpu_progress:
                self.gpu_progress[f"mem_{i}"]["value"] = mem_util
                self.gpu_labels[f"mem_{i}"]["text"] = f"{mem_util}%"

        # --- Update PCIe Throughput ---
        pcie_rx = telemetry_data.get("pcie_rx", [])
        pcie_tx = telemetry_data.get("pcie_tx", [])
        num_gpus = len(self.gpus)
        for i in range(num_gpus):
            rx = pcie_rx[i] if i < len(pcie_rx) else 0
            tx = pcie_tx[i] if i < len(pcie_tx) else 0
            rx_text = self._format_bandwidth(rx)
            tx_text = self._format_bandwidth(tx)

            if f"rx_{i}" in self.pcie_labels: self.pcie_labels[f"rx_{i}"]["text"] = rx_text
            if f"tx_{i}" in self.pcie_labels: self.pcie_labels[f"tx_{i}"]["text"] = tx_text

        # --- Update Temperature ---
        for i, temp in enumerate(telemetry_data.get("temperature", [])):
            if f"temp_{i}" in self.temp_progress:
                self.temp_progress[f"temp_{i}"]["value"] = min(temp, 100) # Cap at 100 for display
                self.temp_labels[f"temp_{i}"]["text"] = f"{temp}°C"

        # --- Update Power Usage ---
        for i, power in enumerate(telemetry_data.get("power_usage", [])):
            if f"power_{i}" in self.power_progress:
                max_power = self.power_progress[f"power_{i}"]["maximum"]
                self.power_progress[f"power_{i}"]["value"] = min(power, max_power)
                self.power_labels[f"power_{i}"]["text"] = f"{power:.1f}W"

        # --- Update Clock Speeds ---
        for i, clock in enumerate(telemetry_data.get("graphics_clock", [])):
            if f"graphics_{i}" in self.graphics_clock_progress:
                max_clock = self.graphics_clock_progress[f"graphics_{i}"]["maximum"]
                self.graphics_clock_progress[f"graphics_{i}"]["value"] = min(clock, max_clock)
                self.graphics_clock_labels[f"graphics_{i}"]["text"] = f"{clock} MHz"

        for i, clock in enumerate(telemetry_data.get("memory_clock", [])):
            if f"memory_{i}" in self.memory_clock_progress:
                max_clock = self.memory_clock_progress[f"memory_{i}"]["maximum"]
                self.memory_clock_progress[f"memory_{i}"]["value"] = min(clock, max_clock)
                self.memory_clock_labels[f"memory_{i}"]["text"] = f"{clock} MHz"

        # --- Update Last Update Time ---
        self.last_update_label["text"] = f"Last update: {time.strftime('%H:%M:%S')}"

        # --- Render History Graph ---
        self.render_history_graph()

    def render_history_graph(self) -> None:
        """Render the GPU usage history graph on the canvas."""
        if not self.tele_hist or not hasattr(self, 'chart_canvas') or not self.chart_canvas.winfo_exists():
            return

        canvas = self.chart_canvas
        # Ensure dimensions are positive before proceeding
        canvas.update_idletasks() # Ensure dimensions are up-to-date
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
             return # Skip rendering if canvas is not visible or too small

        canvas.delete("all")

        # Draw grid lines (using themed color)
        grid_color = GRID_LINE_COLOR
        text_color = LIGHT_FOREGROUND
        for y_percent in range(0, 101, 10):
            y_pos = height - (y_percent / 100 * height)
            canvas.create_line(0, y_pos, width, y_pos, fill=grid_color, dash=(2, 2))
            if y_percent % 20 == 0:
                canvas.create_text(5, y_pos, text=f"{y_percent}%", anchor="w", fill=text_color, font=("Helvetica", 7))

        # Draw vertical grid lines
        samples = len(self.tele_hist)
        if samples > 1:
            interval = max(1, samples // 6) # Aim for ~6 vertical lines
            for i in range(interval, samples, interval):
                x = (i / (samples - 1)) * width if samples > 1 else 0
                canvas.create_line(x, 0, x, height, fill=grid_color, dash=(2, 2))

        # Prepare points for each GPU line
        if not self.tele_hist: return
        num_gpus_in_history = len(self.tele_hist[0])
        points_list = [[] for _ in range(num_gpus_in_history)]

        for i, loads_at_time_i in enumerate(self.tele_hist):
            x = (i / (samples - 1)) * width if samples > 1 else 0
            for gpu_idx, load in enumerate(loads_at_time_i):
                if gpu_idx < num_gpus_in_history:
                    y = height - (load / 100 * height)
                    points_list[gpu_idx].append((x, y))

        # Draw lines and labels for each GPU
        for gpu_idx, points in enumerate(points_list):
            if len(points) > 1:
                # Get color using the GPU index from the constants dictionary
                color = self.gpu_colors.get(gpu_idx, PURPLE_PRIMARY) # Fallback to primary purple

                # Use create_line for potentially smoother rendering with multiple points
                canvas.create_line(
                    points,
                    fill=color,
                    width=2,
                    # smooth=True # Smoothing can sometimes look weird, optional
                )

<<<<<<< HEAD
                # Add label at the end of the line
                last_x, last_y = points[-1]
                # Adjust label position slightly for clarity
                label_x = min(width - 30, last_x + 5)
                label_y = max(10, min(height - 10, last_y))
                canvas.create_text(
                    label_x, label_y,
                    text=f"GPU {gpu_idx}",
                    fill=color,
                    anchor="w",
                    font=("Helvetica", 8, "bold")
                )
=======
                # Draw line segment
                canvas.create_line(
                    smooth_points,
                    fill=color,
                    width=2,
                    smooth=True
                )

                # Add a label for this GPU
                if points:
                    # Put the label at the right edge of the plot
                    last_point = points[-1]
                    canvas.create_text(
                        last_point[0] + 15, last_point[1],
                        text=f"GPU {gpu_idx}",
                        fill=color,
                        anchor="w"
                    )
>>>>>>> 199829b (Update documentation for DualGPUOptimizer to provide a high-level overview of GPU optimization and model inference systems. Organized content into key components: Core GPU Management, Model Optimization Engine, Command System, Monitoring Dashboard, and State Management. Enhanced glob patterns for improved file matching and clarified key implementation files, ensuring comprehensive coverage of system functionalities and integration points.)

    @staticmethod
    def _format_bandwidth(kb_per_sec: int) -> str:
        """Format bandwidth (KB/s) into a human-readable string (MB/s, GB/s)."""
        if kb_per_sec < 1024:
            return f"{kb_per_sec} KB/s"
        elif kb_per_sec < 1024 * 1024:
            return f"{kb_per_sec / 1024:.1f} MB/s"
        else:
            return f"{kb_per_sec / (1024 * 1024):.1f} GB/s"