"""
Theme management for the DualGPUOptimizer GUI.
"""
from __future__ import annotations

import colorsys
import sys
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, List, Optional, Any

# Import ttkthemes for better theme support
try:
    from ttkthemes import ThemedTk, ThemedStyle
    TTKTHEMES_AVAILABLE = True
except ImportError:
    TTKTHEMES_AVAILABLE = False

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

# Modern theme definitions using Material Design palette
THEMES = {
    "dark": {
        "bg": "#263238",  # Material Blue Grey 900
        "text": "#eceff1",  # Material Blue Grey 50
        "chart_bg": "#1a2327", # Darker shade for contrast
        "highlight": "#42a5f5",  # Material Blue 400
        "button": "#37474f",  # Material Blue Grey 800
        "entry": "#37474f",  # Material Blue Grey 800
        "border": "#546e7a",  # Material Blue Grey 600
        "accent": "#64ffda",  # Material Teal A200
        "ttk_theme": "equilux" if TTKTHEMES_AVAILABLE else "clam"
    },
    "light": {
        "bg": "#eceff1",  # Material Blue Grey 50
        "text": "#263238",  # Material Blue Grey 900
        "chart_bg": "#cfd8dc",  # Material Blue Grey 100
        "highlight": "#2196f3",  # Material Blue 500
        "button": "#e0e0e0",  # Material Grey 300
        "entry": "#ffffff",  # White
        "border": "#b0bec5",  # Material Blue Grey 200
        "accent": "#00bfa5",  # Material Teal A700
        "ttk_theme": "arc" if TTKTHEMES_AVAILABLE else "clam"
    },
    "system": {
        # Will use system default theme
        "ttk_theme": None  # Use default
    },
    "green": {
        "bg": "#1b5e20",  # Dark Green
        "text": "#f1f8e9",  # Light Green 50
        "chart_bg": "#143718",  # Darker Green
        "highlight": "#66bb6a",  # Green 400
        "button": "#2e7d32",  # Green 800
        "entry": "#2e7d32",  # Green 800
        "border": "#43a047",  # Green 600
        "accent": "#b9f6ca",  # Green A100
        "ttk_theme": "equilux" if TTKTHEMES_AVAILABLE else "clam"
    },
    "blue": {
        "bg": "#0d47a1",  # Dark Blue
        "text": "#e3f2fd",  # Light Blue 50
        "chart_bg": "#0a3880",  # Darker Blue
        "highlight": "#42a5f5",  # Blue 400
        "button": "#1565c0",  # Blue 800
        "entry": "#1565c0",  # Blue 800
        "border": "#1976d2",  # Blue 700
        "accent": "#80d8ff",  # Light Blue A100
        "ttk_theme": "equilux" if TTKTHEMES_AVAILABLE else "clam"
    }
}

# Available ttk themes from ttkthemes
AVAILABLE_TTK_THEMES = ["arc", "equilux", "adapta", "yaru", "breeze"] if TTKTHEMES_AVAILABLE else []


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


