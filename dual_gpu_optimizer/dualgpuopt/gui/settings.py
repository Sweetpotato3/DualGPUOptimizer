"""
Settings tab for the DualGPUOptimizer GUI.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import pathlib
from typing import Dict, List, Callable, Any, Optional

from dualgpuopt.gpu_info import GPU
from dualgpuopt.configio import save_cfg
from dualgpuopt.gui.theme import THEMES, AVAILABLE_TTK_THEMES


class SettingsTab(ttk.Frame):
    """Settings tab that allows configuration of application settings."""
    
    def __init__(self, parent: ttk.Frame, gpus: List[GPU], config: Dict[str, Any],
                 theme_change_callback: Callable[[str, str], None]) -> None:
        """
        Initialize the settings tab.
        
        Args:
            parent: Parent frame
            gpus: List of GPU objects
            config: Application configuration dictionary
            theme_change_callback: Callback for theme changes
        """
        super().__init__(parent, padding=8)
        self.parent = parent
        self.gpus = gpus
        self.config = config
        self.theme_change_callback = theme_change_callback
        self.columnconfigure(0, weight=1)
        
        # Create a scrollable canvas to contain all settings
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Make the scrollable frame take the full width
        scrollable_frame.columnconfigure(0, weight=1)
        
        # ------ Appearance Section ------
        appearance_frame = ttk.LabelFrame(scrollable_frame, text="Appearance")
        appearance_frame.grid(sticky="ew", pady=(0, 8), padx=8)
        appearance_frame.columnconfigure(1, weight=1)
        
        # Theme selection
        self.theme_var = tk.StringVar(value=config.get("theme", "dark"))
        ttk.Label(appearance_frame, text="Color Theme:").grid(row=0, column=0, sticky="w", padx=8, pady=5)
        theme_combo = ttk.Combobox(
            appearance_frame, 
            textvariable=self.theme_var,
            values=list(THEMES.keys()),
            width=10,
            state="readonly"
        )
        theme_combo.grid(row=0, column=1, sticky="w", padx=8, pady=5)
        
        # Add TTK theme selection if ttkthemes is available
        self.ttk_theme_var = tk.StringVar(value=config.get("ttk_theme", ""))
        if AVAILABLE_TTK_THEMES:
            ttk.Label(appearance_frame, text="Widget Style:").grid(row=1, column=0, sticky="w", padx=8, pady=5)
            ttk_theme_combo = ttk.Combobox(
                appearance_frame,
                textvariable=self.ttk_theme_var,
                values=AVAILABLE_TTK_THEMES,
                width=10,
                state="readonly"
            )
            ttk_theme_combo.grid(row=1, column=1, sticky="w", padx=8, pady=5)
        
        ttk.Button(
            appearance_frame, 
            text="Apply Theme", 
            command=self._apply_theme_change
        ).grid(row=0, column=2, padx=8, pady=5)
        
        # ------ GPU Overclocking Section ------
        overclocking_frame = ttk.LabelFrame(scrollable_frame, text="GPU Overclocking")
        overclocking_frame.grid(sticky="ew", pady=(0, 8), padx=8, row=1)
        overclocking_frame.columnconfigure(1, weight=1)
        
        # GPU selection for overclocking
        ttk.Label(overclocking_frame, text="GPU:").grid(row=0, column=0, sticky="w", padx=8, pady=5)
        self.oc_gpu_var = tk.StringVar()
        gpu_values = [f"GPU {i}: {gpu.short_name}" for i, gpu in enumerate(self.gpus)]
        self.oc_gpu_combo = ttk.Combobox(
            overclocking_frame,
            textvariable=self.oc_gpu_var,
            values=gpu_values,
            width=20,
            state="readonly"
        )
        if gpu_values:
            self.oc_gpu_combo.current(0)
        self.oc_gpu_combo.grid(row=0, column=1, sticky="w", padx=8, pady=5)
        self.oc_gpu_combo.bind("<<ComboboxSelected>>", self._update_oc_controls)
        
        # Create overclocking sliders frame
        oc_sliders_frame = ttk.Frame(overclocking_frame)
        oc_sliders_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=5)
        oc_sliders_frame.columnconfigure(1, weight=1)
        
        # Core Clock Offset slider
        ttk.Label(oc_sliders_frame, text="Core Clock Offset:").grid(row=0, column=0, sticky="w", pady=2)
        self.core_clock_var = tk.IntVar(value=0)
        self.core_clock_scale = ttk.Scale(
            oc_sliders_frame, 
            from_=-200, 
            to=200, 
            orient="horizontal",
            variable=self.core_clock_var,
            command=lambda v: self._update_label(self.core_clock_label, f"{int(float(v))} MHz")
        )
        self.core_clock_scale.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.core_clock_label = ttk.Label(oc_sliders_frame, text="0 MHz", width=8)
        self.core_clock_label.grid(row=0, column=2, padx=5, pady=2)
        
        # Memory Clock Offset slider
        ttk.Label(oc_sliders_frame, text="Memory Clock Offset:").grid(row=1, column=0, sticky="w", pady=2)
        self.memory_clock_var = tk.IntVar(value=0)
        self.memory_clock_scale = ttk.Scale(
            oc_sliders_frame, 
            from_=-1000, 
            to=1500, 
            orient="horizontal",
            variable=self.memory_clock_var,
            command=lambda v: self._update_label(self.memory_clock_label, f"{int(float(v))} MHz")
        )
        self.memory_clock_scale.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.memory_clock_label = ttk.Label(oc_sliders_frame, text="0 MHz", width=8)
        self.memory_clock_label.grid(row=1, column=2, padx=5, pady=2)
        
        # Power Limit slider
        ttk.Label(oc_sliders_frame, text="Power Limit:").grid(row=2, column=0, sticky="w", pady=2)
        self.power_limit_var = tk.IntVar(value=100)
        self.power_limit_scale = ttk.Scale(
            oc_sliders_frame, 
            from_=50, 
            to=120, 
            orient="horizontal",
            variable=self.power_limit_var,
            command=lambda v: self._update_label(self.power_limit_label, f"{int(float(v))}%")
        )
        self.power_limit_scale.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        self.power_limit_label = ttk.Label(oc_sliders_frame, text="100%", width=8)
        self.power_limit_label.grid(row=2, column=2, padx=5, pady=2)
        
        # Fan Control slider
        ttk.Label(oc_sliders_frame, text="Fan Speed:").grid(row=3, column=0, sticky="w", pady=2)
        self.fan_speed_var = tk.IntVar(value=0)
        self.fan_speed_scale = ttk.Scale(
            oc_sliders_frame, 
            from_=0, 
            to=100, 
            orient="horizontal",
            variable=self.fan_speed_var,
            command=lambda v: self._update_label(self.fan_speed_label, f"{int(float(v))}%")
        )
        self.fan_speed_scale.grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        self.fan_speed_label = ttk.Label(oc_sliders_frame, text="Auto", width=8)
        self.fan_speed_label.grid(row=3, column=2, padx=5, pady=2)
        
        # Auto fan checkbox
        self.auto_fan_var = tk.BooleanVar(value=True)
        auto_fan_check = ttk.Checkbutton(
            oc_sliders_frame,
            text="Auto Fan",
            variable=self.auto_fan_var,
            command=self._toggle_fan_control
        )
        auto_fan_check.grid(row=3, column=3, padx=5, pady=2)
        
        # Overclocking buttons
        oc_buttons_frame = ttk.Frame(overclocking_frame)
        oc_buttons_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=8, pady=5)
        
        ttk.Button(
            oc_buttons_frame,
            text="Apply Overclock",
            command=self._apply_overclock
        ).grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Button(
            oc_buttons_frame,
            text="Reset",
            command=self._reset_overclock
        ).grid(row=0, column=1, padx=5, pady=5)
        
        # Note about overclocking
        warning_frame = ttk.Frame(overclocking_frame)
        warning_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=8, pady=5)
        
        warning_text = (
            "Warning: Overclocking may void warranty and can potentially damage hardware. "
            "Use at your own risk. Ensure your cooling is adequate."
        )
        warning_label = ttk.Label(
            warning_frame,
            text=warning_text,
            wraplength=400,
            justify="left"
        )
        warning_label.grid(row=0, column=0, sticky="w")
        
        # ------ Application Settings Section ------
        app_settings_frame = ttk.LabelFrame(scrollable_frame, text="Application Settings")
        app_settings_frame.grid(sticky="ew", pady=(0, 8), padx=8, row=2)
        app_settings_frame.columnconfigure(1, weight=1)
        
        # Startup behavior
        ttk.Label(app_settings_frame, text="Start minimized:").grid(row=0, column=0, sticky="w", padx=8, pady=5)
        self.start_min_var = tk.BooleanVar(value=config.get("start_minimized", False))
        start_min_check = ttk.Checkbutton(
            app_settings_frame,
            variable=self.start_min_var
        )
        start_min_check.grid(row=0, column=1, sticky="w", padx=8, pady=5)
        
        # GPU idle detection
        ttk.Label(app_settings_frame, text="Enable GPU idle alerts:").grid(row=1, column=0, sticky="w", padx=8, pady=5)
        self.idle_alerts_var = tk.BooleanVar(value=config.get("idle_alerts", True))
        idle_alerts_check = ttk.Checkbutton(
            app_settings_frame,
            variable=self.idle_alerts_var
        )
        idle_alerts_check.grid(row=1, column=1, sticky="w", padx=8, pady=5)
        
        # Idle threshold
        ttk.Label(app_settings_frame, text="Idle threshold (%):").grid(row=2, column=0, sticky="w", padx=8, pady=5)
        self.idle_threshold_var = tk.IntVar(value=config.get("idle_threshold", 30))
        idle_threshold_entry = ttk.Entry(
            app_settings_frame,
            textvariable=self.idle_threshold_var,
            width=5
        )
        idle_threshold_entry.grid(row=2, column=1, sticky="w", padx=8, pady=5)
        
        # Idle time
        ttk.Label(app_settings_frame, text="Idle time (minutes):").grid(row=3, column=0, sticky="w", padx=8, pady=5)
        self.idle_time_var = tk.IntVar(value=config.get("idle_time", 5))
        idle_time_entry = ttk.Entry(
            app_settings_frame,
            textvariable=self.idle_time_var,
            width=5
        )
        idle_time_entry.grid(row=3, column=1, sticky="w", padx=8, pady=5)
        
        # ------ Save Button ------
        save_frame = ttk.Frame(scrollable_frame)
        save_frame.grid(row=3, column=0, sticky="ew", pady=8, padx=8)
        
        ttk.Button(
            save_frame,
            text="Save All Settings",
            command=self._save_all_settings
        ).pack(side="right")
        
        # Initialize the fan control state
        self._toggle_fan_control()
    
    def _update_label(self, label: ttk.Label, text: str) -> None:
        """
        Update a label with the given text.
        
        Args:
            label: Label widget to update
            text: New text for the label
        """
        label.config(text=text)
    
    def _toggle_fan_control(self) -> None:
        """Enable or disable fan control based on the auto fan checkbox."""
        if self.auto_fan_var.get():
            self.fan_speed_scale.config(state="disabled")
            self.fan_speed_label.config(text="Auto")
        else:
            self.fan_speed_scale.config(state="normal")
            value = int(self.fan_speed_var.get())
            self.fan_speed_label.config(text=f"{value}%")
    
    def _update_oc_controls(self, event=None) -> None:
        """Update overclocking controls when GPU selection changes."""
        selected = self.oc_gpu_var.get()
        if not selected:
            return
            
        # Extract GPU index from selection
        try:
            gpu_idx = int(selected.split(":")[0].replace("GPU", "").strip())
            
            # Get saved overclock settings for this GPU from config if available
            gpu_oc = self.config.get("gpu_overclock", {}).get(str(gpu_idx), {})
            
            # Update sliders with saved values
            self.core_clock_var.set(gpu_oc.get("core", 0))
            self.memory_clock_var.set(gpu_oc.get("memory", 0))
            self.power_limit_var.set(gpu_oc.get("power", 100))
            self.fan_speed_var.set(gpu_oc.get("fan", 0))
            self.auto_fan_var.set(gpu_oc.get("auto_fan", True))
            
            # Update labels
            self._update_label(self.core_clock_label, f"{self.core_clock_var.get()} MHz")
            self._update_label(self.memory_clock_label, f"{self.memory_clock_var.get()} MHz")
            self._update_label(self.power_limit_label, f"{self.power_limit_var.get()}%")
            
            # Update fan control
            self._toggle_fan_control()
            
        except (ValueError, IndexError):
            pass
    
    def _apply_overclock(self) -> None:
        """Apply overclocking settings to the selected GPU."""
        selected = self.oc_gpu_var.get()
        if not selected:
            return
            
        # Extract GPU index from selection
        try:
            gpu_idx = int(selected.split(":")[0].replace("GPU", "").strip())
            
            # Get the GPU settings
            core_offset = self.core_clock_var.get()
            memory_offset = self.memory_clock_var.get()
            power_limit = self.power_limit_var.get()
            fan_speed = self.fan_speed_var.get() if not self.auto_fan_var.get() else 0
            auto_fan = self.auto_fan_var.get()
            
            # This is where we would apply settings to the actual GPU
            # For now, we'll just show a message and save the settings
            
            message = (
                f"Applying to GPU {gpu_idx}:\n"
                f"Core: {core_offset} MHz\n"
                f"Memory: {memory_offset} MHz\n"
                f"Power: {power_limit}%\n"
                f"Fan: {'Auto' if auto_fan else f'{fan_speed}%'}"
            )
            
            messagebox.showinfo("Overclock Settings", message)
            
            # Save to config for persistence
            if "gpu_overclock" not in self.config:
                self.config["gpu_overclock"] = {}
                
            self.config["gpu_overclock"][str(gpu_idx)] = {
                "core": core_offset,
                "memory": memory_offset,
                "power": power_limit,
                "fan": fan_speed,
                "auto_fan": auto_fan
            }
            
            # Save the config file
            save_cfg(self.config)
            
        except (ValueError, IndexError) as e:
            messagebox.showerror("Error", f"Failed to apply settings: {e}")
    
    def _reset_overclock(self) -> None:
        """Reset overclocking settings to default values."""
        self.core_clock_var.set(0)
        self.memory_clock_var.set(0)
        self.power_limit_var.set(100)
        self.fan_speed_var.set(0)
        self.auto_fan_var.set(True)
        
        self._update_label(self.core_clock_label, "0 MHz")
        self._update_label(self.memory_clock_label, "0 MHz")
        self._update_label(self.power_limit_label, "100%")
        self._toggle_fan_control()
        
        # If a GPU is selected, also remove its saved overclock settings
        selected = self.oc_gpu_var.get()
        if selected and "gpu_overclock" in self.config:
            try:
                gpu_idx = int(selected.split(":")[0].replace("GPU", "").strip())
                if str(gpu_idx) in self.config["gpu_overclock"]:
                    del self.config["gpu_overclock"][str(gpu_idx)]
                    save_cfg(self.config)
            except (ValueError, IndexError):
                pass
    
    def _apply_theme_change(self) -> None:
        """Apply theme change."""
        theme_name = self.theme_var.get()
        ttk_theme = self.ttk_theme_var.get()
        
        # Update config
        self.config["theme"] = theme_name
        if ttk_theme:
            self.config["ttk_theme"] = ttk_theme
            
        # Call the theme change callback
        self.theme_change_callback(theme_name, ttk_theme)
    
    def _save_all_settings(self) -> None:
        """Save all settings to the configuration file."""
        # Update config with current values
        self.config["start_minimized"] = self.start_min_var.get()
        self.config["idle_alerts"] = self.idle_alerts_var.get()
        self.config["idle_threshold"] = self.idle_threshold_var.get()
        self.config["idle_time"] = self.idle_time_var.get()
        
        # Save to file
        try:
            save_cfg(self.config)
            messagebox.showinfo("Settings", "Settings saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}") 