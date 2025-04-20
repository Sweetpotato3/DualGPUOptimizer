"""
Core theme management functionality
"""
import os
import sys
import logging
import tkinter as tk
from tkinter import ttk
from pathlib import Path

from dualgpuopt.gui.theme.colors import current_theme, AVAILABLE_THEMES, update_current_theme
from dualgpuopt.gui.theme.compatibility import apply_theme_with_compatibility
from dualgpuopt.gui.theme.styling import apply_custom_styling

logger = logging.getLogger("DualGPUOpt.Theme.Core")

def get_theme_path():
    """Get the path to theme resources"""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_path = Path(getattr(sys, '_MEIPASS', os.path.dirname(sys.executable)))
    else:
        # Running in a normal Python environment
        base_path = Path(__file__).parent.parent.parent

    return base_path / "resources"

def toggle_theme(root):
    """Toggle between light and dark themes

    Args:
        root: The root Tk window

    Returns:
        The name of the new theme
    """
    # Determine which theme to switch to
    if current_theme == AVAILABLE_THEMES["dark_purple"] or current_theme == AVAILABLE_THEMES["neon_dark"]:
        theme_name = "light"
    else:
        theme_name = "neon_dark"

    # Apply the new theme
    set_theme(root, theme_name)

    logger.info(f"Toggled to {theme_name} theme")
    return theme_name

def set_theme(root, theme_name):
    """Set a specific theme

    Args:
        root: The root Tk window
        theme_name: Name of the theme to set
    Returns:
        The name of the theme that was set
    """
    # Set the theme based on the name
    if theme_name in AVAILABLE_THEMES:
        update_current_theme(theme_name)
    else:
        # Default to dark purple if theme not found
        update_current_theme("dark_purple")
        theme_name = "dark_purple"

    # Apply the theme
    apply_custom_styling(root)

    # Save theme preference to config if available
    try:
        from dualgpuopt.services.config_service import config_service
        config_service.set("theme", theme_name)
        logger.info(f"Saved theme preference: {theme_name}")
    except ImportError:
        logger.warning("Could not save theme preference: config_service not available")

    # Publish theme changed event if event_bus is available
    try:
        from dualgpuopt.services.event_service import event_bus
        event_bus.publish("config_changed:theme", theme_name)
        logger.debug(f"Published theme_changed event for {theme_name}")
    except ImportError:
        logger.debug("Could not publish theme_changed event: event_bus not available")

    logger.info(f"Set theme to {theme_name}")
    return theme_name

def load_theme_from_config(root):
    """Load and apply theme from configuration

    Args:
        root: The root Tk window

    Returns:
        The name of the loaded theme
    """
    try:
        from dualgpuopt.services.config_service import config_service
        theme_name = config_service.get("theme", "dark_purple")
        logger.info(f"Loading theme from config: {theme_name}")
        return set_theme(root, theme_name)
    except ImportError:
        logger.warning("Could not load theme from config: config_service not available")
        return set_theme(root, "dark_purple")  # Default

def apply_theme(root):
    """Apply the current theme to the application

    Args:
        root: The root Tk window
    """
    apply_theme_with_compatibility(root)

# Theme Toggle Button Widget
class ThemeToggleButton(ttk.Button):
    """A button that toggles between light and dark themes"""

    def __init__(self, master, **kwargs):
        """Initialize a theme toggle button

        Args:
            master: Parent widget
            **kwargs: Additional keyword arguments for the button
        """
        # Determine initial icon based on current theme
        is_light = current_theme == AVAILABLE_THEMES["light"]

        # Initialize with theme toggle style
        super().__init__(
            master,
            text="🌙" if is_light else "☀️",
            style="ThemeToggle.TButton",
            command=self._toggle_theme,
            **kwargs
        )

    def _toggle_theme(self):
        """Toggle the theme and update the button text"""
        theme_name = toggle_theme(self.winfo_toplevel())

        # Update button text based on new theme
        new_text = "🌙" if theme_name == "light" else "☀️"
        self.configure(text=new_text)