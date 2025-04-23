"""
User interface components for error display in the DualGPUOptimizer.

This module provides functions to display error messages to the user
through dialog boxes and other UI elements.
"""

import logging
from typing import Callable, Optional

# Initialize module-level logger
logger = logging.getLogger("DualGPUOpt.ErrorUI")


def show_error_dialog(title: str, message: str, details: Optional[str] = None) -> None:
    """
    Show an error dialog to the user

    Args:
    ----
        title: Dialog title
        message: Main error message
        details: Optional technical details
    """
    # Import here to avoid circular imports
    try:
        import tkinter as tk
        from tkinter import messagebox

        # Create a root window if needed
        try:
            # Try to use an existing Tk instance
            root = tk._default_root or tk.Tk()
            if not tk._default_root:
                root.withdraw()  # Hide the root window
        except Exception:
            # If that fails, create a new one
            root = tk.Tk()
            root.withdraw()  # Hide the root window

        # Add details if provided
        full_message = message
        if details:
            full_message += "\n\nDetails:\n" + details

        # Show the error message
        messagebox.showerror(title, full_message)

        # Destroy the root if we created it
        if not tk._default_root:
            root.destroy()

    except Exception as e:
        # Fall back to console if GUI fails
        logger.error(f"Failed to show error dialog: {e}")
        print(f"ERROR: {title}")
        print(f"Message: {message}")
        if details:
            print(f"Details: {details}")


def show_warning_dialog(title: str, message: str) -> None:
    """
    Show a warning dialog to the user

    Args:
    ----
        title: Dialog title
        message: Warning message
    """
    try:
        import tkinter as tk
        from tkinter import messagebox

        # Create a root window if needed
        try:
            # Try to use an existing Tk instance
            root = tk._default_root or tk.Tk()
            if not tk._default_root:
                root.withdraw()  # Hide the root window
        except Exception:
            # If that fails, create a new one
            root = tk.Tk()
            root.withdraw()  # Hide the root window

        # Show the warning message
        messagebox.showwarning(title, message)

        # Destroy the root if we created it
        if not tk._default_root:
            root.destroy()

    except Exception as e:
        # Fall back to console if GUI fails
        logger.error(f"Failed to show warning dialog: {e}")
        print(f"WARNING: {title}")
        print(f"Message: {message}")


def create_error_status_widget(parent, width: int = 20, height: int = 5) -> tuple:
    """
    Create a widget to display error status in the UI

    Args:
    ----
        parent: Parent widget
        width: Width of the widget
        height: Height of the widget

    Returns:
    -------
        Tuple containing (widget, update_function)
    """
    try:
        import tkinter as tk
        from tkinter import ttk

        # Create a frame
        frame = ttk.Frame(parent)

        # Create a text widget for displaying errors
        text = tk.Text(frame, width=width, height=height, wrap=tk.WORD, state=tk.DISABLED)
        text.grid(row=0, column=0, sticky="nsew")

        # Add a scrollbar
        scrollbar = ttk.Scrollbar(frame, command=text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        text.config(yscrollcommand=scrollbar.set)

        # Update function
        def update_error_display(error_text: str, tag: Optional[str] = None):
            text.config(state=tk.NORMAL)
            text.delete(1.0, tk.END)
            text.insert(tk.END, error_text)
            if tag:
                text.tag_configure(tag, foreground="red")
                text.tag_add(tag, "1.0", tk.END)
            text.config(state=tk.DISABLED)

        return frame, update_error_display

    except Exception as e:
        logger.error(f"Failed to create error status widget: {e}")
        # Return dummy widget and function
        dummy_frame = parent

        def dummy_update(error_text: str, tag: Optional[str] = None):
            logger.info(f"Would display: {error_text}")

        return dummy_frame, dummy_update


def register_ui_callbacks(error_callback: Callable) -> None:
    """
    Register UI callbacks for error handling

    Args:
    ----
        error_callback: Function to call when an error occurs
    """
    from dualgpuopt.error_handler.base import ErrorSeverity
    from dualgpuopt.error_handler.handler import get_error_handler

    # Get the error handler
    handler = get_error_handler()

    # Register callbacks for error severity levels
    for severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL, ErrorSeverity.FATAL]:
        handler.register_callback(severity, error_callback)
