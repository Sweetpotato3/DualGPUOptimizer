"""
Theme management for DualGPUOptimizer
Provides custom theme functionality for the application
"""
import os
import sys
import logging
import tkinter as tk
from tkinter import ttk
from pathlib import Path

logger = logging.getLogger("DualGPUOpt.Theme")

# Define theme colors
THEME_DARK_PURPLE = {
    "bg": "#2D1E40",
    "fg": "#FFFFFF",
    "accent": "#8A54FD",
    "accent_light": "#A883FD",
    "accent_dark": "#6A3EBD",
    "warning": "#FF9800",
    "error": "#F44336",
    "success": "#4CAF50",
    "border": "#3D2A50"
}

# Define fallback theme
THEME_DEFAULT = {
    "bg": "#F0F0F0",
    "fg": "#000000",
    "accent": "#007BFF",
    "accent_light": "#3395FF",
    "accent_dark": "#0062CC",
    "warning": "#FF9800",
    "error": "#F44336",
    "success": "#4CAF50",
    "border": "#CDCDCD"
}

# Current theme
current_theme = THEME_DARK_PURPLE

def get_theme_path():
    """Get the path to theme resources"""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_path = Path(getattr(sys, '_MEIPASS', os.path.dirname(sys.executable)))
    else:
        # Running in a normal Python environment
        base_path = Path(__file__).parent.parent
    
    return base_path / "resources"

def apply_theme(root):
    """Apply the current theme to the application
    
    Args:
        root: The root Tk window
    """
    try:
        # Try to load ttkthemes if available
        try:
            from ttkthemes import ThemedTk
            # If the root is not already a ThemedTk, we can't theme it
            if not isinstance(root, ThemedTk):
                logger.warning("Root window is not a ThemedTk, using custom styling instead")
                apply_custom_styling(root)
            else:
                root.set_theme("equilux")  # Dark theme similar to our purple
                adjust_equilux_colors(root)
        except ImportError:
            logger.info("ttkthemes not available, using custom styling")
            apply_custom_styling(root)
    except Exception as e:
        logger.error(f"Error applying theme: {e}")
        # If anything goes wrong, apply minimal styling
        apply_minimal_styling(root)

def apply_custom_styling(root):
    """Apply custom styling using ttk.Style
    
    Args:
        root: The root Tk window
    """
    style = ttk.Style(root)
    
    # Configure TFrame
    style.configure("TFrame", background=current_theme["bg"])
    
    # Configure TLabel
    style.configure("TLabel", 
                    background=current_theme["bg"], 
                    foreground=current_theme["fg"])
    
    # Configure TButton
    style.configure("TButton", 
                    background=current_theme["accent"],
                    foreground=current_theme["fg"],
                    borderwidth=1,
                    focusthickness=1,
                    focuscolor=current_theme["accent_light"],
                    padding=(10, 5))
    
    style.map("TButton",
               background=[("active", current_theme["accent_light"]),
                          ("disabled", current_theme["bg"])],
               foreground=[("disabled", "#AAAAAA")])
    
    # Configure TEntry
    style.configure("TEntry", 
                    fieldbackground=current_theme["bg"],
                    foreground=current_theme["fg"],
                    bordercolor=current_theme["border"],
                    lightcolor=current_theme["accent_light"],
                    darkcolor=current_theme["accent_dark"])
    
    # Configure TNotebook
    style.configure("TNotebook", 
                    background=current_theme["bg"],
                    borderwidth=0)
    
    style.configure("TNotebook.Tab", 
                    background=current_theme["bg"],
                    foreground=current_theme["fg"],
                    padding=(10, 2),
                    borderwidth=1,
                    bordercolor=current_theme["border"])
    
    style.map("TNotebook.Tab",
              background=[("selected", current_theme["accent"]),
                          ("active", current_theme["accent_light"])],
              foreground=[("selected", "#FFFFFF"),
                          ("active", "#FFFFFF")])
    
    # Root window configuration
    root.configure(background=current_theme["bg"])

def adjust_equilux_colors(root):
    """Adjust equilux theme to match our purple colors
    
    Args:
        root: The root Tk window
    """
    style = ttk.Style(root)
    
    # Adjust accent colors for buttons
    style.configure("TButton", 
                    background=current_theme["accent"])
    
    style.map("TButton",
              background=[("active", current_theme["accent_light"]),
                          ("disabled", "#555555")])
    
    # Adjust selected tab color
    style.map("TNotebook.Tab",
              background=[("selected", current_theme["accent"]),
                          ("active", current_theme["accent_light"])])

def apply_minimal_styling(root):
    """Apply minimal styling in case of failures
    
    Args:
        root: The root Tk window
    """
    style = ttk.Style(root)
    
    # Basic button styling
    style.configure("TButton", padding=(10, 5))
    
    # Basic tab styling
    style.configure("TNotebook.Tab", padding=(10, 2)) 