def apply_theme(root: tk.Tk, theme_name: str, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Apply selected theme to the application.

    Args:
        root: The root Tk window
        theme_name: Name of the theme to apply
        logger: Optional logger for error messages

    Returns:
        Dict containing theme properties
    """
    if logger is None:
        logger = logging.getLogger("dualgpuopt.gui.theme")

    # Handle system theme specially
    if theme_name == "system":
        # Just use default theme for the platform
        if sys.platform == "darwin":  # macOS
            ttk_theme = "aqua"
        elif sys.platform == "win32":  # Windows
            ttk_theme = "vista"
        else:  # Linux and others
            ttk_theme = "clam"

        return {"ttk_theme": ttk_theme}
    else:
        # Get theme from our definitions
        theme = THEMES.get(theme_name, THEMES["dark"])
        ttk_theme = theme.get("ttk_theme")

        # Configure colors
        if "bg" in theme:
            root.configure(bg=theme["bg"])

            # Create or get style
            if TTKTHEMES_AVAILABLE and hasattr(root, "set_theme"):
                # For ThemedTk
                if ttk_theme in AVAILABLE_TTK_THEMES:
                    try:
                        root.set_theme(ttk_theme)
                        style = root.style
                    except Exception as e:
                        if logger:
                            logger.warning(f"Failed to set ThemedTk theme: {e}")
                        style = ttk.Style()
                else:
                    style = ttk.Style()
            elif TTKTHEMES_AVAILABLE:
                # For regular Tk with ThemedStyle
                style = ThemedStyle(root)
                if ttk_theme in AVAILABLE_TTK_THEMES:
                    try:
                        style.set_theme(ttk_theme)
                    except Exception as e:
                        if logger:
                            logger.warning(f"Failed to set ThemedStyle theme: {e}")
            else:
                # Regular Style
                style = ttk.Style()

            # Configure style for widgets
            style.configure(".", background=theme["bg"], foreground=theme["text"])
            style.configure("TButton",
                            background=theme["button"],
                            foreground=theme["text"],
                            bordercolor=theme.get("border", theme["button"]))

            style.map("TButton",
                     background=[('active', theme.get("highlight"))],
                     relief=[('pressed', 'sunken')])

            # Configure entry fields
            style.configure("TEntry",
                           fieldbackground=theme["entry"],
                           foreground=theme["text"],
                           bordercolor=theme.get("border", theme["entry"]))

            # Configure other widget types
            style.configure("TFrame", background=theme["bg"])
            style.configure("TLabelframe", background=theme["bg"], foreground=theme["text"])
            style.configure("TLabelframe.Label", background=theme["bg"], foreground=theme["text"])
            style.configure("TLabel", background=theme["bg"], foreground=theme["text"])
            style.configure("TNotebook", background=theme["bg"], tabmargins=[2, 5, 2, 0])
            style.configure("TNotebook.Tab", background=theme["button"],
                           foreground=theme["text"], padding=[10, 2])

            # Map states for notebook tabs
            style.map("TNotebook.Tab",
                     background=[("selected", theme.get("highlight"))],
                     foreground=[("selected", theme["bg"])])

            # Set progressbar colors
            style.configure("Horizontal.TProgressbar",
                           background=theme.get("accent", theme.get("highlight")),
                           troughcolor=theme.get("chart_bg", "#202020"))

            # Set text widget colors via root options
            root.option_add("*Text.Background", theme["entry"])
            root.option_add("*Text.Foreground", theme["text"])
            root.option_add("*Text.selectBackground", theme.get("highlight"))
            root.option_add("*Text.selectForeground", theme.get("bg"))

            # Set combobox colors
            style.map('TCombobox',
                     fieldbackground=[('readonly', theme["entry"])],
                     selectbackground=[('readonly', theme.get("highlight"))])

            # Update notebook styling for better appearance
            notebook_style = ttk.Style()
            notebook_style.layout("TNotebook", [
                ("TNotebook.client", {"sticky": "nswe"})
            ])
            notebook_style.layout("TNotebook.Tab", [
                ("TNotebook.tab", {
                    "sticky": "nswe",
                    "children": [
                        ("TNotebook.padding", {
                            "side": "top",
                            "sticky": "nswe",
                            "children": [
                                ("TNotebook.label", {"side": "top", "sticky": ""})
                            ]
                        })
                    ]
                })
            ])

            # Apply ttk theme if specified
            if ttk_theme and not TTKTHEMES_AVAILABLE:
                try:
                    ttk.Style().theme_use(ttk_theme)
                except tk.TclError:
                    # Fall back to default theme if specified one not available
                    if logger:
                        logger.warning(f"TTK theme {ttk_theme} not available, using default")

            # Apply font for better readability
            default_font = ("Segoe UI", 9) if sys.platform == "win32" else ("Helvetica", 10)
            for widget in ["TLabel", "TButton", "TCheckbutton", "TRadiobutton", "TEntry", "TCombobox"]:
                try:
                    style = ttk.Style()
                    style.configure(widget, font=default_font)
                except tk.TclError as e:
                    if logger:
                        logger.debug(f"Could not set font for {widget}: {e}")

        return theme


def update_widgets_theme(parent: tk.Widget, theme: Dict[str, Any]) -> None:
    """
    Update the theme of existing widgets recursively.

    Args:
        parent: The parent widget
        theme: The theme dictionary with color settings
    """
    if isinstance(parent, (ttk.Frame, ttk.LabelFrame, ttk.Notebook)):
        # Update ttk widgets - these should automatically use the ttk style
        pass
    elif isinstance(parent, tk.Frame):
        # Update tk.Frame background
        parent.configure(bg=theme.get("bg", parent.cget("bg")))
    elif isinstance(parent, tk.Canvas):
        # Update Canvas background
        parent.configure(bg=theme.get("chart_bg", theme.get("bg", parent.cget("bg"))))
    elif isinstance(parent, tk.Text):
        # Update Text widget colors
        parent.configure(
            bg=theme.get("entry", parent.cget("bg")),
            fg=theme.get("text", parent.cget("fg")),
            insertbackground=theme.get("text", parent.cget("insertbackground")),
            selectbackground=theme.get("highlight", parent.cget("selectbackground")),
            selectforeground=theme.get("bg", parent.cget("selectforeground"))
        )

    # Recursively update all children
    for child in parent.winfo_children():
        update_widgets_theme(child, theme)