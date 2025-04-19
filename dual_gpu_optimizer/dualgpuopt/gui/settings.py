"""
Settings tab for the DualGPUOptimizer GUI.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import pathlib
import logging
from typing import Dict, List, Callable, Any, Optional

# Try to import ttkbootstrap components
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    TTKBOOTSTRAP_AVAILABLE = True
except ImportError:
    import tkinter.ttk as ttk
    TTKBOOTSTRAP_AVAILABLE = False

from dualgpuopt.gui.app import PAD
from dualgpuopt.gpu_info import GPU
from dualgpuopt.services.event_service import event_bus
from dualgpuopt.services.config_service import config_service
from dualgpuopt.services.error_service import error_service
from dualgpuopt.gui.theme import THEMES, AVAILABLE_TTK_THEMES
from dualgpuopt.commands.command_base import command_manager
from dualgpuopt.commands.gpu_commands import ApplyOverclockCommand


class SettingsTab(ttk.Frame):
    """Settings tab that allows configuration of application settings."""
    
    def __init__(self, parent: ttk.Frame, gpus: List[GPU], config_service) -> None:
        """
        Initialize the settings tab.
        
        Args:
            parent: Parent frame
            gpus: List of GPU objects
            config_service: Application configuration service
        """
        super().__init__(parent, padding=PAD)
        self.parent = parent
        self.gpus = gpus
        self.config_service = config_service
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)  # Content area takes all available space
        self.rowconfigure(1, weight=0)  # Footer bar is fixed height
        self.logger = logging.getLogger("dualgpuopt.gui.settings")
        
        # Register event handlers
        self._register_event_handlers()
        
        # Create a scrollable canvas to contain all settings
        canvas_frame = ttk.Frame(self)
        canvas_frame.grid(row=0, column=0, sticky="nsew")
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        
        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Make the scrollable frame take the full width
        scrollable_frame.columnconfigure(0, weight=1)
        
        # ------ Appearance Section ------
        appearance_frame = ttk.LabelFrame(scrollable_frame, text="Appearance")
        appearance_frame.grid(sticky="ew", pady=(0, PAD), padx=PAD, row=0)
        appearance_frame.columnconfigure(1, weight=1)
        
        # Theme selection
        self.theme_var = tk.StringVar(value=config_service.get("theme", "dark"))
        ttk.Label(appearance_frame, text="Color Theme:").grid(row=0, column=0, sticky="w", padx=PAD, pady=5)
        theme_combo = ttk.Combobox(
            appearance_frame, 
            textvariable=self.theme_var,
            values=list(THEMES.keys()),
            width=10,
            state="readonly"
        )
        theme_combo.grid(row=0, column=1, sticky="w", padx=PAD, pady=5)
        
        # Add TTK theme selection if ttkthemes is available
        self.ttk_theme_var = tk.StringVar(value=config_service.get("ttk_theme", ""))
        if AVAILABLE_TTK_THEMES:
            ttk.Label(appearance_frame, text="Widget Style:").grid(row=1, column=0, sticky="w", padx=PAD, pady=5)
            ttk_theme_combo = ttk.Combobox(
                appearance_frame,
                textvariable=self.ttk_theme_var,
                values=AVAILABLE_TTK_THEMES,
                width=10,
                state="readonly"
            )
            ttk_theme_combo.grid(row=1, column=1, sticky="w", padx=PAD, pady=5)
        
        ttk.Button(
            appearance_frame, 
            text="Apply Theme", 
            command=self._apply_theme_change
        ).grid(row=0, column=2, padx=PAD, pady=5)
        
        # ------ GPU Overclocking Section ------
        overclocking_frame = ttk.LabelFrame(scrollable_frame, text="GPU Overclocking")
        overclocking_frame.grid(sticky="ew", pady=(0, PAD), padx=PAD, row=1)
        overclocking_frame.columnconfigure(1, weight=1)
        
        # Create danger zone styling for overclocking section
        if TTKBOOTSTRAP_AVAILABLE:
            overclocking_frame.configure(bootstyle="danger")
        else:
            # Apply custom styling for non-ttkbootstrap
            style = ttk.Style()
            style.configure("Danger.TLabelframe", bordercolor="#c0392b", borderwidth=2)
            style.configure("Danger.TLabelframe.Label", foreground="#c0392b")
            overclocking_frame.configure(style="Danger.TLabelframe")
        
        # GPU selection for overclocking
        ttk.Label(overclocking_frame, text="GPU:").grid(row=0, column=0, sticky="w", padx=PAD, pady=5)
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
        self.oc_gpu_combo.grid(row=0, column=1, sticky="w", padx=PAD, pady=5)
        self.oc_gpu_combo.bind("<<ComboboxSelected>>", self._update_oc_controls)
        
        # Create overclocking sliders frame
        oc_sliders_frame = ttk.Frame(overclocking_frame)
        oc_sliders_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=PAD, pady=5)
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
        
        # Auto fan checkbox or Switch (if ttkbootstrap available)
        self.auto_fan_var = tk.BooleanVar(value=True)
        if TTKBOOTSTRAP_AVAILABLE:
            from ttkbootstrap.widgets import ToggleButton
            auto_fan_check = ToggleButton(
                oc_sliders_frame,
                text="Auto Fan",
                variable=self.auto_fan_var,
                onvalue=True,
                offvalue=False,
                bootstyle="success",
                command=self._toggle_fan_control
            )
        else:
            auto_fan_check = ttk.Checkbutton(
                oc_sliders_frame,
                text="Auto Fan",
                variable=self.auto_fan_var,
                command=self._toggle_fan_control
            )
        auto_fan_check.grid(row=3, column=3, padx=5, pady=2)
        
        # Overclocking buttons
        oc_buttons_frame = ttk.Frame(overclocking_frame)
        oc_buttons_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=PAD, pady=5)
        
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
        
        ttk.Button(
            oc_buttons_frame,
            text="Undo",
            command=self._undo_last_command,
            state="disabled"  # Will be enabled when commands are available
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Note about overclocking
        warning_frame = ttk.Frame(overclocking_frame)
        warning_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=PAD, pady=5)
        
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
        app_settings_frame.grid(sticky="ew", pady=(0, PAD), padx=PAD, row=2)
        app_settings_frame.columnconfigure(1, weight=1)
        
        # GPU idle detection settings frame
        idle_settings_frame = ttk.Frame(app_settings_frame)
        idle_settings_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=PAD, pady=5)
        idle_settings_frame.columnconfigure(1, weight=1)
        
        # Startup behavior
        ttk.Label(idle_settings_frame, text="Start minimized:").grid(row=0, column=0, sticky="w", padx=PAD, pady=5)
        self.start_min_var = tk.BooleanVar(value=config_service.get("start_minimized", False))
        
        # Use Switch if ttkbootstrap available, otherwise checkbox
        if TTKBOOTSTRAP_AVAILABLE:
            from ttkbootstrap.widgets import Switch
            start_min_check = Switch(
                idle_settings_frame,
                variable=self.start_min_var,
                bootstyle="success"
            )
        else:
            start_min_check = ttk.Checkbutton(
                idle_settings_frame,
                variable=self.start_min_var
            )
        start_min_check.grid(row=0, column=1, sticky="w", padx=PAD, pady=5)
        
        # GPU idle detection
        ttk.Label(idle_settings_frame, text="Enable GPU idle alerts:").grid(row=1, column=0, sticky="w", padx=PAD, pady=5)
        self.idle_alerts_var = tk.BooleanVar(value=config_service.get("idle_alerts", True))
        
        # Use Switch if ttkbootstrap available, otherwise checkbox
        if TTKBOOTSTRAP_AVAILABLE:
            idle_alerts_check = Switch(
                idle_settings_frame,
                variable=self.idle_alerts_var,
                bootstyle="success"
            )
        else:
            idle_alerts_check = ttk.Checkbutton(
                idle_settings_frame,
                variable=self.idle_alerts_var
            )
        idle_alerts_check.grid(row=1, column=1, sticky="w", padx=PAD, pady=5)
        
        # Idle threshold
        ttk.Label(idle_settings_frame, text="Idle threshold (%):").grid(row=2, column=0, sticky="w", padx=PAD, pady=5)
        self.idle_threshold_var = tk.IntVar(value=config_service.get("idle_threshold", 30))
        idle_threshold_entry = ttk.Entry(
            idle_settings_frame,
            textvariable=self.idle_threshold_var,
            width=5
        )
        idle_threshold_entry.grid(row=2, column=1, sticky="w", padx=PAD, pady=5)
        
        # Idle time
        ttk.Label(idle_settings_frame, text="Idle time (minutes):").grid(row=3, column=0, sticky="w", padx=PAD, pady=5)
        self.idle_time_var = tk.IntVar(value=config_service.get("idle_time", 5))
        idle_time_entry = ttk.Entry(
            idle_settings_frame,
            textvariable=self.idle_time_var,
            width=5
        )
        idle_time_entry.grid(row=3, column=1, sticky="w", padx=PAD, pady=5)
        
        # Initialize the fan control state
        self._toggle_fan_control()
        
        # Reference to undo button
        self.undo_button = oc_buttons_frame.winfo_children()[2]
        
        # ------ Sticky Footer Bar ------
        if TTKBOOTSTRAP_AVAILABLE:
            footer_frame = ttk.Frame(self, bootstyle="secondary")
        else:
            footer_frame = ttk.Frame(self, style="Secondary.TFrame")
        footer_frame.grid(row=1, column=0, sticky="ew", pady=(PAD/2, 0))
        footer_frame.columnconfigure(0, weight=1)  # Status text expands
        footer_frame.columnconfigure(1, weight=0)  # Buttons fixed width
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(footer_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=0, sticky="w", padx=PAD, pady=PAD/2)
        
        # Buttons frame
        buttons_frame = ttk.Frame(footer_frame)
        buttons_frame.grid(row=0, column=1, sticky="e", padx=PAD, pady=PAD/2)
        
        # Save button
        ttk.Button(
            buttons_frame,
            text="Save Settings",
            command=self._save_all_settings
        ).pack(side="right", padx=5)
        
        # Reset button
        ttk.Button(
            buttons_frame,
            text="Reset to Defaults",
            command=self._reset_all_settings
        ).pack(side="right", padx=5)
    
    def _register_event_handlers(self) -> None:
        """Register event handlers for events."""
        event_bus.subscribe("command_history_updated", self._update_command_history)
        event_bus.subscribe("command_executed:apply_overclock", self._handle_overclock_result)
        event_bus.subscribe("settings_saved", self._update_status_saved)
    
    def _update_status_saved(self, *args) -> None:
        """Update status bar to show settings were saved."""
        self.status_var.set("Settings saved successfully")
        # Reset after 3 seconds
        self.after(3000, lambda: self.status_var.set("Ready"))
    
    def _update_command_history(self, data: Dict[str, Any]) -> None:
        """
        Update the command history UI.
        
        Args:
            data: Command history data
        """
        # Enable/disable the undo button based on history
        can_undo = data.get("can_undo", False)
        self.undo_button["state"] = "normal" if can_undo else "disabled"
    
    def _handle_overclock_result(self, data: Dict[str, Any]) -> None:
        """
        Handle the result of an overclock command.
        
        Args:
            data: Overclock result data
        """
        success = data.get("success", False)
        
        if success:
            self.status_var.set(f"Overclock applied to GPU {data.get('gpu_index', '?')}")
            # Reset status after 3 seconds
            self.after(3000, lambda: self.status_var.set("Ready"))
            
            messagebox.showinfo(
                "Overclock Applied", 
                f"Overclocking settings applied to GPU {data.get('gpu_index', '?')}",
                parent=self.winfo_toplevel()
            )
    
    def _undo_last_command(self) -> None:
        """Undo the last command."""
        result = command_manager.undo()
        if result:
            self.status_var.set("Last operation undone")
            # Reset status after 3 seconds
            self.after(3000, lambda: self.status_var.set("Ready"))
        else:
            messagebox.showerror(
                "Undo Failed", 
                "Failed to undo the last operation",
                parent=self.winfo_toplevel()
            )
    
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
            
            # Get saved overclock settings for this GPU from config
            gpu_oc = self.config_service.get("gpu_overclock", {}).get(str(gpu_idx), {})
            
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
            
            # Update status
            self.status_var.set(f"Loaded settings for GPU {gpu_idx}")
            # Reset status after 3 seconds
            self.after(3000, lambda: self.status_var.set("Ready"))
            
        except (ValueError, IndexError) as e:
            error_service.handle_error(e, level="WARNING", title="GPU Selection Error",
                                     show_dialog=False,
                                     context={"operation": "update_oc_controls", "selection": selected})
    
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
            
            # Create overclocking command
            command = ApplyOverclockCommand(
                gpu_idx, core_offset, memory_offset, power_limit, fan_speed, auto_fan
            )
            
            # Update status
            self.status_var.set(f"Applying overclock to GPU {gpu_idx}...")
            
            # Execute command
            command_manager.execute(command)
            
        except (ValueError, IndexError) as e:
            error_service.handle_error(e, level="ERROR", title="Overclock Error",
                                    context={"operation": "apply_overclock"})
    
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
        if selected and "gpu_overclock" in self.config_service.config:
            try:
                gpu_idx = int(selected.split(":")[0].replace("GPU", "").strip())
                if str(gpu_idx) in self.config_service.config["gpu_overclock"]:
                    del self.config_service.config["gpu_overclock"][str(gpu_idx)]
                    self.config_service.save()
                    
                    # Publish event that GPU overclock was reset
                    event_bus.publish("gpu_overclock_reset", {"gpu_index": gpu_idx})
                    
                    # Update status
                    self.status_var.set(f"Reset overclock for GPU {gpu_idx}")
                    # Reset status after 3 seconds
                    self.after(3000, lambda: self.status_var.set("Ready"))
            except (ValueError, IndexError) as e:
                error_service.handle_error(e, level="WARNING", title="Reset Error",
                                        show_dialog=False,
                                        context={"operation": "reset_overclock"})
    
    def _apply_theme_change(self) -> None:
        """Apply theme change."""
        theme_name = self.theme_var.get()
        ttk_theme = self.ttk_theme_var.get()
        
        # Update config
        self.config_service.update({
            "theme": theme_name,
            "ttk_theme": ttk_theme
        })
        
        # Update status
        self.status_var.set(f"Theme changed to {theme_name}")
        # Reset status after 3 seconds
        self.after(3000, lambda: self.status_var.set("Ready"))
        
        # Notify about theme change
        event_bus.publish("config_changed:theme", theme_name)
    
    def _reset_all_settings(self) -> None:
        """Reset all settings to defaults."""
        if messagebox.askyesno("Reset Settings", 
                             "Are you sure you want to reset all settings to defaults?",
                             parent=self.winfo_toplevel()):
            # Reset to defaults
            self.start_min_var.set(False)
            self.idle_alerts_var.set(True)
            self.idle_threshold_var.set(30)
            self.idle_time_var.set(5)
            
            # Apply default theme
            self.theme_var.set("dark")
            self.ttk_theme_var.set("")
            
            # Save changes
            self._save_all_settings()
            
            # Update status
            self.status_var.set("All settings reset to defaults")
            # Reset status after 3 seconds
            self.after(3000, lambda: self.status_var.set("Ready"))
    
    def _save_all_settings(self) -> None:
        """Save all settings to the configuration file."""
        try:
            # Update config with current values
            self.config_service.update({
                "start_minimized": self.start_min_var.get(),
                "idle_alerts": self.idle_alerts_var.get(),
                "idle_threshold": self.idle_threshold_var.get(),
                "idle_time": self.idle_time_var.get(),
                "theme": self.theme_var.get(),
                "ttk_theme": self.ttk_theme_var.get()
            })
            
            # Update status
            self.status_var.set("Settings saved successfully")
            # Reset status after 3 seconds
            self.after(3000, lambda: self.status_var.set("Ready"))
            
            # Notify about settings update
            event_bus.publish("settings_saved")
            
            messagebox.showinfo("Settings", "Settings saved successfully",
                              parent=self.winfo_toplevel())
        except Exception as e:
            error_service.handle_error(e, level="ERROR", title="Settings Error",
                                     context={"operation": "save_settings"}) 