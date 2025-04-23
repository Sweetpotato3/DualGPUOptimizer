"""
Error handling service for centralized error management.
"""

from __future__ import annotations

import logging
import tkinter as tk
import traceback
from tkinter import messagebox
from typing import Any, Callable, Dict, Optional

from dualgpuopt.services.event_bus import event_bus


class ErrorService:
    """Service for centralized error handling."""

    # Error severity levels
    ERROR_LEVELS = {
        "INFO": 0,
        "WARNING": 1,
        "ERROR": 2,
        "CRITICAL": 3,
    }

    def __init__(self, root: Optional[tk.Tk] = None) -> None:
        """
        Initialize the error service.

        Args:
            root: Optional root window for displaying dialogs
        """
        self.logger = logging.getLogger("dualgpuopt.services.error")
        self.root = root
        self.error_handlers: Dict[str, Callable] = {}
        self.general_handler: Optional[Callable] = None

    def set_root(self, root: tk.Tk) -> None:
        """
        Set the root window for displaying dialogs.

        Args:
            root: Tkinter root window
        """
        self.root = root

    def register_handler(self, handler: Callable, error_type: str = None) -> None:
        """
        Register a custom handler for errors.

        Args:
            handler: Callback function that takes (error, context)
            error_type: Optional name of the exception class for specific handling
        """
        if error_type:
            self.error_handlers[error_type] = handler
            self.logger.debug(f"Registered custom handler for {error_type}")
        else:
            self.general_handler = handler
            self.logger.debug("Registered general error handler")

    def handle_error(
        self,
        error: Exception,
        level: str = "ERROR",
        title: str = "Error",
        show_dialog: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Handle an error with appropriate logging and user feedback.

        Args:
            error: The exception to handle.
            level: Error severity level ('INFO', 'WARNING', 'ERROR', 'CRITICAL').
            title: Dialog title.
            show_dialog: Whether to show a dialog to the user.
            context: Additional contextual information about the error.
        """
        if context is None:
            context = {}

        # Get error type
        error_type = error.__class__.__name__

        # Log the error
        log_message = f"{error_type}: {str(error)}"
        if context:
            log_message += f" Context: {context}"

        # Log with appropriate level
        if level == "INFO":
            self.logger.info(log_message)
        elif level == "WARNING":
            self.logger.warning(log_message)
        elif level == "ERROR":
            self.logger.error(log_message, exc_info=True)
        elif level == "CRITICAL":
            self.logger.critical(log_message, exc_info=True)

        # Publish error event
        event_data = {
            "error": error,
            "error_type": error_type,
            "level": level,
            "message": str(error),
            "context": context,
        }
        event_bus.publish("error_occurred", event_data)

        # Check for custom handler for this error type
        if error_type in self.error_handlers:
            try:
                self.error_handlers[error_type](error, context)
                return
            except Exception as handler_error:
                self.logger.error(f"Error in custom handler: {handler_error}")

        # Try general handler if available
        if self.general_handler:
            try:
                self.general_handler(error, context)
                return
            except Exception as handler_error:
                self.logger.error(f"Error in general handler: {handler_error}")

        # Show dialog if requested
        if show_dialog and self.root is not None:
            message = str(error)
            if level == "CRITICAL":
                # Add stack trace for critical errors
                message += f"\n\nStack Trace:\n{traceback.format_exc()}"

            if level == "INFO":
                messagebox.showinfo(title, message, parent=self.root)
            elif level == "WARNING":
                messagebox.showwarning(title, message, parent=self.root)
            else:
                messagebox.showerror(title, message, parent=self.root)

    def handle_gpu_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Special handler for GPU-related errors.

        Args:
            error: The GPU-related exception
            context: Additional contextual information
        """
        if context is None:
            context = {}

        error_type = error.__class__.__name__
        self.logger.error(f"GPU error ({error_type}): {error}", exc_info=True)

        # Show special dialog for GPU errors with mock mode option
        if self.root is not None:
            response = messagebox.askquestion(
                "GPU Error",
                f"GPU error detected: {error}\n\n"
                f"Would you like to enable mock GPU mode?",
                icon="warning",
                parent=self.root,
            )

            if response == "yes":
                # Publish event to enable mock mode
                event_bus.publish("enable_mock_mode")


# Create global error service
error_service = ErrorService()
