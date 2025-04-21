"""
UI module for DualGPUOptimizer

Provides compatibility layers and widgets that don't depend on advanced UI libraries.
This module ensures the application works even when optional dependencies are missing.
"""
from __future__ import annotations
import logging

# Configure logger
logger = logging.getLogger("DualGPUOpt.UI")

# Try to import our compatibility utilities
try:
    from .compat import (
        get_themed_tk,
        get_meter_widget,
        ScrolledFrame,
        DEPENDENCIES
    )
    from .chat_compat import get_chat_tab

    # Export for direct import
    __all__ = [
        "get_themed_tk",
        "get_meter_widget",
        "ScrolledFrame",
        "get_chat_tab",
    ]

    # Log available UI dependencies
    available_deps = [name for name, info in DEPENDENCIES.items() if info["available"]]
    if available_deps:
        logger.info(f"UI module initialized with: {', '.join(available_deps)}")
    else:
        logger.warning("UI module initialized with no optional dependencies")
except ImportError as e:
    logger.error(f"Failed to import UI compatibility modules: {e}")

    # Define minimal compatibility layer if imports fail
    def get_themed_tk():
        """Get a themed Tk window, falling back to standard Tk"""
        import tkinter as tk
        return tk.Tk()

    def get_meter_widget(parent, **kwargs):
        """Get a meter widget, falling back to a simple frame"""
        from tkinter import ttk
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="0").pack()
        return frame

    # Create a minimal ScrolledFrame
    from tkinter import ttk
    ScrolledFrame = ttk.Frame

    def get_chat_tab(master, out_q):
        """Get a chat tab, falling back to a simple frame"""
        from tkinter import ttk
        frame = ttk.Frame(master)
        ttk.Label(frame, text="Chat not available - missing dependencies").pack(pady=20)
        frame.handle_queue = lambda *args: None
        return frame

    # Export for direct import
    __all__ = [
        "get_themed_tk",
        "get_meter_widget",
        "ScrolledFrame",
        "get_chat_tab",
    ]

    logger.warning("Using minimal UI compatibility layer due to import errors")