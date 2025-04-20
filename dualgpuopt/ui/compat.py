"""
UI Compatibility Layer

Provides graceful fallbacks for UI dependencies that might not be installed.
"""
from __future__ import annotations
import logging
import sys
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, Optional, Type, Callable

# Configure logger
logger = logging.getLogger("DualGPUOpt.UI.Compat")

# Default theme colors to use when ttkbootstrap is not available
DEFAULT_THEME = {
    "bg": "#2b2b2b",
    "fg": "#e0e0e0",
    "primary": "#6d55c8",
    "secondary": "#7e68ca",
    "success": "#28a745",
    "info": "#17a2b8",
    "warning": "#ffc107",
    "danger": "#dc3545",
    "border": "#444444",
}

# Track the status of optional dependencies
DEPENDENCIES = {
    "ttkbootstrap": {"available": False, "module": None},
    "ttkthemes": {"available": False, "module": None},
    "ttkwidgets": {"available": False, "module": None},
}

# Try to import optional dependencies and mark their availability
try:
    import ttkbootstrap
    DEPENDENCIES["ttkbootstrap"]["available"] = True
    DEPENDENCIES["ttkbootstrap"]["module"] = ttkbootstrap
    logger.info("ttkbootstrap is available")
except ImportError:
    logger.warning("ttkbootstrap is not installed - using standard ttk theming")

try:
    import ttkthemes
    DEPENDENCIES["ttkthemes"]["available"] = True
    DEPENDENCIES["ttkthemes"]["module"] = ttkthemes
    logger.info("ttkthemes is available")
except ImportError:
    logger.warning("ttkthemes is not installed - using standard ttk theming")

try:
    import ttkwidgets
    DEPENDENCIES["ttkwidgets"]["available"] = True
    DEPENDENCIES["ttkwidgets"]["module"] = ttkwidgets
    logger.info("ttkwidgets is available")
except ImportError:
    logger.warning("ttkwidgets is not installed - some widgets will be unavailable")

def get_themed_tk() -> tk.Tk:
    """
    Get the best available themed Tk root window

    Returns:
        tk.Tk: A Tk window with the best available theming
    """
    if DEPENDENCIES["ttkbootstrap"]["available"]:
        # Use ttkbootstrap if available (best option)
        return DEPENDENCIES["ttkbootstrap"]["module"].Window(themename="darkly")
    elif DEPENDENCIES["ttkthemes"]["available"]:
        # Otherwise try ttkthemes
        return DEPENDENCIES["ttkthemes"]["module"].ThemedTk(theme="equilux")
    else:
        # Fall back to standard Tk
        root = tk.Tk()
        # Apply basic dark theme styling
        root.configure(bg=DEFAULT_THEME["bg"])
        style = ttk.Style(root)
        style.configure(".", background=DEFAULT_THEME["bg"], foreground=DEFAULT_THEME["fg"])
        style.configure("TLabel", background=DEFAULT_THEME["bg"], foreground=DEFAULT_THEME["fg"])
        style.configure("TButton", background=DEFAULT_THEME["primary"], foreground=DEFAULT_THEME["fg"])
        style.configure("TFrame", background=DEFAULT_THEME["bg"])
        style.configure("TNotebook", background=DEFAULT_THEME["bg"])
        style.configure("TNotebook.Tab", background=DEFAULT_THEME["secondary"], foreground=DEFAULT_THEME["fg"])
        return root

def get_meter_widget(parent: tk.Widget, **kwargs) -> ttk.Frame:
    """
    Get a meter widget if available, or a fallback frame with a progress bar

    Args:
        parent: Parent widget
        **kwargs: Keyword arguments for the meter

    Returns:
        Widget that mimics a meter with the best available implementation
    """
    if DEPENDENCIES["ttkbootstrap"]["available"] and hasattr(DEPENDENCIES["ttkbootstrap"]["module"], "Meter"):
        return DEPENDENCIES["ttkbootstrap"]["module"].Meter(parent, **kwargs)
    else:
        # Create a fallback frame with a progress bar
        frame = ttk.Frame(parent)

        # Extract relevant arguments
        amounttotal = kwargs.get("amounttotal", 100)
        amountused = kwargs.get("amountused", 0)
        subtext = kwargs.get("subtext", "")

        # Create a progress bar
        bar = ttk.Progressbar(frame, orient="horizontal", length=100, mode="determinate")
        bar.configure(maximum=amounttotal, value=amountused)
        bar.pack(side="top", padx=5, pady=5, fill="x")

        # Create a label for the subtext
        label = ttk.Label(frame, text=f"{amountused} {subtext}")
        label.pack(side="top")

        # Add a method to update the progress bar
        def configure(**cfg):
            if "amountused" in cfg:
                bar.configure(value=cfg["amountused"])
                label.configure(text=f"{cfg['amountused']} {subtext}")

        # Attach the configure method to the frame
        frame.configure = configure

        return frame

# For ScrolledFrame fallback
class ScrolledFrame(ttk.Frame):
    """A frame with a scrollbar that scrolls another frame"""

    def __init__(self, parent, autohide=True):
        """Initialize the ScrolledFrame

        Args:
            parent: Parent widget
            autohide: Whether to hide the scrollbar when not needed
        """
        super().__init__(parent)

        # Create a canvas with scrollbar
        self.canvas = tk.Canvas(self, bg=DEFAULT_THEME["bg"],
                               highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical",
                                      command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create the scrollable frame
        self.inner_frame = ttk.Frame(self.canvas)
        self.inner_frame_id = self.canvas.create_window((0, 0),
                                                     window=self.inner_frame,
                                                     anchor="nw")

        # Pack the widgets
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Configure the canvas to expand the inner frame to its width
        def _configure_inner_frame(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            # Set the scrollable frame's width to match the canvas
            self.canvas.itemconfigure(self.inner_frame_id,
                                     width=event.width)

        # Bind to the configure event
        self.inner_frame.bind("<Configure>", _configure_inner_frame)
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self.inner_frame_id, width=e.width))

        # Forward methods to the inner frame
        def __getattr__(self, attr):
            if hasattr(self.inner_frame, attr):
                return getattr(self.inner_frame, attr)
            raise AttributeError(f"'ScrolledFrame' object has no attribute '{attr}'")

        # Set the __getattr__ method
        self.__class__.__getattr__ = __getattr__

# Make ScrolledFrame available if ttkbootstrap is not installed
if not DEPENDENCIES["ttkbootstrap"]["available"]:
    logger.info("Using custom ScrolledFrame implementation")
else:
    # Use ttkbootstrap's ScrolledFrame if available
    ScrolledFrame = DEPENDENCIES["ttkbootstrap"]["module"].scrolled.ScrolledFrame