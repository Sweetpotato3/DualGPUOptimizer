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
    "border": "#3D2A50",
    "input_bg": "#241934",
    "secondary_bg": "#372952"
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
    "border": "#CDCDCD",
    "input_bg": "#FFFFFF",
    "secondary_bg": "#E8E8E8"
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

def fix_dpi_scaling(root):
    """Fix DPI scaling issues with Windows
    
    Args:
        root: The root Tk window
    """
    try:
        # Try to set DPI awareness programmatically
        if sys.platform == 'win32':
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)  # Process_System_DPI_Aware
            except Exception:
                pass  # Ignore if it fails

        # Force a specific scaling factor if needed
        root.tk.call('tk', 'scaling', 1.0)
        
        logger.info("Applied DPI scaling fixes")
    except Exception as e:
        logger.warning(f"Failed to fix DPI scaling: {e}")

def apply_theme(root):
    """Apply the current theme to the application
    
    Args:
        root: The root Tk window
    """
    try:
        # Fix DPI scaling first
        fix_dpi_scaling(root)
        
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
    
    # Configure inner frames in tabs differently
    style.configure("Inner.TFrame", background=current_theme["secondary_bg"])
    
    # Configure TLabel
    style.configure("TLabel", 
                    background=current_theme["bg"], 
                    foreground=current_theme["fg"])
    
    # Configure inner labels to match inner frames
    style.configure("Inner.TLabel", 
                    background=current_theme["secondary_bg"],
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
                    fieldbackground=current_theme["input_bg"],
                    foreground=current_theme["fg"],
                    bordercolor=current_theme["border"],
                    lightcolor=current_theme["accent_light"],
                    darkcolor=current_theme["accent_dark"],
                    insertcolor=current_theme["accent_light"])  # Text cursor color
    
    # Configure TCombobox - includes dropdown
    style.configure("TCombobox",
                    fieldbackground=current_theme["input_bg"],
                    background=current_theme["bg"],
                    foreground=current_theme["fg"],
                    arrowcolor=current_theme["fg"],
                    bordercolor=current_theme["border"])
    
    style.map("TCombobox",
              fieldbackground=[("readonly", current_theme["input_bg"])],
              selectbackground=[("readonly", current_theme["accent"])],
              selectforeground=[("readonly", current_theme["fg"])])
    
    # Configure option menu
    root.option_add("*TCombobox*Listbox*Background", current_theme["input_bg"])
    root.option_add("*TCombobox*Listbox*Foreground", current_theme["fg"])
    root.option_add("*TCombobox*Listbox*selectBackground", current_theme["accent"])
    root.option_add("*TCombobox*Listbox*selectForeground", current_theme["fg"])
    
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
    
    # Configure TCheckbutton
    style.configure("TCheckbutton", 
                    background=current_theme["bg"],
                    foreground=current_theme["fg"],
                    indicatorcolor=current_theme["input_bg"],
                    indicatorbackground=current_theme["input_bg"])
    
    style.map("TCheckbutton",
              indicatorcolor=[("selected", current_theme["accent"])],
              background=[("active", current_theme["bg"])])
    
    # Configure Inner.TCheckbutton for checkbuttons inside tab frames
    style.configure("Inner.TCheckbutton", 
                    background=current_theme["secondary_bg"],
                    foreground=current_theme["fg"],
                    indicatorcolor=current_theme["input_bg"],
                    indicatorbackground=current_theme["input_bg"])
    
    style.map("Inner.TCheckbutton",
              indicatorcolor=[("selected", current_theme["accent"])],
              background=[("active", current_theme["secondary_bg"])])
    
    # Configure TProgressbar
    style.configure("TProgressbar", 
                    background=current_theme["accent"],
                    troughcolor=current_theme["secondary_bg"],
                    bordercolor=current_theme["border"],
                    lightcolor=current_theme["accent_light"],
                    darkcolor=current_theme["accent_dark"])
    
    # Configure TLabelframe
    style.configure("TLabelframe", 
                    background=current_theme["secondary_bg"],
                    foreground=current_theme["fg"],
                    bordercolor=current_theme["border"])
    
    style.configure("TLabelframe.Label", 
                    background=current_theme["bg"],
                    foreground=current_theme["fg"])
    
    # Configure TPanedwindow
    style.configure("TPanedwindow", 
                    background=current_theme["bg"],
                    sashrelief="flat")
    
    # Configure TScale (slider)
    style.configure("TScale", 
                    background=current_theme["bg"],
                    troughcolor=current_theme["secondary_bg"],
                    sliderrelief="flat")
    
    # Root window configuration
    root.configure(background=current_theme["bg"])
    
    # Configure standard Tkinter widgets by updating the option database
    root.option_add("*Text.background", current_theme["input_bg"])
    root.option_add("*Text.foreground", current_theme["fg"])
    root.option_add("*Text.insertBackground", current_theme["fg"])  # Text cursor
    root.option_add("*Text.selectBackground", current_theme["accent"])
    root.option_add("*Text.selectForeground", current_theme["fg"])
    
    root.option_add("*Listbox.background", current_theme["input_bg"])
    root.option_add("*Listbox.foreground", current_theme["fg"])
    root.option_add("*Listbox.selectBackground", current_theme["accent"])
    root.option_add("*Listbox.selectForeground", current_theme["fg"])
    
    root.option_add("*Canvas.background", current_theme["bg"])
    root.option_add("*Canvas.highlightthickness", 0)  # Remove highlight border
    
    root.option_add("*Menu.background", current_theme["bg"])
    root.option_add("*Menu.foreground", current_theme["fg"])
    root.option_add("*Menu.activeBackground", current_theme["accent"])
    root.option_add("*Menu.activeForeground", current_theme["fg"])
    
    # Override any platform-specific appearance
    try:
        root.tk.call("tk_setPalette", current_theme["bg"])
    except Exception:
        pass

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
    
    # Configure inner frame style
    style.configure("Inner.TFrame", background=current_theme["secondary_bg"])
    style.configure("Inner.TLabel", background=current_theme["secondary_bg"])
    
    # Configure option menu items
    root.option_add("*TCombobox*Listbox*Background", current_theme["input_bg"])
    root.option_add("*TCombobox*Listbox*Foreground", current_theme["fg"])
    root.option_add("*TCombobox*Listbox*selectBackground", current_theme["accent"])

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