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

from dualgpuopt.gui.app import PAD
from dualgpuopt.gpu_info import GPU
from dualgpuopt.telemetry import Telemetry


class GpuDashboard(ttk.Frame):
    """GPU Dashboard tab that shows real-time GPU metrics."""
    
    def __init__(self, parent: ttk.Frame, gpu_colors: List[str]) -> None:
        """
        Initialize the dashboard tab.
        
        Args:
            parent: Parent frame
            gpu_colors: List of colors for GPU visualization
        """
        super().__init__(parent, padding=PAD)
        self.parent = parent
        self.gpu_colors = gpu_colors
        self.columnconfigure(0, weight=1)
        
        # Canvas for GPU usage history
        history_frame = ttk.LabelFrame(self, text="GPU Usage History")
        history_frame.grid(row=0, column=0, sticky="news", padx=PAD, pady=(0, PAD))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        
        self.chart_canvas = tk.Canvas(history_frame, height=150, bg="#1a2327")
        self.chart_canvas.grid(row=0, column=0, sticky="news", padx=PAD/2, pady=PAD/2)
        
        # GPU metrics grid
        metrics_frame = ttk.LabelFrame(self, text="Real-time GPU Metrics")
        metrics_frame.grid(row=1, column=0, sticky="news", padx=PAD, pady=(0, PAD))
        metrics_frame.columnconfigure(0, weight=0)  # Label column
        metrics_frame.columnconfigure(1, weight=1)  # Progress bar column
        metrics_frame.columnconfigure(2, weight=0)  # Value column
        
        # Create metric rows for each GPU
        self.gpu_frames = []
        self.gpu_progress = {}
        self.gpu_labels = {}
        
        # Create PCIe throughput frame
        pcie_frame = ttk.LabelFrame(self, text="PCIe Bandwidth")
        pcie_frame.grid(row=2, column=0, sticky="news", padx=PAD, pady=(0, PAD))
        pcie_frame.columnconfigure(0, weight=0)  # Label column
        pcie_frame.columnconfigure(1, weight=1)  # Value column
        
        self.pcie_labels = {}
        
        # Create temperature and power frame
        temp_power_frame = ttk.LabelFrame(self, text="Temperature & Power")
        temp_power_frame.grid(row=3, column=0, sticky="news", padx=PAD, pady=(0, PAD))
        temp_power_frame.columnconfigure(0, weight=0)  # Label column
        temp_power_frame.columnconfigure(1, weight=1)  # Progress bar column
        temp_power_frame.columnconfigure(2, weight=0)  # Value column
        
        self.temp_progress = {}
        self.temp_labels = {}
        self.power_progress = {}
        self.power_labels = {}
        
        # Create clock speeds frame
        clock_frame = ttk.LabelFrame(self, text="Clock Speeds")
        clock_frame.grid(row=4, column=0, sticky="news", padx=PAD, pady=(0, PAD))
        clock_frame.columnconfigure(0, weight=0)  # Label column
        clock_frame.columnconfigure(1, weight=1)  # Progress bar column
        clock_frame.columnconfigure(2, weight=0)  # Value column
        
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
        
        # Initialize with empty data
        self.tele_hist = []
        
    def initialize_gpu_metrics(self, gpus: List[GPU]) -> None:
        """
        Initialize the GPU metrics UI with the list of GPUs.
        
        Args:
            gpus: List of GPU objects
        """
        # Setup metrics frame for each GPU
        metrics_frame = self.winfo_children()[1]  # Get the metrics frame
        
        for i, gpu in enumerate(gpus):
            # Create a container frame for this GPU
            gpu_frame = ttk.LabelFrame(metrics_frame, text=f"GPU {gpu.index}: {gpu.short_name}")
            gpu_frame.grid(row=i, column=0, columnspan=3, sticky="ew", padx=PAD/2, pady=PAD/2)
            gpu_frame.columnconfigure(1, weight=1)
            
            # GPU utilization
            ttk.Label(gpu_frame, text="GPU:").grid(row=0, column=0, sticky="w", padx=PAD/2, pady=PAD/4)
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
            
            # Add tooltip to memory utilization bar
            if TOOLTIP_AVAILABLE:
                ToolTip(mem_prog, f"GPU {gpu.index} Memory: {gpu.mem_total} MiB total")
            
            # Store references
            self.gpu_frames.append(gpu_frame)
            self.gpu_progress[f"gpu_{gpu.index}"] = gpu_prog
            self.gpu_labels[f"gpu_{gpu.index}"] = gpu_label
            self.gpu_progress[f"mem_{gpu.index}"] = mem_prog
            self.gpu_labels[f"mem_{gpu.index}"] = mem_label
        
        # Setup PCIe throughput labels
        pcie_frame = self.winfo_children()[2]  # Get the PCIe frame
        
        for i, gpu in enumerate(gpus):
            # RX throughput
            ttk.Label(pcie_frame, text=f"GPU {gpu.index} RX:").grid(row=i*2, column=0, sticky="w", padx=PAD/2, pady=PAD/4)
            rx_label = ttk.Label(pcie_frame, text="0 KB/s")
            rx_label.grid(row=i*2, column=1, sticky="w", padx=PAD/2, pady=PAD/4)
            
            # TX throughput
            ttk.Label(pcie_frame, text=f"GPU {gpu.index} TX:").grid(row=i*2+1, column=0, sticky="w", padx=PAD/2, pady=PAD/4)
            tx_label = ttk.Label(pcie_frame, text="0 KB/s")
            tx_label.grid(row=i*2+1, column=1, sticky="w", padx=PAD/2, pady=PAD/4)
            
            # Add tooltips
            if TOOLTIP_AVAILABLE:
                ToolTip(rx_label, f"GPU {gpu.index} PCIe RX bandwidth (receive)")
                ToolTip(tx_label, f"GPU {gpu.index} PCIe TX bandwidth (transmit)")
            
            # Store references
            self.pcie_labels[f"rx_{gpu.index}"] = rx_label
            self.pcie_labels[f"tx_{gpu.index}"] = tx_label
        
        # Setup temperature and power metrics
        temp_power_frame = self.winfo_children()[3]  # Get the temperature/power frame
        
        for i, gpu in enumerate(gpus):
            # Temperature
            ttk.Label(temp_power_frame, text=f"GPU {gpu.index} Temp:").grid(row=i*2, column=0, sticky="w", padx=PAD/2, pady=PAD/4)
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
            
            # Add tooltip to power bar
            if TOOLTIP_AVAILABLE:
                ToolTip(power_prog, f"GPU {gpu.index} Power Consumption (Watts)")
            
            # Store references
            self.temp_progress[f"temp_{gpu.index}"] = temp_prog
            self.temp_labels[f"temp_{gpu.index}"] = temp_label
            self.power_progress[f"power_{gpu.index}"] = power_prog
            self.power_labels[f"power_{gpu.index}"] = power_label
        
        # Setup clock speeds
        clock_frame = self.winfo_children()[4]  # Get the clock speeds frame
        
        for i, gpu in enumerate(gpus):
            # Graphics clock
            ttk.Label(clock_frame, text=f"GPU {gpu.index} Graphics:").grid(row=i*2, column=0, sticky="w", padx=PAD/2, pady=PAD/4)
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
            
            # Add tooltip
            if TOOLTIP_AVAILABLE:
                ToolTip(memory_prog, f"GPU {gpu.index} Memory Clock Speed (MHz)")
            
            # Store references
            self.graphics_clock_progress[f"graphics_{gpu.index}"] = graphics_prog
            self.graphics_clock_labels[f"graphics_{gpu.index}"] = graphics_label
            self.memory_clock_progress[f"memory_{gpu.index}"] = memory_prog
            self.memory_clock_labels[f"memory_{gpu.index}"] = memory_label
    
    def update(self, telemetry: Telemetry) -> None:
        """
        Update the dashboard with the latest telemetry data.
        
        Args:
            telemetry: Telemetry data with GPU metrics
        """
        # Add to history for chart
        self.tele_hist.append(telemetry)
        
        # Limit history to last 60 samples
        if len(self.tele_hist) > 60:
            self.tele_hist = self.tele_hist[-60:]
        
        # Update GPU utilization metrics
        for i, load in enumerate(telemetry.load):
            if f"gpu_{i}" in self.gpu_progress:
                self.gpu_progress[f"gpu_{i}"]["value"] = load
                self.gpu_labels[f"gpu_{i}"]["text"] = f"{load}%"
        
        # Update memory utilization
        for i, mem_util in enumerate(telemetry.memory_util):
            if f"mem_{i}" in self.gpu_progress:
                self.gpu_progress[f"mem_{i}"]["value"] = mem_util
                self.gpu_labels[f"mem_{i}"]["text"] = f"{mem_util}%"
        
        # Update PCIe throughput
        for i, (rx, tx) in enumerate(zip(telemetry.pcie_rx, telemetry.pcie_tx)):
            # Convert KB/s to more readable units
            rx_text = self._format_bandwidth(rx)
            tx_text = self._format_bandwidth(tx)
            
            if f"rx_{i}" in self.pcie_labels:
                self.pcie_labels[f"rx_{i}"]["text"] = rx_text
            if f"tx_{i}" in self.pcie_labels:
                self.pcie_labels[f"tx_{i}"]["text"] = tx_text
        
        # Update temperature
        for i, temp in enumerate(telemetry.temperature):
            if f"temp_{i}" in self.temp_progress:
                # Scale temperature: 0-100°C maps to 0-100%
                self.temp_progress[f"temp_{i}"]["value"] = min(temp, 100)
                self.temp_labels[f"temp_{i}"]["text"] = f"{temp}°C"
        
        # Update power usage
        for i, (power, _) in enumerate(zip(telemetry.power_usage, self.gpu_progress)):
            if f"power_{i}" in self.power_progress:
                # Assume max reasonable power is 400W for progress bar
                self.power_progress[f"power_{i}"]["value"] = min(power / 4, 100)
                self.power_labels[f"power_{i}"]["text"] = f"{power:.1f}W"
        
        # Update clock speeds
        for i, clock in enumerate(telemetry.graphics_clock):
            if f"graphics_{i}" in self.graphics_clock_progress:
                self.graphics_clock_progress[f"graphics_{i}"]["value"] = clock
                self.graphics_clock_labels[f"graphics_{i}"]["text"] = f"{clock} MHz"
        
        for i, clock in enumerate(telemetry.memory_clock):
            if f"memory_{i}" in self.memory_clock_progress:
                self.memory_clock_progress[f"memory_{i}"]["value"] = clock
                self.memory_clock_labels[f"memory_{i}"]["text"] = f"{clock} MHz"
        
        # Update last update time
        self.last_update_label["text"] = f"Last update: {time.strftime('%H:%M:%S')}"
        
        # Render the history graph
        self.render_history_graph()
    
    def render_history_graph(self) -> None:
        """Render the GPU usage history graph."""
        if not self.tele_hist:
            return
        
        canvas = self.chart_canvas
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        # Clear the canvas
        canvas.delete("all")
        
        # Draw grid lines (dashed)
        for y in range(0, 101, 10):  # 0%, 10%, 20%, ..., 100%
            y_pos = height - (y / 100 * height)
            canvas.create_line(0, y_pos, width, y_pos, fill="#555555", dash=(2, 2))
            if y % 20 == 0:  # Only label at 0%, 20%, 40%, 60%, 80%, 100%
                canvas.create_text(5, y_pos, text=f"{y}%", anchor="w", fill="#aaaaaa", font=("Helvetica", 7))
        
        # Draw vertical grid lines (time intervals)
        samples = len(self.tele_hist)
        if samples > 1:
            interval = max(1, samples // 6)  # Show ~6 vertical lines
            for i in range(0, samples, interval):
                x = (i / samples) * width
                canvas.create_line(x, 0, x, height, fill="#555555", dash=(2, 2))
        
        # Generate points for each GPU's utilization
        gpu_count = len(self.tele_hist[0].load)
        points_list = [[] for _ in range(gpu_count)]
        
        # Plot load for each GPU
        for i, telemetry in enumerate(self.tele_hist):
            x = (i / len(self.tele_hist)) * width
            
            for gpu_idx, load in enumerate(telemetry.load):
                if gpu_idx < gpu_count:
                    y = height - (load / 100 * height)
                    points_list[gpu_idx].append((x, y))
        
        # Draw lines for each GPU with faded trailing points
        for gpu_idx, points in enumerate(points_list):
            if len(points) > 1:
                if gpu_idx < len(self.gpu_colors):
                    color = self.gpu_colors[gpu_idx]
                else:
                    color = "#ffffff"  # Default to white if we run out of colors
                
                # Create points for a smoother line
                smooth_points = []
                for i, (x, y) in enumerate(points):
                    # Add actual data point
                    smooth_points.append((x, y))
                    
                    # Add intermediate point for smoother curves (except at the ends)
                    if 0 < i < len(points) - 1:
                        next_x, next_y = points[i + 1]
                        smooth_points.append((x + (next_x - x) / 2, y + (next_y - y) / 2))
                
                # Draw segments with gradually fading effect for trailing points
                for i in range(len(smooth_points) - 1):
                    # Calculate opacity based on position (more recent = more opaque)
                    opacity = int(((i + 1) / len(smooth_points)) * 255)
                    segment_color = f"{color[0:7]}${opacity:02x}" if opacity < 255 else color
                    
                    # Draw line segment
                    canvas.create_line(
                        smooth_points[i], smooth_points[i + 1],
                        fill=color,  # Use full opacity for now
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
    
    @staticmethod
    def _format_bandwidth(kb_per_sec: int) -> str:
        """
        Format bandwidth in human-readable form.
        
        Args:
            kb_per_sec: Bandwidth in KB/s
            
        Returns:
            Formatted bandwidth string
        """
        if kb_per_sec < 1024:
            return f"{kb_per_sec} KB/s"
        elif kb_per_sec < 1024 * 1024:
            return f"{kb_per_sec / 1024:.1f} MB/s"
        else:
            return f"{kb_per_sec / (1024 * 1024):.1f} GB/s" 