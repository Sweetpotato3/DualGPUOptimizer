"""
Tkinter front‑end.  No business logic – pulls helpers from gpu_info / optimizer.
"""
from __future__ import annotations

import json
import pathlib
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import colorsys
import sys
import logging

from dualgpuopt import gpu_info, optimizer, configio
from dualgpuopt.telemetry import start_stream
from dualgpuopt.runner import Runner
from dualgpuopt.tray import init_tray


# Pre-defined colors for up to 8 GPUs
GPU_COLORS = [
    "#33ff55",  # Green
    "#00b0ff",  # Blue
    "#ff5500",  # Orange
    "#aa00ff",  # Purple
    "#ffcc00",  # Yellow
    "#ff0066",  # Pink
    "#00ffcc",  # Cyan
    "#ffffff",  # White
]

# Theme definitions
THEMES = {
    "dark": {
        "bg": "#2d2d2d",
        "text": "#ffffff",
        "chart_bg": "#202020",
        "highlight": "#0078d7",
        "button": "#3d3d3d",
        "entry": "#3d3d3d",
        "ttk_theme": "clam"
    },
    "light": {
        "bg": "#f0f0f0",
        "text": "#000000",
        "chart_bg": "#e0e0e0",
        "highlight": "#007acc",
        "button": "#e0e0e0",
        "entry": "#ffffff",
        "ttk_theme": "clam"
    },
    "system": {
        # Will use system default theme
        "ttk_theme": None  # Use default
    }
}


def generate_colors(count: int) -> list[str]:
    """Generate distinct colors for GPU visualization."""
    if count <= len(GPU_COLORS):
        return GPU_COLORS[:count]
    
    # Generate additional colors if needed using HSV color space
    colors = []
    for i in range(count):
        hue = i / count
        r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
        hex_color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        colors.append(hex_color)
    return colors


