"""
Appearance settings component for the DualGPUOptimizer.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Callable, Dict, Any, Optional

# Try to import ttkbootstrap components
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    TTKBOOTSTRAP_AVAILABLE = True
except ImportError:
    import tkinter.ttk as ttk
    TTKBOOTSTRAP_AVAILABLE = False

from dualgpuopt.services.event_service import event_bus
from dualgpuopt.services.config_service import config_service
from dualgpuopt.gui.theme import THEMES, AVAILABLE_TTK_THEMES, AVAILABLE_THEMES
from dualgpuopt.gui.theme_selector import ThemeSelector


class AppearanceFrame(ttk.LabelFrame):
    """Frame containing appearance settings."""

    def __init__(self, parent: ttk.Frame, pad: int = 16, on_theme_change: Optional[Callable[[str], None]] = None) -> None:
        """
        Initialize the appearance settings frame.

        Args:
            parent: Parent frame
            pad: Padding value
            on_theme_change: Callback function when theme is changed
        """
        super().__init__(parent, text="Appearance")
        self.parent = parent
        self.pad = pad
        self.on_theme_change = on_theme_change
        self.logger = logging.getLogger("dualgpuopt.gui.settings.appearance")

        self.grid(sticky="ew", pady=(0, self.pad), padx=self.pad)
        self.columnconfigure(0, weight=1)

        self._create_theme_settings()

    def _create_theme_settings(self) -> None:
        """Create theme settings controls."""
        theme_settings_frame = ttk.Frame(self)
        theme_settings_frame.grid(row=0, column=0, sticky="ew", padx=self.pad, pady=5)
        theme_settings_frame.columnconfigure(0, weight=1)

        # Use the ThemeSelector component
        self.theme_selector = ThemeSelector(
            theme_settings_frame,
            label_text="Color Theme:",
            callback=self._on_theme_applied,
            padx=self.pad,
            pady=5
        )
        self.theme_selector.grid(row=0, column=0, sticky="w", pady=5)

        # Add TTK theme selection if ttkthemes is available
        if AVAILABLE_TTK_THEMES:
            self.ttk_theme_var = tk.StringVar(value=config_service.get("ttk_theme", ""))
            ttk_theme_frame = ttk.Frame(self)
            ttk_theme_frame.grid(row=1, column=0, sticky="ew", padx=self.pad, pady=5)

            ttk.Label(ttk_theme_frame, text="Widget Style:").pack(side="left", padx=self.pad, pady=5)
            ttk_theme_combo = ttk.Combobox(
                ttk_theme_frame,
                textvariable=self.ttk_theme_var,
                values=AVAILABLE_TTK_THEMES,
                width=12,
                state="readonly"
            )
            ttk_theme_combo.pack(side="left", padx=self.pad, pady=5)

            ttk.Button(
                ttk_theme_frame,
                text="Apply",
                command=self._apply_ttk_theme
            ).pack(side="left", padx=self.pad, pady=5)

        # Theme previews section
        preview_frame = ttk.Frame(self)
        preview_frame.grid(row=2, column=0, sticky="ew", padx=self.pad, pady=5)
        preview_frame.columnconfigure(0, weight=1)

        # Add theme preview thumbnails
        ttk.Label(preview_frame, text="Available Themes:").grid(row=0, column=0, sticky="w", pady=(10, 5))

        # Create preview grid
        preview_grid = ttk.Frame(preview_frame)
        preview_grid.grid(row=1, column=0, sticky="ew", pady=5)

        # Create a preview tile for each theme
        for i, (theme_name, theme_colors) in enumerate(AVAILABLE_THEMES.items()):
            preview_tile = self._create_theme_preview(preview_grid, theme_name, theme_colors)
            col = i % 3
            row = i // 3
            preview_tile.grid(row=row, column=col, padx=10, pady=10)

    def _create_theme_preview(self, parent, theme_name, theme_colors):
        """
        Create a preview tile for a theme

        Args:
            parent: Parent widget
            theme_name: Name of the theme
            theme_colors: Theme color definitions

        Returns:
            Frame containing the preview
        """
        frame = ttk.Frame(parent)

        # Create the preview canvas
        canvas = tk.Canvas(frame, width=80, height=60, highlightthickness=1, highlightbackground=theme_colors["border"])
        canvas.pack(pady=5)

        # Draw theme preview with primary, secondary and accent colors
        canvas.create_rectangle(0, 0, 80, 60, fill=theme_colors["bg"], outline="")
        canvas.create_rectangle(10, 10, 70, 50, fill=theme_colors["secondary_bg"], outline="")
        canvas.create_rectangle(30, 25, 50, 35, fill=theme_colors["accent"], outline="")

        # Add theme name label
        ttk.Label(frame, text=theme_name).pack()

        # Add click handler to apply this theme
        canvas.bind("<Button-1>", lambda e, name=theme_name: self._apply_theme_from_preview(name))

        return frame

    def _apply_theme_from_preview(self, theme_name: str) -> None:
        """
        Apply a theme from a preview tile click

        Args:
            theme_name: Name of the theme to apply
        """
        # Update theme selector
        self.theme_selector.set_theme(theme_name)

        # Apply the theme
        root_window = self.winfo_toplevel()
        from dualgpuopt.gui.theme import set_theme
        set_theme(root_window, theme_name)

        # Call the theme change callback if provided
        if self.on_theme_change:
            self.on_theme_change(f"Theme changed to {theme_name}")

    def _on_theme_applied(self, theme_name: str) -> None:
        """
        Callback when theme is applied through the selector

        Args:
            theme_name: Name of the applied theme
        """
        # Call the theme change callback if provided
        if self.on_theme_change:
            self.on_theme_change(f"Theme changed to {theme_name}")

    def _apply_ttk_theme(self) -> None:
        """Apply the selected TTK theme"""
        ttk_theme = self.ttk_theme_var.get()

        # Update config
        config_service.set("ttk_theme", ttk_theme)

        # Notify about theme change
        event_bus.publish("config_changed:ttk_theme", ttk_theme)

        # Show message that restart is required
        messagebox.showinfo("Theme Changed",
                          "TTK theme will be applied on next application restart",
                          parent=self.winfo_toplevel())

        # Call the theme change callback if provided
        if self.on_theme_change:
            self.on_theme_change("TTK theme will apply on restart")

    def get_theme(self) -> str:
        """
        Get the currently selected theme.

        Returns:
            Name of the current theme
        """
        return self.theme_selector.get_theme()

    def get_ttk_theme(self) -> str:
        """
        Get the currently selected TTK theme.

        Returns:
            Name of the current TTK theme or empty string if not available
        """
        if hasattr(self, 'ttk_theme_var'):
            return self.ttk_theme_var.get()
        return ""
