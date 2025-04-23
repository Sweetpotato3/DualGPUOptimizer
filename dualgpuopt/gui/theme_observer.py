"""
Theme observer module for ensuring consistent theme propagation
"""
from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable

try:
    from dualgpuopt.services.event_service import event_bus

    HAS_EVENT_BUS = True
except ImportError:
    HAS_EVENT_BUS = False
    print("Warning: event_bus not available, theme observation will be limited")

from dualgpuopt.gui.theme import AVAILABLE_THEMES

logger = logging.getLogger("DualGPUOpt.ThemeObserver")

# Global registry of themed widgets
_themed_widgets: set[tk.Widget] = set()
_themed_callbacks: list[Callable[[str], None]] = []


def register_themed_widget(widget: tk.Widget) -> None:
    """
    Register a widget to be updated when theme changes

    Args:
    ----
        widget: Widget to register
    """
    _themed_widgets.add(widget)
    logger.debug(f"Registered themed widget: {widget}")


def register_theme_callback(callback: Callable[[str], None]) -> None:
    """
    Register a callback to be called when theme changes

    Args:
    ----
        callback: Function to call when theme changes
    """
    if callback not in _themed_callbacks:
        _themed_callbacks.append(callback)
        logger.debug(f"Registered theme callback: {callback}")


def unregister_themed_widget(widget: tk.Widget) -> None:
    """
    Unregister a widget from theme updates

    Args:
    ----
        widget: Widget to unregister
    """
    if widget in _themed_widgets:
        _themed_widgets.remove(widget)
        logger.debug(f"Unregistered themed widget: {widget}")


def unregister_theme_callback(callback: Callable[[str], None]) -> None:
    """
    Unregister a theme change callback

    Args:
    ----
        callback: Function to unregister
    """
    if callback in _themed_callbacks:
        _themed_callbacks.remove(callback)
        logger.debug(f"Unregistered theme callback: {callback}")


def update_themed_widgets(theme_name: str) -> None:
    """
    Update all registered themed widgets

    Args:
    ----
        theme_name: Name of the new theme
    """
    # Remove destroyed widgets
    destroyed = set()
    for widget in _themed_widgets:
        try:
            if not widget.winfo_exists():
                destroyed.add(widget)
        except tk.TclError:
            destroyed.add(widget)

    _themed_widgets.difference_update(destroyed)

    # Update remaining widgets
    for widget in _themed_widgets:
        update_widget_theme(widget, theme_name)

    # Call registered callbacks
    for callback in _themed_callbacks:
        try:
            callback(theme_name)
        except Exception as e:
            logger.error(f"Error in theme callback: {e}")

    logger.info(
        f"Updated {len(_themed_widgets)} widgets and {len(_themed_callbacks)} callbacks for theme: {theme_name}"
    )


def update_widget_theme(widget: tk.Widget, theme_name: str) -> None:
    """
    Update a single widget's theme

    Args:
    ----
        widget: Widget to update
        theme_name: Name of the new theme
    """
    theme_colors = AVAILABLE_THEMES.get(theme_name, AVAILABLE_THEMES["dark_purple"])

    try:
        # Update based on widget type
        if isinstance(widget, ttk.Widget):
            # TTK widgets are handled by the style system
            pass
        elif isinstance(widget, tk.Canvas):
            widget.configure(bg=theme_colors["bg"])
        elif isinstance(widget, (tk.Frame, tk.LabelFrame)):
            widget.configure(bg=theme_colors["bg"])
        elif isinstance(widget, tk.Label):
            widget.configure(bg=theme_colors["bg"], fg=theme_colors["fg"])
        elif isinstance(widget, (tk.Entry, tk.Text)):
            widget.configure(
                bg=theme_colors["input_bg"],
                fg=theme_colors["fg"],
                insertbackground=theme_colors["fg"],
            )
        elif isinstance(widget, tk.Button):
            widget.configure(
                bg=theme_colors["accent"],
                fg=theme_colors["fg"],
                activebackground=theme_colors["accent_light"],
                activeforeground=theme_colors["fg"],
            )
        elif isinstance(widget, (tk.Checkbutton, tk.Radiobutton)):
            widget.configure(
                bg=theme_colors["bg"],
                fg=theme_colors["fg"],
                activebackground=theme_colors["bg"],
                activeforeground=theme_colors["accent"],
                selectcolor=theme_colors["input_bg"],
            )
        elif isinstance(widget, tk.Listbox):
            widget.configure(
                bg=theme_colors["input_bg"],
                fg=theme_colors["fg"],
                selectbackground=theme_colors["accent"],
                selectforeground=theme_colors["fg"],
            )
        elif isinstance(widget, tk.Menu):
            widget.configure(
                bg=theme_colors["bg"],
                fg=theme_colors["fg"],
                activebackground=theme_colors["accent"],
                activeforeground=theme_colors["fg"],
            )
    except tk.TclError as e:
        logger.warning(f"Error updating widget theme: {e}")


class ThemedWidget:
    """Mixin for widgets that need to respond to theme changes"""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the themed widget mixin"""
        # Track if initialized for multiple inheritance
        self._theme_initialized = False

    def setup_theming(self) -> None:
        """Setup theme observation for this widget"""
        if hasattr(self, "_theme_initialized") and self._theme_initialized:
            return

        # Register for theme updates
        register_themed_widget(self)

        # Register for theme change events if event bus available
        if HAS_EVENT_BUS:
            event_bus.subscribe("config_changed:theme", self._handle_theme_change)

        self._theme_initialized = True

    def _handle_theme_change(self, theme_name: str) -> None:
        """
        Handle theme change events

        Args:
        ----
            theme_name: Name of the new theme
        """
        self.apply_theme(theme_name)

    def apply_theme(self, theme_name: str) -> None:
        """
        Apply the theme to this widget

        Args:
        ----
            theme_name: Name of the theme to apply
        """
        # Override in subclasses to apply specific theme styling
        update_widget_theme(self, theme_name)

    def cleanup(self) -> None:
        """Clean up theme observation"""
        unregister_themed_widget(self)
        if HAS_EVENT_BUS:
            event_bus.unsubscribe("config_changed:theme", self._handle_theme_change)


# Initialize theme change event listener
if HAS_EVENT_BUS:

    def _on_theme_changed(theme_name: str) -> None:
        """
        Handle theme change events from event bus

        Args:
        ----
            theme_name: Name of the new theme
        """
        logger.info(f"Theme changed to: {theme_name}")
        update_themed_widgets(theme_name)

    # Subscribe to theme change events
    event_bus.subscribe("config_changed:theme", _on_theme_changed)