class DualGpuApp(ttk.Frame):
    PAD = 8

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)
        self.master = master
        self.logger = logging.getLogger("dualgpuopt.gui")
        
        try:
            # Load config before initializing UI
            self.cfg = configio.load_cfg()
            
            # Apply theme to root window before creating widgets
            self._apply_theme(master)
            
            self.model_var = tk.StringVar(value="dolphin‑2.5‑mixtral‑8x7b.Q3_K_M.gguf")
            self.ctx_var = tk.IntVar(value=65536)
            self.theme_var = tk.StringVar(value=self.cfg["theme"])
            self.runner = None
            self.tele_hist = []  # List of GPU load tuples

            # Load presets
            preset_path = pathlib.Path(__file__).parent / "presets" / "mixtral.json"
            self.presets = json.load(preset_path.open())
            
            if self.cfg["last_model"]:
                self.model_var.set(self.cfg["last_model"])

            self.gpus = gpu_info.probe_gpus()
            if len(self.gpus) < 2:
                self.show_error("Need ≥ 2 GPUs – aborting")
                master.destroy()
                return
            
            # Generate colors for GPU visualization
            self.gpu_colors = generate_colors(len(self.gpus))

            self.init_ui()
            self._refresh_outputs()
            
            # Setup telemetry
            self.tele_q = start_stream(1.0)
            self.after(1000, self._tick_chart)
            
            # Setup tray
            init_tray(self)
        except Exception as err:
            self.show_error(f"Error initializing application: {err}")
    
    def show_error(self, message, title="Error"):
        """Show an error dialog and log the error."""
        self.logger.error(message)
        messagebox.showerror(title, message)
        
        # Add a simple interface with mock mode option if this is a GPU detection error
        if "GPU detection failed" in message or "NVML" in message:
            frame = ttk.Frame(self)
            frame.pack(padx=20, pady=20, fill="both", expand=True)
            
            ttk.Label(frame, text="GPU detection failed. Would you like to:").pack(pady=10)
            
            # Mock mode button
            mock_btn = ttk.Button(frame, text="Launch in Mock Mode", 
                               command=self.enable_mock_mode)
            mock_btn.pack(pady=10)
            
            # Exit button
            exit_btn = ttk.Button(frame, text="Exit", 
                               command=self.master.destroy)
            exit_btn.pack(pady=10)
            
    def enable_mock_mode(self):
        """Enable mock mode and restart the application."""
        import os
        import sys
        
        # Set environment variable for mock mode
        os.environ["DGPUOPT_MOCK_GPUS"] = "1"
        
        # Clear the current UI
        for widget in self.winfo_children():
            widget.destroy()
            
        # Try to initialize with mock GPUs
        try:
            self.gpus = gpu_info.probe_gpus()
            self.init_ui()
        except Exception as e:
            self.show_error(f"Failed to initialize even in mock mode: {e}")
            self.master.destroy()

    def _apply_theme(self, root: tk.Tk) -> None:
        """Apply selected theme to the application."""
        theme_name = self.cfg["theme"]
        
        # Handle system theme specially
        if theme_name == "system":
            # Just use default theme for the platform
            if sys.platform == "darwin":  # macOS
                ttk_theme = "aqua"
            elif sys.platform == "win32":  # Windows
                ttk_theme = "vista"
            else:  # Linux and others
                ttk_theme = "clam"
        else:
            # Get theme from our definitions
            theme = THEMES.get(theme_name, THEMES["dark"])
            ttk_theme = theme.get("ttk_theme")
            
            # Configure colors
            if "bg" in theme:
                root.configure(bg=theme["bg"])
                style = ttk.Style()
                style.configure(".", background=theme["bg"], foreground=theme["text"])
                style.configure("TButton", background=theme["button"])
                style.configure("TEntry", fieldbackground=theme["entry"])
                style.configure("TFrame", background=theme["bg"])
                style.configure("TLabel", background=theme["bg"], foreground=theme["text"])
                
                # Set text widget colors via root options
                root.option_add("*Text.Background", theme["entry"])
                root.option_add("*Text.Foreground", theme["text"])
                
                # Set canvas colors
                self.chart_bg = theme.get("chart_bg", "#202020")
        
        # Apply ttk theme if specified
        if ttk_theme:
            try:
                ttk.Style().theme_use(ttk_theme)
            except tk.TclError:
                # Fall back to default theme if specified one not available
                pass

    def init_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        
        # Use notebook for tabs
        nb = ttk.Notebook(self)
        opt_frame = ttk.Frame(nb, padding=self.PAD)
        
        # Move existing UI elements to opt_frame
        self._build_optimizer_tab(opt_frame)
        
        # Add tabs
        nb.add(opt_frame, text="Optimiser")
        self.launch_frame = ttk.Frame(nb, padding=self.PAD)
        self._build_launch_tab(self.launch_frame)
        nb.add(self.launch_frame, text="Launch")
        
        # Add GPU Dashboard tab
        self.dashboard_frame = ttk.Frame(nb, padding=self.PAD)
        self._build_dashboard_tab(self.dashboard_frame)
        nb.add(self.dashboard_frame, text="GPU Dashboard")
        
        # Add settings tab
        self.settings_frame = ttk.Frame(nb, padding=self.PAD)
        self._build_settings_tab(self.settings_frame)
        nb.add(self.settings_frame, text="Settings")
        
        nb.pack(fill="both", expand=True)
    
    def _build_settings_tab(self, parent: ttk.Frame) -> None:
        """Create enhanced settings UI with better organization."""
        parent.columnconfigure(0, weight=1)
        
        # ------ Appearance Section ------
        appearance_frame = ttk.LabelFrame(parent, text="Appearance")
        appearance_frame.grid(sticky="ew", pady=(0, self.PAD), padx=self.PAD)
        appearance_frame.columnconfigure(1, weight=1)
        
        # Theme selection
        ttk.Label(appearance_frame, text="Theme:").grid(row=0, column=0, sticky="w", padx=self.PAD, pady=5)
        theme_combo = ttk.Combobox(
            appearance_frame, 
            textvariable=self.theme_var,
            values=["dark", "light", "system"],
            width=10,
            state="readonly"
        )
        theme_combo.grid(row=0, column=1, sticky="w", padx=self.PAD, pady=5)
        theme_combo.bind("<<ComboboxSelected>>", self._theme_changed)
        
        ttk.Button(
            appearance_frame, 
            text="Apply", 
            command=self._apply_theme_change
        ).grid(row=0, column=2, padx=self.PAD, pady=5)
        
        # ------ Monitoring Settings Section ------
        monitor_frame = ttk.LabelFrame(parent, text="Monitoring")
        monitor_frame.grid(sticky="ew", pady=(0, self.PAD), padx=self.PAD, row=1)
        monitor_frame.columnconfigure(1, weight=1)
        
        self.interval_var = tk.DoubleVar(value=self.cfg["monitor_interval"])
        ttk.Label(monitor_frame, text="Update interval (sec):").grid(row=0, column=0, padx=self.PAD, pady=5, sticky="w")
        interval_spin = ttk.Spinbox(
            monitor_frame,
            from_=0.5,
            to=10.0,
            increment=0.5,
            textvariable=self.interval_var,
            width=5
        )
        interval_spin.grid(row=0, column=1, sticky="w", padx=self.PAD, pady=5)
        
        self.alert_threshold_var = tk.IntVar(value=self.cfg["alert_threshold"])
        ttk.Label(monitor_frame, text="Alert threshold (%):").grid(row=1, column=0, padx=self.PAD, pady=5, sticky="w")
        threshold_spin = ttk.Spinbox(
            monitor_frame,
            from_=5,
            to=80,
            increment=5,
            textvariable=self.alert_threshold_var,
            width=5
        )
        threshold_spin.grid(row=1, column=1, sticky="w", padx=self.PAD, pady=5)
        
        self.alert_duration_var = tk.IntVar(value=self.cfg["alert_duration"])
        ttk.Label(monitor_frame, text="Alert after (sec):").grid(row=2, column=0, padx=self.PAD, pady=5, sticky="w")
        duration_spin = ttk.Spinbox(
            monitor_frame,
            from_=60,
            to=900,
            increment=60,
            textvariable=self.alert_duration_var,
            width=5
        )
        duration_spin.grid(row=2, column=1, sticky="w", padx=self.PAD, pady=5)
        
        # ------ Advanced Settings Section ------
        advanced_frame = ttk.LabelFrame(parent, text="Advanced Settings")
        advanced_frame.grid(sticky="ew", pady=(0, self.PAD), padx=self.PAD, row=2)
        advanced_frame.columnconfigure(0, weight=1)
        
        # GPU Memory Override
        ttk.Label(advanced_frame, text="GPU Memory Overrides:").grid(row=0, column=0, sticky="w", padx=self.PAD, pady=(5,0))
        
        # Create a frame for GPU memory overrides with a scrollbar
        override_frame = ttk.Frame(advanced_frame)
        override_frame.grid(row=1, column=0, sticky="ew", padx=self.PAD, pady=5)
        override_frame.columnconfigure(1, weight=1)
        
        # Create entry fields for each GPU's memory override
        self.memory_override_vars = {}
        for i, gpu in enumerate(self.gpus):
            gpu_name = f"{gpu.name} (GPU {gpu.index})"
            ttk.Label(override_frame, text=gpu_name).grid(row=i, column=0, sticky="w", pady=2)
            
            # Create variable and entry for memory override
            override_var = tk.StringVar(value=self.cfg.get("env_overrides", {}).get(f"DGPUOPT_MEM_{gpu.index}", ""))
            self.memory_override_vars[f"DGPUOPT_MEM_{gpu.index}"] = override_var
            
            ttk.Entry(override_frame, textvariable=override_var, width=8).grid(row=i, column=1, sticky="w", padx=(5,0), pady=2)
            ttk.Label(override_frame, text="MiB").grid(row=i, column=2, sticky="w", pady=2)
        
        # Startup options
        self.auto_check_updates = tk.BooleanVar(value=self.cfg.get("check_updates", True))
        ttk.Checkbutton(
            advanced_frame, 
            text="Check for updates on startup", 
            variable=self.auto_check_updates
        ).grid(row=2, column=0, sticky="w", padx=self.PAD, pady=5)
        
        # ------ Save Settings Button ------
        save_frame = ttk.Frame(parent)
        save_frame.grid(row=3, column=0, sticky="ew", pady=self.PAD, padx=self.PAD)
        
        ttk.Button(
            save_frame,
            text="Save All Settings",
            command=self._save_all_settings
        ).pack(side="right")
        
        # Explanation text
        ttk.Label(
            save_frame,
            text="Memory overrides take effect after restart.",
            font=("", 8, "italic")
        ).pack(side="left")
    
    def _theme_changed(self, event=None) -> None:
        """Handle theme selection change."""
        # Just update the UI to show Apply button is needed
        pass
    
    def _apply_theme_change(self) -> None:
        """Apply the selected theme immediately and save to config."""
        new_theme = self.theme_var.get()
        self.cfg["theme"] = new_theme
        configio.save_cfg(self.cfg)
        
        # Apply theme immediately instead of requiring restart
        self._apply_theme(self.master)
        
        # Force all widgets to update with new theme
        self._update_widgets_theme(self)
        
        messagebox.showinfo(
            "Theme Changed", 
            "Theme has been applied successfully."
        )
    
    def _update_widgets_theme(self, parent):
        """Recursively update theme for all widgets."""
        for widget in parent.winfo_children():
            # Skip text widgets that already have content to preserve it
            if isinstance(widget, tk.Text) and widget.get("1.0", "end").strip():
                continue
                
            # Apply theme to current widget based on its type
            if isinstance(widget, ttk.Frame) or isinstance(widget, ttk.LabelFrame):
                widget.configure(style="TFrame")
            elif isinstance(widget, ttk.Label):
                widget.configure(style="TLabel")
            elif isinstance(widget, ttk.Button):
                widget.configure(style="TButton")
            elif isinstance(widget, ttk.Entry):
                widget.configure(style="TEntry")
            elif isinstance(widget, tk.Canvas) and hasattr(self, 'chart_bg'):
                widget.configure(bg=self.chart_bg)
            
            # Recursively process child widgets
            if widget.winfo_children():
                self._update_widgets_theme(widget)

    # ---------- UI builders ----------
    def _build_optimizer_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)

        # GPU Treeview
        tv = ttk.Treeview(parent, columns=("name", "total", "free"), show="headings")
        for col, hdr in zip(("name", "total", "free"),
                            ("Name", "Total (MiB)", "Free (MiB)")):
            tv.heading(col, text=hdr)
            tv.column(col, anchor="center")
        for g in self.gpus:
            tv.insert("", "end", values=(g.name, g.mem_total, g.mem_free))
        tv.grid(sticky="ew", pady=(0, self.PAD))

        # Model path frame with preset selection
        path_frame = ttk.Frame(parent)
        ttk.Label(path_frame, text="Model path / repo:").pack(side="left")
        ttk.Entry(path_frame, textvariable=self.model_var, width=60).pack(side="left", expand=1, fill="x")
        ttk.Button(path_frame, text="Browse…", command=self._browse).pack(side="right")
        
        # Add preset selection
        self.preset_cmb = ttk.Combobox(path_frame, width=18, values=list(self.presets.keys()))
        self.preset_cmb.set("choose‑preset")
        self.preset_cmb.bind("<<ComboboxSelected>>", self._preset_selected)
        self.preset_cmb.pack(side="right")
        
        path_frame.grid(sticky="ew", pady=(0, self.PAD))
        parent.columnconfigure(0, weight=1)

        # Ctx + buttons
        ctl = ttk.Frame(parent)
        ttk.Label(ctl, text="Context size:").pack(side="left")
        ttk.Spinbox(ctl, from_=2048, to=131072, textvariable=self.ctx_var, width=8).pack(side="left")
        ttk.Button(ctl, text="Generate", command=self._refresh_outputs).pack(side="right")
        ctl.grid(sticky="ew", pady=(0, self.PAD))

        # Output text
        self.text = tk.Text(parent, height=10, wrap="word")
        self.text.grid(sticky="nsew")
        parent.rowconfigure(parent.grid_size()[1]-1, weight=1)

        # Copy + save env
        btm = ttk.Frame(parent)
        ttk.Button(btm, text="Copy llama.cpp", command=lambda: self._copy("llama")).pack(side="left")
        ttk.Button(btm, text="Copy vLLM", command=lambda: self._copy("vllm")).pack(side="left")
        ttk.Button(btm, text="Save env file", command=self._save_env).pack(side="right")
        btm.grid(sticky="ew", pady=(self.PAD, 0))

    def _build_launch_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        
        # Control buttons
        btn_frame = ttk.Frame(parent)
        ttk.Button(btn_frame, text="Launch llama.cpp", command=lambda: self._start_runner("llama")).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Launch vLLM", command=lambda: self._start_runner("vllm")).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Stop", command=self._stop_runner).pack(side="left", padx=5)
        btn_frame.grid(row=0, column=0, sticky="ew", pady=(0, self.PAD))
        
        # Log output
        log_frame = ttk.LabelFrame(parent, text="Execution Log")
        self.log_box = tk.Text(log_frame, height=15, wrap="word")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=scrollbar.set)
        self.log_box.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        log_frame.grid(row=1, column=0, sticky="nsew")
        
        # GPU utilization chart
        chart_frame = ttk.LabelFrame(parent, text="GPU Utilization")
        self.chart = tk.Canvas(chart_frame, height=120, bg="#202020")
        self.chart.pack(fill="both", expand=True)
        chart_frame.grid(row=2, column=0, sticky="ew", pady=(self.PAD, 0))
        
        # Start log refreshing
        self.after(500, self._pump_log)

    def _build_dashboard_tab(self, parent: ttk.Frame) -> None:
        """Create the GPU Dashboard tab with detailed GPU information and visualizations."""
        parent.columnconfigure(0, weight=1)
        
        # Create a frame for the dashboard
        top_frame = ttk.Frame(parent)
        top_frame.grid(row=0, column=0, sticky="ew")
        
        # Create GPU detail frames
        self.gpu_detail_frames = []
        for i, gpu in enumerate(self.gpus):
            gpu_frame = ttk.LabelFrame(parent, text=f"GPU {gpu.index}: {gpu.short_name}")
            gpu_frame.grid(row=i+1, column=0, sticky="ew", pady=(0, self.PAD))
            gpu_frame.columnconfigure(1, weight=1)
            
            # Add hardware info section
            hw_frame = ttk.Frame(gpu_frame)
            hw_frame.grid(row=0, column=0, rowspan=4, sticky="ns", padx=self.PAD, pady=self.PAD)
            
            ttk.Label(hw_frame, text="Architecture:").grid(row=0, column=0, sticky="w", pady=2)
            self.arch_label = ttk.Label(hw_frame, text=gpu.architecture)
            self.arch_label.grid(row=0, column=1, sticky="w", padx=self.PAD, pady=2)
            
            ttk.Label(hw_frame, text="CUDA Cores:").grid(row=1, column=0, sticky="w", pady=2)
            self.cores_label = ttk.Label(hw_frame, text=str(gpu.cuda_cores))
            self.cores_label.grid(row=1, column=1, sticky="w", padx=self.PAD, pady=2)
            
            ttk.Label(hw_frame, text="Compute:").grid(row=2, column=0, sticky="w", pady=2)
            self.compute_label = ttk.Label(hw_frame, text=gpu.compute_capability)
            self.compute_label.grid(row=2, column=1, sticky="w", padx=self.PAD, pady=2)
            
            ttk.Label(hw_frame, text="PCIe:").grid(row=3, column=0, sticky="w", pady=2)
            self.pcie_label = ttk.Label(hw_frame, text=f"{gpu.pcie_gen} x{gpu.pcie_width}")
            self.pcie_label.grid(row=3, column=1, sticky="w", padx=self.PAD, pady=2)
            
            # Memory usage bar
            ttk.Label(gpu_frame, text="Memory:").grid(row=0, column=1, sticky="w", pady=2)
            mem_frame = ttk.Frame(gpu_frame)
            mem_frame.grid(row=0, column=2, sticky="ew", pady=2)
            mem_frame.columnconfigure(0, weight=1)
            
            self.mem_bar = ttk.Progressbar(mem_frame, length=200, mode="determinate")
            self.mem_bar["value"] = gpu.mem_used_percent
            self.mem_bar.grid(row=0, column=0, sticky="ew")
            
            self.mem_text = ttk.Label(
                mem_frame, 
                text=f"{gpu.mem_used_gb:.1f} GB / {gpu.mem_total_gb:.1f} GB ({gpu.mem_used_percent:.1f}%)"
            )
            self.mem_text.grid(row=1, column=0, sticky="e")
            
            # Performance metrics
            perf_frame = ttk.Frame(gpu_frame)
            perf_frame.grid(row=1, column=1, columnspan=2, sticky="ew", pady=self.PAD)
            perf_frame.columnconfigure(1, weight=1)
            perf_frame.columnconfigure(3, weight=1)
            
            # GPU Utilization
            ttk.Label(perf_frame, text="GPU:").grid(row=0, column=0, sticky="w", padx=(0, 5))
            self.gpu_util_bar = ttk.Progressbar(perf_frame, length=100, mode="determinate")
            self.gpu_util_bar["value"] = gpu.gpu_utilization
            self.gpu_util_bar.grid(row=0, column=1, sticky="ew", padx=5)
            self.gpu_util_text = ttk.Label(perf_frame, text=f"{gpu.gpu_utilization}%")
            self.gpu_util_text.grid(row=0, column=2, sticky="w", padx=5)
            
            # Temperature
            ttk.Label(perf_frame, text="Temp:").grid(row=0, column=3, sticky="w", padx=(10, 5))
            self.temp_bar = ttk.Progressbar(perf_frame, length=100, mode="determinate")
            self.temp_bar["maximum"] = 100  # Max reasonable temperature
            self.temp_bar["value"] = gpu.temperature
            
            # Set color based on temperature
            if gpu.temperature < 60:
                style = ttk.Style()
                style.configure("temp_cool.Horizontal.TProgressbar", background="green")
                self.temp_bar.configure(style="temp_cool.Horizontal.TProgressbar")
            elif gpu.temperature < 80:
                style = ttk.Style()
                style.configure("temp_warm.Horizontal.TProgressbar", background="orange")
                self.temp_bar.configure(style="temp_warm.Horizontal.TProgressbar")
            else:
                style = ttk.Style()
                style.configure("temp_hot.Horizontal.TProgressbar", background="red")
                self.temp_bar.configure(style="temp_hot.Horizontal.TProgressbar")
                
            self.temp_bar.grid(row=0, column=4, sticky="ew", padx=5)
            self.temp_text = ttk.Label(perf_frame, text=f"{gpu.temperature}°C")
            self.temp_text.grid(row=0, column=5, sticky="w", padx=5)
            
            # Power and Fan
            ttk.Label(perf_frame, text="Power:").grid(row=1, column=0, sticky="w", padx=(0, 5))
            self.power_bar = ttk.Progressbar(perf_frame, length=100, mode="determinate")
            self.power_bar["value"] = gpu.power_usage_percent
            self.power_bar.grid(row=1, column=1, sticky="ew", padx=5)
            self.power_text = ttk.Label(
                perf_frame, 
                text=f"{gpu.power_usage:.1f}W / {gpu.power_limit:.1f}W"
            )
            self.power_text.grid(row=1, column=2, sticky="w", padx=5)
            
            ttk.Label(perf_frame, text="Fan:").grid(row=1, column=3, sticky="w", padx=(10, 5))
            self.fan_bar = ttk.Progressbar(perf_frame, length=100, mode="determinate")
            self.fan_bar["value"] = gpu.fan_speed
            self.fan_bar.grid(row=1, column=4, sticky="ew", padx=5)
            self.fan_text = ttk.Label(perf_frame, text=f"{gpu.fan_speed}%")
            self.fan_text.grid(row=1, column=5, sticky="w", padx=5)
            
            # Clock speeds
            clock_frame = ttk.Frame(gpu_frame)
            clock_frame.grid(row=2, column=1, columnspan=2, sticky="ew", pady=self.PAD)
            
            ttk.Label(clock_frame, text="GPU Clock:").grid(row=0, column=0, sticky="w")
            self.gpu_clock = ttk.Label(clock_frame, text=f"{gpu.graphics_clock} MHz")
            self.gpu_clock.grid(row=0, column=1, sticky="w", padx=self.PAD)
            
            ttk.Label(clock_frame, text="Memory Clock:").grid(row=0, column=2, sticky="w", padx=(20, 0))
            self.mem_clock = ttk.Label(clock_frame, text=f"{gpu.memory_clock} MHz")
            self.mem_clock.grid(row=0, column=3, sticky="w", padx=self.PAD)
            
            ttk.Label(clock_frame, text="Driver:").grid(row=0, column=4, sticky="w", padx=(20, 0))
            self.driver_text = ttk.Label(clock_frame, text=gpu.driver_version)
            self.driver_text.grid(row=0, column=5, sticky="w", padx=self.PAD)
            
            # Store references for updates
            self.gpu_detail_frames.append({
                "gpu_index": gpu.index,
                "mem_bar": self.mem_bar,
                "mem_text": self.mem_text,
                "gpu_util_bar": self.gpu_util_bar,
                "gpu_util_text": self.gpu_util_text,
                "temp_bar": self.temp_bar,
                "temp_text": self.temp_text,
                "power_bar": self.power_bar,
                "power_text": self.power_text,
                "fan_bar": self.fan_bar,
                "fan_text": self.fan_text,
                "gpu_clock": self.gpu_clock,
                "mem_clock": self.mem_clock
            })
        
        # History graph frame
        history_frame = ttk.LabelFrame(parent, text="Performance History")
        history_frame.grid(row=len(self.gpus)+1, column=0, sticky="ew", pady=(0, self.PAD))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        
        # Create canvas for history graphs
        self.history_canvas = tk.Canvas(history_frame, height=150, bg=self.chart_bg)
        self.history_canvas.grid(row=0, column=0, sticky="nsew", padx=self.PAD, pady=self.PAD)
        
        # Start dashboard updating
        self.after(1000, self._update_dashboard)
    
    def _update_dashboard(self) -> None:
        """Update the GPU Dashboard with the latest telemetry data."""
        try:
            # Try to get telemetry data from the queue without blocking
            try:
                tele = self.tele_q.get_nowait()
            except queue.Empty:
                # If no data available, just reschedule the update and return
                self.after(1000, self._update_dashboard)
                return
                
            for frame in self.gpu_detail_frames:
                idx = frame["gpu_index"]
                
                # Make sure we have data for this GPU
                if idx < len(tele.load) and idx < len(tele.mem_used):
                    # Update memory usage
                    mem_used = tele.mem_used[idx]
                    gpu = next((g for g in self.gpus if g.index == idx), None)
                    if gpu:
                        mem_total = gpu.mem_total
                        mem_percent = (mem_used / mem_total) * 100 if mem_total else 0
                        
                        frame["mem_bar"]["value"] = mem_percent
                        frame["mem_text"].config(
                            text=f"{mem_used/1024:.1f} GB / {mem_total/1024:.1f} GB ({mem_percent:.1f}%)"
                        )
                        
                        # Update GPU utilization
                        frame["gpu_util_bar"]["value"] = tele.load[idx]
                        frame["gpu_util_text"].config(text=f"{tele.load[idx]}%")
                        
                        # Update temperature if available
                        if idx < len(tele.temperature):
                            temp = tele.temperature[idx]
                            frame["temp_bar"]["value"] = temp
                            frame["temp_text"].config(text=f"{temp}°C")
                            
                            # Update color based on temperature
                            style = ttk.Style()
                            if temp < 60:
                                style.configure("temp_cool.Horizontal.TProgressbar", background="green")
                                frame["temp_bar"].configure(style="temp_cool.Horizontal.TProgressbar")
                            elif temp < 80:
                                style.configure("temp_warm.Horizontal.TProgressbar", background="orange")
                                frame["temp_bar"].configure(style="temp_warm.Horizontal.TProgressbar")
                            else:
                                style.configure("temp_hot.Horizontal.TProgressbar", background="red")
                                frame["temp_bar"].configure(style="temp_hot.Horizontal.TProgressbar")
                        
                        # Update power usage if available
                        if idx < len(tele.power_usage):
                            power = tele.power_usage[idx]
                            if gpu.power_limit > 0:
                                power_percent = (power / gpu.power_limit) * 100
                                frame["power_bar"]["value"] = power_percent
                            frame["power_text"].config(text=f"{power:.1f}W / {gpu.power_limit:.1f}W")
                        
                        # Update fan speed if available
                        if idx < len(tele.fan_speed):
                            fan = tele.fan_speed[idx]
                            frame["fan_bar"]["value"] = fan
                            frame["fan_text"].config(text=f"{fan}%")
                        
                        # Update clock speeds if available
                        if idx < len(tele.graphics_clock):
                            frame["gpu_clock"].config(text=f"{tele.graphics_clock[idx]} MHz")
                        
                        if idx < len(tele.memory_clock):
                            frame["mem_clock"].config(text=f"{tele.memory_clock[idx]} MHz")
            
            # Render history graph
            self._render_history_graph()
            
        except Exception as e:
            # Log any errors but don't crash
            self.logger.error(f"Error updating dashboard: {e}")
            
        # Schedule the next update
        self.after(1000, self._update_dashboard)
    
    def _render_history_graph(self) -> None:
        """Render the performance history graph on the history canvas."""
        # Store telemetry history
        if not hasattr(self, 'dashboard_history'):
            # Initialize history if it doesn't exist
            self.dashboard_history = {
                'timestamps': [],
                'gpu_util': [[] for _ in range(len(self.gpus))],
                'mem_util': [[] for _ in range(len(self.gpus))],
                'temp': [[] for _ in range(len(self.gpus))]
            }
        
        # Add latest telemetry to history
        try:
            tele = self.tele_q.get_nowait()
            
            # Add timestamp
            self.dashboard_history['timestamps'].append(tele.ts)
            
            # Limit history to 60 seconds (assuming 1 second interval)
            max_history = 60
            if len(self.dashboard_history['timestamps']) > max_history:
                self.dashboard_history['timestamps'] = self.dashboard_history['timestamps'][-max_history:]
                
            # Add GPU utilization
            for i, load in enumerate(tele.load):
                if i < len(self.dashboard_history['gpu_util']):
                    self.dashboard_history['gpu_util'][i].append(load)
                    if len(self.dashboard_history['gpu_util'][i]) > max_history:
                        self.dashboard_history['gpu_util'][i] = self.dashboard_history['gpu_util'][i][-max_history:]
            
            # Add memory utilization
            for i, util in enumerate(tele.memory_util):
                if i < len(self.dashboard_history['mem_util']):
                    self.dashboard_history['mem_util'][i].append(util)
                    if len(self.dashboard_history['mem_util'][i]) > max_history:
                        self.dashboard_history['mem_util'][i] = self.dashboard_history['mem_util'][i][-max_history:]
            
            # Add temperature
            for i, temp in enumerate(tele.temperature):
                if i < len(self.dashboard_history['temp']):
                    self.dashboard_history['temp'][i].append(temp)
                    if len(self.dashboard_history['temp'][i]) > max_history:
                        self.dashboard_history['temp'][i] = self.dashboard_history['temp'][i][-max_history:]
            
        except queue.Empty:
            pass
        
        # Clear canvas
        self.history_canvas.delete("all")
        
        # Draw background
        w = self.history_canvas.winfo_width()
        h = self.history_canvas.winfo_height()
        
        if w <= 1 or h <= 1:
            # Canvas not properly initialized yet
            return
            
        # Draw grid lines
        for i in range(0, 101, 20):
            y = h - (i * h / 100)
            self.history_canvas.create_line(0, y, w, y, fill="#444444", dash=(1, 2))
            self.history_canvas.create_text(5, y, text=f"{i}%", anchor="w", fill="#bbbbbb", font=("", 8))
        
        # Draw temperature scale on right side
        for i in range(0, 101, 20):
            y = h - (i * h / 100)
            self.history_canvas.create_text(w-5, y, text=f"{i}°C", anchor="e", fill="#ff6600", font=("", 8))
        
        # Draw metrics
        if len(self.dashboard_history['timestamps']) > 1:
            time_span = self.dashboard_history['timestamps'][-1] - self.dashboard_history['timestamps'][0]
            if time_span > 0:
                # Draw GPU utilization
                for i, gpu_util in enumerate(self.dashboard_history['gpu_util']):
                    if len(gpu_util) > 1:
                        points = []
                        for j, util in enumerate(gpu_util):
                            x = (self.dashboard_history['timestamps'][j] - self.dashboard_history['timestamps'][0]) / time_span * w
                            y = h - (util * h / 100)
                            points.extend([x, y])
                        
                        if points:
                            self.history_canvas.create_line(points, fill=self.gpu_colors[i], width=2, smooth=True)
                            
                # Draw memory utilization as dashed lines
                for i, mem_util in enumerate(self.dashboard_history['mem_util']):
                    if len(mem_util) > 1:
                        points = []
                        for j, util in enumerate(mem_util):
                            x = (self.dashboard_history['timestamps'][j] - self.dashboard_history['timestamps'][0]) / time_span * w
                            y = h - (util * h / 100)
                            points.extend([x, y])
                        
                        if points:
                            self.history_canvas.create_line(points, fill=self.gpu_colors[i], width=1, dash=(4, 2))
                
                # Draw temperature as dotted lines
                for i, temp in enumerate(self.dashboard_history['temp']):
                    if len(temp) > 1:
                        points = []
                        for j, t in enumerate(temp):
                            x = (self.dashboard_history['timestamps'][j] - self.dashboard_history['timestamps'][0]) / time_span * w
                            y = h - (t * h / 100)
                            points.extend([x, y])
                        
                        if points:
                            self.history_canvas.create_line(points, fill="#ff6600", width=1, dash=(2, 4))
                            
        # Draw legend
        legend_items = [
            {"name": "GPU Util", "color": self.gpu_colors[0], "style": "solid"},
            {"name": "Mem Util", "color": self.gpu_colors[0], "style": "dashed"},
            {"name": "Temperature", "color": "#ff6600", "style": "dotted"}
        ]
        
        legend_x = 10
        legend_y = 10
        for item in legend_items:
            # Draw color sample
            if item["style"] == "solid":
                self.history_canvas.create_line(legend_x, legend_y, legend_x+20, legend_y, fill=item["color"], width=2)
            elif item["style"] == "dashed":
                self.history_canvas.create_line(legend_x, legend_y, legend_x+20, legend_y, fill=item["color"], width=1, dash=(4, 2))
            else:  # dotted
                self.history_canvas.create_line(legend_x, legend_y, legend_x+20, legend_y, fill=item["color"], width=1, dash=(2, 4))
                
            # Draw label
            self.history_canvas.create_text(legend_x+25, legend_y, text=item["name"], fill="#ffffff", anchor="w")
            legend_x += 100

    # ---------- callbacks ----------
    def _browse(self) -> None:
        path = filedialog.askopenfilename(title="Select model / folder")
        if path:
            self.model_var.set(path)
            # Update config
            self.cfg["last_model"] = path
            configio.save_cfg(self.cfg)

    def _refresh_outputs(self) -> None:
        split = optimizer.split_string(self.gpus)
        llama_cmd = optimizer.llama_command(self.model_var.get(), self.ctx_var.get(), split)
        vllm_cmd = optimizer.vllm_command(self.model_var.get(), len(self.gpus))
        out = (
            f"# gpu‑split suggestion\n{split}\n\n"
            f"# llama.cpp\n{llama_cmd}\n\n"
            f"# vLLM\n{vllm_cmd}\n"
        )
        self.text.delete("1.0", "end")
        self.text.insert("1.0", out)

    def _copy(self, which: str) -> None:
        content = self.text.get("1.0", "end").splitlines()
        if which == "llama":
            snippet = "\n".join(line for line in content if line.startswith("./main"))
        else:
            snippet = "\n".join(line for line in content if line.startswith("python -m vllm"))
        self.clipboard_clear()
        self.clipboard_append(snippet)
        messagebox.showinfo("Copied", f"{which} command copied to clipboard!")

    def _save_env(self) -> None:
        filename = filedialog.asksaveasfilename(
            title="Save env file",
            defaultextension=".sh" if not tk.sys.platform.startswith("win") else ".ps1",
            filetypes=[("Shell script", "*.sh"), ("PowerShell", "*.ps1"), ("All", "*.*")]
        )
        if filename:
            optimizer.make_env_file(self.gpus, pathlib.Path(filename))
            messagebox.showinfo("Saved", f"Env file saved → {filename}")
    
    def _preset_selected(self, *_) -> None:
        key = self.preset_cmb.get()
        pre = self.presets[key]
        self.model_var.set(pre["model"])
        self.ctx_var.set(pre.get("ctx", 65536))
    
    def _start_runner(self, which: str) -> None:
        if self.runner:
            self.runner.stop()
        split = optimizer.split_string(self.gpus)
        cmd = optimizer.llama_command(self.model_var.get(), self.ctx_var.get(), split) if which=="llama" \
            else optimizer.vllm_command(self.model_var.get(), len(self.gpus))
        self.runner = Runner(cmd)
        self.runner.start()
        self.log_box.delete("1.0", "end")
    
    def _stop_runner(self) -> None:
        if self.runner:
            self.runner.stop()
            self.log_box.insert("end", "Process stopped.\n")
            self.log_box.see("end")
    
    def _pump_log(self) -> None:
        if self.runner:
            try:
                while True:
                    line = self.runner.q.get_nowait()
                    self.log_box.insert("end", line+"\n")
                    self.log_box.see("end")
            except queue.Empty:
                pass
        self.after(500, self._pump_log)
    
    def _tick_chart(self) -> None:
        try:
            tele = self.tele_q.get_nowait()
            
            # Store all GPU loads in history
            self.tele_hist.append(tele.load)
            self.tele_hist = self.tele_hist[-120:]  # keep 2 min
            
            # Clear and draw chart
            self.chart.delete("all")
            w = self.chart.winfo_width()
            h = self.chart.winfo_height()
            
            if w > 1 and self.tele_hist:  # Ensure chart is visible
                step = w / len(self.tele_hist)
                
                # Draw load history for each GPU
                for t_idx, loads in enumerate(self.tele_hist):
                    x = int(t_idx * step)
                    y_bottom = h
                    
                    # Draw stacked bars for each GPU
                    for g_idx, load in enumerate(loads):
                        if g_idx < len(self.gpus):  # Ensure we have data for this GPU
                            y_top = y_bottom - (load * h / 100)  # Scale load to chart height
                            self.chart.create_line(x, y_bottom, x, y_top, 
                                                  fill=self.gpu_colors[g_idx])
                            y_bottom = y_top
                
                # Draw legend
                legend_x = 10
                legend_y = 15
                for i, gpu in enumerate(self.gpus):
                    if i < len(self.gpu_colors):
                        # Draw color sample
                        self.chart.create_rectangle(legend_x, legend_y, 
                                                   legend_x + 10, legend_y + 10, 
                                                   fill=self.gpu_colors[i], outline="")
                        # Draw GPU name
                        self.chart.create_text(legend_x + 15, legend_y + 5, 
                                              text=f"GPU {gpu.index}", 
                                              fill="white", anchor="w")
                        legend_y += 15
                        
        except queue.Empty:
            pass
        except Exception as e:
            # Handle any other exceptions gracefully
            print(f"Chart error: {e}")
            
        self.after(1000, self._tick_chart)

    def _save_all_settings(self):
        """Save all settings from the settings tab to config."""
        # Update monitoring settings
        self.cfg["monitor_interval"] = self.interval_var.get()
        self.cfg["alert_threshold"] = self.alert_threshold_var.get()
        self.cfg["alert_duration"] = self.alert_duration_var.get()
        
        # Update advanced settings
        self.cfg["check_updates"] = self.auto_check_updates.get()
        
        # Update memory overrides
        if "env_overrides" not in self.cfg:
            self.cfg["env_overrides"] = {}
            
        # Process memory overrides, removing empty ones
        for key, var in self.memory_override_vars.items():
            value = var.get().strip()
            if value:
                try:
                    # Validate as integer
                    int_value = int(value)
                    self.cfg["env_overrides"][key] = str(int_value)
                except ValueError:
                    # Skip invalid values
                    messagebox.showwarning("Invalid Value", f"Memory override for {key} must be a number. Ignoring.")
            else:
                # Remove empty overrides
                if key in self.cfg["env_overrides"]:
                    del self.cfg["env_overrides"][key]
        
        # Save the updated configuration
        configio.save_cfg(self.cfg)
        messagebox.showinfo("Settings Saved", "All settings have been saved successfully.\nSome changes may require a restart to take effect.")
        
        # Update monitoring settings immediately if possible
        # (This would require modifications to the telemetry system)


def run_app() -> None:
    root = tk.Tk()
    root.title("Dual‑GPU Optimiser")
    root.minsize(800, 480)
    
    try:
        # Set application icon if available
        try:
            icon_path = pathlib.Path(__file__).parent / "assets" / "app_icon.ico"
            if icon_path.exists():
                root.iconbitmap(icon_path)
        except Exception as icon_err:
            # Non-critical error, just log it
            logging.getLogger("dualgpuopt.gui").warning(f"Could not load application icon: {icon_err}")
        
        app = DualGpuApp(root)
        app.pack(fill="both", expand=True)
        root.mainloop()
    except Exception as e:
        logging.getLogger("dualgpuopt.gui").error(f"Application error: {e}", exc_info=True)
        messagebox.showerror("Error", f"An error occurred: {e}\n\nCheck the logs for more details.") 