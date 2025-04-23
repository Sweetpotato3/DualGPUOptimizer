"""
Theme selector component for DualGPUOptimizer
Provides a dropdown for selecting and previewing themes
"""
from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from dualgpuopt.gui.theme import AVAILABLE_THEMES, set_theme
from dualgpuopt.services.event_service import event_bus

try:
    from dualgpuopt.services.config_service import config_service
except ImportError:
    config_service = None

logger = logging.getLogger("DualGPUOpt.ThemeSelector")


class ThemeSelector(ttk.Frame):
    """A theme selection dropdown with previews"""

    def __init__(
        self,
        parent: ttk.Frame,
        label_text: str = "Theme:",
        callback: Optional[Callable[[str], None]] = None,
        padx: int = 8,
        pady: int = 5,
    ) -> None:
        """
        Initialize a theme selector widget

        Args:
        ----
            parent: Parent widget
            label_text: Text for the label
            callback: Optional callback when theme changes
            padx: Horizontal padding
            pady: Vertical padding

        """
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.padx = padx
        self.pady = pady

        # Get current theme from config if available
        current_theme = "dark_purple"
        if config_service:
            current_theme = config_service.get("theme", "dark_purple")

        # Create theme selection widgets
        self.theme_var = tk.StringVar(value=current_theme)
        ttk.Label(self, text=label_text).pack(side="left", padx=padx, pady=pady)

        # Create combobox with theme options
        theme_values = list(AVAILABLE_THEMES.keys())
        self.theme_combo = ttk.Combobox(
            self,
            textvariable=self.theme_var,
            values=theme_values,
            width=12,
            state="readonly",
        )
        self.theme_combo.pack(side="left", padx=padx, pady=pady)

        # Display color preview swatch
        self.preview_canvas = tk.Canvas(self, width=24, height=24, highlightthickness=1)
        self.preview_canvas.pack(side="left", padx=padx, pady=pady)

        # Apply button
        self.apply_button = ttk.Button(
            self,
            text="Apply",
            command=self._apply_theme,
        )
        self.apply_button.pack(side="left", padx=padx, pady=pady)

        # Bind combobox selection to preview update
        self.theme_combo.bind("<<ComboboxSelected>>", self._update_preview)

        # Initialize preview
        self._update_preview()

        # Subscribe to theme change events
        event_bus.subscribe("config_changed:theme", self._handle_external_theme_change)

    def _update_preview(self, event=None) -> None:
        """Update the preview swatch based on selected theme"""
        theme_name = self.theme_var.get()
        theme_colors = AVAILABLE_THEMES.get(theme_name, AVAILABLE_THEMES["dark_purple"])

        # Update preview swatch with theme colors
        self.preview_canvas.delete("all")

        # Draw theme preview with primary, secondary and accent colors
        self.preview_canvas.create_rectangle(
            2,
            2,
            24,
            24,
            fill=theme_colors["bg"],
            outline=theme_colors["border"],
        )
        self.preview_canvas.create_rectangle(
            6,
            6,
            20,
            20,
            fill=theme_colors["secondary_bg"],
            outline="",
        )
        self.preview_canvas.create_rectangle(
            10,
            10,
            14,
            14,
            fill=theme_colors["accent"],
            outline="",
        )

    def _apply_theme(self) -> None:
        """Apply the selected theme"""
        theme_name = self.theme_var.get()

        # Set the theme
        logger.info(f"Applying theme: {theme_name}")
        root_window = self.winfo_toplevel()
        set_theme(root_window, theme_name)

        # Execute callback if provided
        if self.callback:
            self.callback(theme_name)

    def _handle_external_theme_change(self, theme_name) -> None:
        """Handle theme changes from outside this widget"""
        if theme_name != self.theme_var.get():
            self.theme_var.set(theme_name)
            self._update_preview()

    def get_theme(self) -> str:
        """Get the current selected theme"""
        return self.theme_var.get()

    def set_theme(self, theme_name: str) -> None:
        """Set the current selected theme"""
        if theme_name in AVAILABLE_THEMES:
            self.theme_var.set(theme_name)
            self._update_preview()
