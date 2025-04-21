"""
Settings tab for the DualGPUOptimizer GUI.
Provides a unified interface for all settings components.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, List, Any, Optional

# Try to import ttkbootstrap components
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    TTKBOOTSTRAP_AVAILABLE = True
except ImportError:
    import tkinter.ttk as ttk
    TTKBOOTSTRAP_AVAILABLE = False

from dualgpuopt.gpu_info import GPU
from dualgpuopt.services.event_service import event_bus
from dualgpuopt.services.config_service import config_service
from dualgpuopt.services.state_service import StateService, state_service
from dualgpuopt.services.error_service import error_service

# Import settings components
from dualgpuopt.gui.settings.appearance import AppearanceFrame
from dualgpuopt.gui.settings.overclocking import OverclockingFrame
from dualgpuopt.gui.settings.application_settings import ApplicationSettingsFrame


class SettingsTab(ttk.Frame):
    """Settings tab that allows configuration of application settings."""

    def __init__(self, parent: ttk.Frame, gpus: Optional[List[GPU]] = None,
                 config_service_instance = None,
                 state_service_instance: Optional[StateService] = None,
                 danger_style: str = "danger") -> None:
        """
        Initialize the settings tab.

        Args:
            parent: Parent frame
            gpus: List of GPU objects
            config_service_instance: Application configuration service
            state_service_instance: State service for loading/saving settings
            danger_style: Style name for danger elements
        """
        # Set default values for services
        if gpus is None:
            gpus = []
        if config_service_instance is None:
            config_service_instance = config_service
        if state_service_instance is None:
            state_service_instance = state_service

        # Define default padding
        self.PAD = 16

        super().__init__(parent, padding=self.PAD)
        self.parent = parent
        self.gpus = gpus
        self.config_service = config_service_instance
        self.state_service = state_service_instance
        self.logger = logging.getLogger("dualgpuopt.gui.settings")

        # Set up grid configuration
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)  # Content area takes all available space
        self.rowconfigure(1, weight=0)  # Footer bar is fixed height

        # Register event handlers
        self._register_event_handlers()

        # Create a scrollable canvas for the content
        self._create_scrollable_content()

        # Create footer with status and action buttons
        self._create_footer()

    def _register_event_handlers(self) -> None:
        """Register event handlers for events."""
        event_bus.subscribe("settings_saved", self._update_status_saved)

    def _update_status_saved(self, *args) -> None:
        """Update status bar to show settings were saved."""
        self.status_var.set("Settings saved successfully")
        # Reset after 3 seconds
        self.after(3000, lambda: self.status_var.set("Ready"))

    def _create_scrollable_content(self) -> None:
        """Create a scrollable frame to contain all settings."""
        canvas_frame = ttk.Frame(self)
        canvas_frame.grid(row=0, column=0, sticky="nsew")
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Make the scrollable frame take the full width
        self.scrollable_frame.columnconfigure(0, weight=1)

        # Add the settings components
        self._add_settings_components()

    def _add_settings_components(self) -> None:
        """Add the settings components to the scrollable frame."""
        # Appearance settings
        self.appearance_frame = AppearanceFrame(
            self.scrollable_frame,
            pad=self.PAD,
            on_theme_change=self._update_status
        )
        self.appearance_frame.grid(row=0, column=0, sticky="ew")

        # GPU Overclocking settings
        self.overclocking_frame = OverclockingFrame(
            self.scrollable_frame,
            self.gpus,
            pad=self.PAD,
            on_status_change=self._update_status
        )
        self.overclocking_frame.grid(row=1, column=0, sticky="ew")

        # Application settings
        self.application_settings_frame = ApplicationSettingsFrame(
            self.scrollable_frame,
            pad=self.PAD,
            on_settings_change=self._update_status
        )
        self.application_settings_frame.grid(row=2, column=0, sticky="ew")

    def _create_footer(self) -> None:
        """Create a sticky footer bar with status and buttons."""
        if TTKBOOTSTRAP_AVAILABLE:
            footer_frame = ttk.Frame(self, bootstyle="secondary")
        else:
            footer_frame = ttk.Frame(self, style="Secondary.TFrame")
        footer_frame.grid(row=1, column=0, sticky="ew", pady=(self.PAD/2, 0))
        footer_frame.columnconfigure(0, weight=1)  # Status text expands
        footer_frame.columnconfigure(1, weight=0)  # Buttons fixed width

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(footer_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=0, sticky="w", padx=self.PAD, pady=self.PAD/2)

        # Buttons frame
        buttons_frame = ttk.Frame(footer_frame)
        buttons_frame.grid(row=0, column=1, sticky="e", padx=self.PAD, pady=self.PAD/2)

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

    def _update_status(self, message: str) -> None:
        """
        Update the status message.

        Args:
            message: Status message to display
        """
        self.status_var.set(message)
        # Reset after 3 seconds
        self.after(3000, lambda: self.status_var.set("Ready"))

    def _reset_all_settings(self) -> None:
        """Reset all settings to defaults."""
        if messagebox.askyesno("Reset Settings",
                             "Are you sure you want to reset all settings to defaults?",
                             parent=self.winfo_toplevel()):
            # Reset application settings
            self.application_settings_frame.apply_settings({
                "start_minimized": False,
                "idle_alerts": True,
                "idle_threshold": 30,
                "idle_time": 5
            })

            # Apply default theme
            root_window = self.winfo_toplevel()
            from dualgpuopt.gui.theme import set_theme
            set_theme(root_window, "dark_purple")

            # Save changes
            self._save_all_settings()

            # Update status
            self._update_status("All settings reset to defaults")

    def _save_all_settings(self) -> None:
        """Save all settings to the configuration file."""
        try:
            # Get settings from each component
            app_settings = self.application_settings_frame.get_settings()
            theme_settings = {
                "theme": self.appearance_frame.get_theme(),
                "ttk_theme": self.appearance_frame.get_ttk_theme()
            }

            # Update config with current values
            config_dict = {**app_settings, **theme_settings}
            self.config_service.update(config_dict)

            # Update status
            self._update_status("Settings saved successfully")

            # Notify about settings update
            event_bus.publish("settings_saved")

            messagebox.showinfo("Settings", "Settings saved successfully",
                              parent=self.winfo_toplevel())
        except Exception as e:
            error_service.handle_error(e, level="ERROR", title="Settings Error",
                                     context={"operation": "save_settings"})
