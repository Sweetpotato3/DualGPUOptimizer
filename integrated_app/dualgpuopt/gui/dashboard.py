#!/usr/bin/env python3
"""
GPU metrics dashboard component.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
import time
import threading
import logging
from typing import Dict, List, Optional, Tuple, Any

from dualgpuopt.gui_constants import (
    PAD, DARK_BACKGROUND, LIGHT_FOREGROUND, PURPLE_PRIMARY,
    ORANGE_ACCENT, GPU_COLORS, DEFAULT_FONT, DEFAULT_FONT_SIZE
)
from dualgpuopt.gpu_info import GPU, probe_gpus
from dualgpuopt.services.event_bus import event_bus, GPUMetricsEvent, EventPriority


class GPUDashboard(ttk.Frame):
    """GPU metrics dashboard displaying real-time GPU information."""

    def __init__(self, master: Any, **kwargs: Any) -> None:
        """Initialize the dashboard."""
        super().__init__(master, **kwargs)

        # Configure style
        self.bg_color = DARK_BACKGROUND
        self.fg_color = LIGHT_FOREGROUND
        self.configure(style="Dashboard.TFrame")

        # Create style if it doesn't exist
        style = ttk.Style()
        style.configure(
            "Dashboard.TFrame",
            background=self.bg_color,
        )
        style.configure(
            "GPU.TFrame",
            background=self.bg_color,
        )
        style.configure(
            "Dashboard.TLabel",
            background=self.bg_color,
            foreground=self.fg_color,
            font=(DEFAULT_FONT, DEFAULT_FONT_SIZE)
        )
        style.configure(
            "DashboardTitle.TLabel",
            background=self.bg_color,
            foreground=PURPLE_PRIMARY,
            font=(DEFAULT_FONT, DEFAULT_FONT_SIZE + 4, "bold")
        )

        # Initialize variables
        self.gpu_frames: Dict[int, ttk.Frame] = {}
        self.gpu_data: Dict[int, Dict[str, tk.StringVar]] = {}
        self.update_interval_ms = 1000  # 1 second refresh
        self.logger = logging.getLogger("dualgpuopt.gui.dashboard")

        # Build UI
        self._build_ui()

        # Start update thread
        self._setup_event_handlers()

    def _build_ui(self) -> None:
        """Build the dashboard UI."""
        # Create title
        title = ttk.Label(
            self,
            text="GPU Dashboard",
            style="DashboardTitle.TLabel"
        )
        title.pack(pady=(PAD, PAD*2), padx=PAD, anchor=tk.W)

        # GPU container
        self.gpu_container = ttk.Frame(self, style="Dashboard.TFrame")
        self.gpu_container.pack(fill=tk.BOTH, expand=True, padx=PAD, pady=PAD)

        # Initial GPU discovery
        self._discover_gpus()

    def _discover_gpus(self) -> None:
        """Discover available GPUs and create their UI elements."""
        try:
            gpus = probe_gpus()

            # Clear existing frames
            for frame in self.gpu_frames.values():
                frame.destroy()
            self.gpu_frames.clear()
            self.gpu_data.clear()

            # Create frames for each GPU
            for i, gpu in enumerate(gpus):
                self._create_gpu_frame(gpu)

            if not gpus:
                self._show_no_gpu_message()

        except Exception as e:
            self.logger.error(f"Error discovering GPUs: {e}")
            self._show_no_gpu_message()

    def _show_no_gpu_message(self) -> None:
        """Show a message when no GPUs are found."""
        msg_frame = ttk.Frame(self.gpu_container, style="GPU.TFrame")
        msg_frame.pack(fill=tk.X, pady=PAD)

        ttk.Label(
            msg_frame,
            text="No GPUs detected. Either no NVIDIA GPUs are present or the drivers are not loaded.",
            style="Dashboard.TLabel",
            foreground=ORANGE_ACCENT
        ).pack(pady=PAD*2)

        ttk.Label(
            msg_frame,
            text="You can use the 'mock' mode to see simulated GPU data for testing.",
            style="Dashboard.TLabel"
        ).pack(pady=PAD)

    def _create_gpu_frame(self, gpu: GPU) -> None:
        """Create a frame for displaying a GPU's metrics."""
        # Frame for this GPU
        frame = ttk.Frame(self.gpu_container, style="GPU.TFrame")
        frame.pack(fill=tk.X, pady=PAD/2)
        self.gpu_frames[gpu.index] = frame

        # Color indicator
        color = GPU_COLORS.get(gpu.index, PURPLE_PRIMARY)
        indicator = tk.Canvas(frame, width=10, height=80, bg=color, highlightthickness=0)
        indicator.pack(side=tk.LEFT, padx=(0, PAD))

        # Info frame
        info_frame = ttk.Frame(frame, style="GPU.TFrame")
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=PAD/2)

        # GPU name and basic info
        header_frame = ttk.Frame(info_frame, style="GPU.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, PAD/2))

        ttk.Label(
            header_frame,
            text=f"GPU {gpu.index}: {gpu.name}",
            style="Dashboard.TLabel",
            font=(DEFAULT_FONT, DEFAULT_FONT_SIZE + 2, "bold")
        ).pack(side=tk.LEFT)

        # Memory info
        mem_text = f"{gpu.mem_used_gb} GB / {gpu.mem_total_gb} GB ({int(gpu.mem_used_percent)}%)"
        ttk.Label(
            header_frame,
            text=f"Memory: {mem_text}",
            style="Dashboard.TLabel"
        ).pack(side=tk.RIGHT)

        # Create metrics grid
        metrics_frame = ttk.Frame(info_frame, style="GPU.TFrame")
        metrics_frame.pack(fill=tk.X, pady=PAD/2)

        # Initialize data for each metric
        self.gpu_data[gpu.index] = {
            "util": tk.StringVar(value=f"{gpu.gpu_utilization}%"),
            "temp": tk.StringVar(value=f"{gpu.temperature}°C"),
            "power": tk.StringVar(value=f"{gpu.power_usage:.1f}W / {gpu.power_limit:.1f}W"),
            "fan": tk.StringVar(value=f"{gpu.fan_speed}%"),
            "clocks": tk.StringVar(value=f"GPU: {gpu.graphics_clock} MHz, Mem: {gpu.memory_clock} MHz")
        }

        # Create metric labels
        metrics = [
            ("Utilization:", "util"),
            ("Temperature:", "temp"),
            ("Power:", "power"),
            ("Fan Speed:", "fan"),
            ("Clocks:", "clocks")
        ]

        for i, (label_text, data_key) in enumerate(metrics):
            row = i // 3
            col = i % 3

            # Label
            ttk.Label(
                metrics_frame,
                text=label_text,
                style="Dashboard.TLabel",
                width=12,
                anchor=tk.W
            ).grid(row=row, column=col*2, sticky=tk.W, padx=(PAD, 0))

            # Value
            ttk.Label(
                metrics_frame,
                textvariable=self.gpu_data[gpu.index][data_key],
                style="Dashboard.TLabel"
            ).grid(row=row, column=col*2+1, sticky=tk.W, padx=(0, PAD*2))

    def _setup_event_handlers(self) -> None:
        """Set up event handlers for GPU metrics updates."""
        event_bus.subscribe_typed(
            GPUMetricsEvent,
            self._on_gpu_metrics_update,
            priority=EventPriority.NORMAL
        )

    def _on_gpu_metrics_update(self, event: GPUMetricsEvent) -> None:
        """Handle GPU metrics update events."""
        # Skip if we don't have this GPU in our display
        if event.gpu_index not in self.gpu_data:
            return

        # Update the UI with the new metrics
        try:
            data = self.gpu_data[event.gpu_index]

            # Update metrics
            data["util"].set(f"{event.utilization:.0f}%")
            data["temp"].set(f"{event.temperature:.0f}°C")
            data["power"].set(f"{event.power_draw:.1f}W")
            data["fan"].set(f"{event.fan_speed}%")

        except Exception as e:
            self.logger.error(f"Error updating GPU metrics: {e}")

    def refresh(self) -> None:
        """Force refresh of all GPU data."""
        self._discover_gpus()