"""
Application settings component for the DualGPUOptimizer.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import logging
from typing import Callable, Optional

# Try to import ttkbootstrap components
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    TTKBOOTSTRAP_AVAILABLE = True
except ImportError:
    import tkinter.ttk as ttk
    TTKBOOTSTRAP_AVAILABLE = False

from dualgpuopt.services.config_service import config_service


class ApplicationSettingsFrame(ttk.LabelFrame):
    """Frame containing application settings."""
    
    def __init__(self, parent: ttk.Frame, pad: int = 16, 
                 on_settings_change: Optional[Callable[[str], None]] = None) -> None:
        """
        Initialize the application settings frame.
        
        Args:
            parent: Parent frame
            pad: Padding value
            on_settings_change: Callback for settings changes
        """
        super().__init__(parent, text="Application Settings")
        self.parent = parent
        self.pad = pad
        self.on_settings_change = on_settings_change
        self.logger = logging.getLogger("dualgpuopt.gui.settings.application")
        
        self.grid(sticky="ew", pady=(0, self.pad), padx=self.pad)
        self.columnconfigure(1, weight=1)
        
        self._create_idle_settings()
        
    def _create_idle_settings(self) -> None:
        """Create idle detection settings controls."""
        idle_settings_frame = ttk.Frame(self)
        idle_settings_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=self.pad, pady=5)
        idle_settings_frame.columnconfigure(1, weight=1)
        
        # Startup behavior
        ttk.Label(idle_settings_frame, text="Start minimized:").grid(
            row=0, column=0, sticky="w", padx=self.pad, pady=5
        )
        self.start_min_var = tk.BooleanVar(value=config_service.get("start_minimized", False))
        
        # Use a standard checkbutton
        start_min_check = ttk.Checkbutton(
            idle_settings_frame,
            variable=self.start_min_var,
            style="success.TCheckbutton" if TTKBOOTSTRAP_AVAILABLE else ""
        )
        start_min_check.grid(row=0, column=1, sticky="w", padx=self.pad, pady=5)
        
        # GPU idle detection
        ttk.Label(idle_settings_frame, text="Enable GPU idle alerts:").grid(
            row=1, column=0, sticky="w", padx=self.pad, pady=5
        )
        self.idle_alerts_var = tk.BooleanVar(value=config_service.get("idle_alerts", True))
        
        # Use a standard checkbutton
        idle_alerts_check = ttk.Checkbutton(
            idle_settings_frame,
            variable=self.idle_alerts_var,
            style="success.TCheckbutton" if TTKBOOTSTRAP_AVAILABLE else ""
        )
        idle_alerts_check.grid(row=1, column=1, sticky="w", padx=self.pad, pady=5)
        
        # Idle threshold
        ttk.Label(idle_settings_frame, text="Idle threshold (%):").grid(
            row=2, column=0, sticky="w", padx=self.pad, pady=5
        )
        self.idle_threshold_var = tk.IntVar(value=config_service.get("idle_threshold", 30))
        idle_threshold_entry = ttk.Entry(
            idle_settings_frame,
            textvariable=self.idle_threshold_var,
            width=5
        )
        idle_threshold_entry.grid(row=2, column=1, sticky="w", padx=self.pad, pady=5)
        
        # Idle time
        ttk.Label(idle_settings_frame, text="Idle time (minutes):").grid(
            row=3, column=0, sticky="w", padx=self.pad, pady=5
        )
        self.idle_time_var = tk.IntVar(value=config_service.get("idle_time", 5))
        idle_time_entry = ttk.Entry(
            idle_settings_frame,
            textvariable=self.idle_time_var,
            width=5
        )
        idle_time_entry.grid(row=3, column=1, sticky="w", padx=self.pad, pady=5)
        
    def get_settings(self) -> dict:
        """
        Get current application settings.
        
        Returns:
            Dictionary with current settings
        """
        return {
            "start_minimized": self.start_min_var.get(),
            "idle_alerts": self.idle_alerts_var.get(),
            "idle_threshold": self.idle_threshold_var.get(),
            "idle_time": self.idle_time_var.get()
        }
        
    def apply_settings(self, settings: dict) -> None:
        """
        Apply settings from dictionary.
        
        Args:
            settings: Dictionary with settings to apply
        """
        if "start_minimized" in settings:
            self.start_min_var.set(settings["start_minimized"])
            
        if "idle_alerts" in settings:
            self.idle_alerts_var.set(settings["idle_alerts"])
            
        if "idle_threshold" in settings:
            self.idle_threshold_var.set(settings["idle_threshold"])
            
        if "idle_time" in settings:
            self.idle_time_var.set(settings["idle_time"])
            
        # Notify that settings were changed
        if self.on_settings_change:
            self.on_settings_change("Application settings updated")
