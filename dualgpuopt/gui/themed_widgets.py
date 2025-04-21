"""
Theme-aware custom widgets for DualGPUOptimizer
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, List, Any, Callable, Optional, Union, Tuple

try:
    from dualgpuopt.services.event_service import event_bus
    HAS_EVENT_BUS = True
except ImportError:
    HAS_EVENT_BUS = False
    print("Warning: event_bus not available, themed widgets will have limited functionality")

from dualgpuopt.gui.theme import AVAILABLE_THEMES, current_theme
from dualgpuopt.gui.theme_observer import ThemedWidget, register_themed_widget, unregister_themed_widget

logger = logging.getLogger("DualGPUOpt.ThemedWidgets")

class ThemedFrame(tk.Frame, ThemedWidget):
    """A frame with automatic theme updating"""

    def __init__(self, master=None, **kwargs):
        """Initialize a themed frame

        Args:
            master: Parent widget
            **kwargs: Additional keyword arguments for tk.Frame
        """
        # Set theme-related properties from current theme
        theme_props = self._get_theme_props()
        for prop, value in theme_props.items():
            if prop not in kwargs:
                kwargs[prop] = value

        # Initialize the frame
        tk.Frame.__init__(self, master, **kwargs)
        ThemedWidget.__init__(self)

        # Setup theme observation
        self.setup_theming()

    def _get_theme_props(self) -> Dict[str, Any]:
        """Get theme-related properties for this widget

        Returns:
            Dictionary of properties from current theme
        """
        return {
            "bg": current_theme["bg"],
            "highlightbackground": current_theme["border"],
            "highlightcolor": current_theme["accent"]
        }

    def apply_theme(self, theme_name: str) -> None:
        """Apply theme to this widget

        Args:
            theme_name: Name of the theme to apply
        """
        theme_colors = AVAILABLE_THEMES.get(theme_name, AVAILABLE_THEMES["dark_purple"])

        self.configure(
            bg=theme_colors["bg"],
            highlightbackground=theme_colors["border"],
            highlightcolor=theme_colors["accent"]
        )

    def destroy(self):
        """Clean up before destroying the widget"""
        self.cleanup()
        tk.Frame.destroy(self)

class ThemedLabel(tk.Label, ThemedWidget):
    """A label with automatic theme updating"""

    def __init__(self, master=None, **kwargs):
        """Initialize a themed label

        Args:
            master: Parent widget
            **kwargs: Additional keyword arguments for tk.Label
        """
        # Set theme-related properties from current theme
        theme_props = self._get_theme_props()
        for prop, value in theme_props.items():
            if prop not in kwargs:
                kwargs[prop] = value

        # Initialize the label
        tk.Label.__init__(self, master, **kwargs)
        ThemedWidget.__init__(self)

        # Setup theme observation
        self.setup_theming()

    def _get_theme_props(self) -> Dict[str, Any]:
        """Get theme-related properties for this widget

        Returns:
            Dictionary of properties from current theme
        """
        return {
            "bg": current_theme["bg"],
            "fg": current_theme["fg"],
            "highlightbackground": current_theme["bg"]
        }

    def apply_theme(self, theme_name: str) -> None:
        """Apply theme to this widget

        Args:
            theme_name: Name of the theme to apply
        """
        theme_colors = AVAILABLE_THEMES.get(theme_name, AVAILABLE_THEMES["dark_purple"])

        self.configure(
            bg=theme_colors["bg"],
            fg=theme_colors["fg"],
            highlightbackground=theme_colors["bg"]
        )

    def destroy(self):
        """Clean up before destroying the widget"""
        self.cleanup()
        tk.Label.destroy(self)

class ThemedButton(tk.Button, ThemedWidget):
    """A button with automatic theme updating"""

    def __init__(self, master=None, **kwargs):
        """Initialize a themed button

        Args:
            master: Parent widget
            **kwargs: Additional keyword arguments for tk.Button
        """
        # Set theme-related properties from current theme
        theme_props = self._get_theme_props()
        for prop, value in theme_props.items():
            if prop not in kwargs:
                kwargs[prop] = value

        # Initialize the button
        tk.Button.__init__(self, master, **kwargs)
        ThemedWidget.__init__(self)

        # Setup theme observation
        self.setup_theming()

    def _get_theme_props(self) -> Dict[str, Any]:
        """Get theme-related properties for this widget

        Returns:
            Dictionary of properties from current theme
        """
        return {
            "bg": current_theme["accent"],
            "fg": current_theme["fg"],
            "activebackground": current_theme["accent_light"],
            "activeforeground": current_theme["fg"],
            "highlightbackground": current_theme["border"],
            "relief": tk.FLAT,
            "borderwidth": 1
        }

    def apply_theme(self, theme_name: str) -> None:
        """Apply theme to this widget

        Args:
            theme_name: Name of the theme to apply
        """
        theme_colors = AVAILABLE_THEMES.get(theme_name, AVAILABLE_THEMES["dark_purple"])

        self.configure(
            bg=theme_colors["accent"],
            fg=theme_colors["fg"],
            activebackground=theme_colors["accent_light"],
            activeforeground=theme_colors["fg"],
            highlightbackground=theme_colors["border"]
        )

    def destroy(self):
        """Clean up before destroying the widget"""
        self.cleanup()
        tk.Button.destroy(self)

class ThemedEntry(tk.Entry, ThemedWidget):
    """An entry with automatic theme updating"""

    def __init__(self, master=None, **kwargs):
        """Initialize a themed entry

        Args:
            master: Parent widget
            **kwargs: Additional keyword arguments for tk.Entry
        """
        # Set theme-related properties from current theme
        theme_props = self._get_theme_props()
        for prop, value in theme_props.items():
            if prop not in kwargs:
                kwargs[prop] = value

        # Initialize the entry
        tk.Entry.__init__(self, master, **kwargs)
        ThemedWidget.__init__(self)

        # Setup theme observation
        self.setup_theming()

    def _get_theme_props(self) -> Dict[str, Any]:
        """Get theme-related properties for this widget

        Returns:
            Dictionary of properties from current theme
        """
        return {
            "bg": current_theme["input_bg"],
            "fg": current_theme["fg"],
            "insertbackground": current_theme["fg"],
            "selectbackground": current_theme["accent"],
            "selectforeground": current_theme["fg"],
            "highlightbackground": current_theme["border"],
            "relief": tk.FLAT,
            "borderwidth": 1
        }

    def apply_theme(self, theme_name: str) -> None:
        """Apply theme to this widget

        Args:
            theme_name: Name of the theme to apply
        """
        theme_colors = AVAILABLE_THEMES.get(theme_name, AVAILABLE_THEMES["dark_purple"])

        self.configure(
            bg=theme_colors["input_bg"],
            fg=theme_colors["fg"],
            insertbackground=theme_colors["fg"],
            selectbackground=theme_colors["accent"],
            selectforeground=theme_colors["fg"],
            highlightbackground=theme_colors["border"]
        )

    def destroy(self):
        """Clean up before destroying the widget"""
        self.cleanup()
        tk.Entry.destroy(self)

class ThemedListbox(tk.Listbox, ThemedWidget):
    """A listbox with automatic theme updating"""

    def __init__(self, master=None, **kwargs):
        """Initialize a themed listbox

        Args:
            master: Parent widget
            **kwargs: Additional keyword arguments for tk.Listbox
        """
        # Set theme-related properties from current theme
        theme_props = self._get_theme_props()
        for prop, value in theme_props.items():
            if prop not in kwargs:
                kwargs[prop] = value

        # Initialize the listbox
        tk.Listbox.__init__(self, master, **kwargs)
        ThemedWidget.__init__(self)

        # Setup theme observation
        self.setup_theming()

    def _get_theme_props(self) -> Dict[str, Any]:
        """Get theme-related properties for this widget

        Returns:
            Dictionary of properties from current theme
        """
        return {
            "bg": current_theme["input_bg"],
            "fg": current_theme["fg"],
            "selectbackground": current_theme["accent"],
            "selectforeground": current_theme["fg"],
            "highlightbackground": current_theme["border"],
            "relief": tk.FLAT,
            "borderwidth": 1
        }

    def apply_theme(self, theme_name: str) -> None:
        """Apply theme to this widget

        Args:
            theme_name: Name of the theme to apply
        """
        theme_colors = AVAILABLE_THEMES.get(theme_name, AVAILABLE_THEMES["dark_purple"])

        self.configure(
            bg=theme_colors["input_bg"],
            fg=theme_colors["fg"],
            selectbackground=theme_colors["accent"],
            selectforeground=theme_colors["fg"],
            highlightbackground=theme_colors["border"]
        )

    def destroy(self):
        """Clean up before destroying the widget"""
        self.cleanup()
        tk.Listbox.destroy(self)

class ColorSwatch(ThemedFrame):
    """A color swatch for displaying theme colors"""

    def __init__(self, master=None, color: str = "#000000", width: int = 30, height: int = 30, **kwargs):
        """Initialize a color swatch

        Args:
            master: Parent widget
            color: Color to display
            width: Width of the swatch
            height: Height of the swatch
            **kwargs: Additional keyword arguments for ThemedFrame
        """
        super().__init__(master, width=width, height=height, **kwargs)

        self.color = color
        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=color,
            highlightthickness=1,
            highlightbackground=current_theme["border"]
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Register the canvas for theme updates
        register_themed_widget(self.canvas)

    def set_color(self, color: str) -> None:
        """Set the color of the swatch

        Args:
            color: New color to display
        """
        self.color = color
        self.canvas.configure(bg=color)

    def apply_theme(self, theme_name: str) -> None:
        """Apply theme to this widget

        Args:
            theme_name: Name of the theme to apply
        """
        super().apply_theme(theme_name)
        theme_colors = AVAILABLE_THEMES.get(theme_name, AVAILABLE_THEMES["dark_purple"])

        self.canvas.configure(highlightbackground=theme_colors["border"])

    def destroy(self):
        """Clean up before destroying the widget"""
        unregister_themed_widget(self.canvas)
        super().destroy()