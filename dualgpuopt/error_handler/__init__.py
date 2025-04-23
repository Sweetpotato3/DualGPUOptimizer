"""
Error handling module for the DualGPUOptimizer.

This module provides a comprehensive error handling system
for logging, displaying, and recovering from errors throughout
the application.
"""

# Import core components for public API
from dualgpuopt.error_handler.base import ErrorCategory, ErrorDetails, ErrorSeverity
from dualgpuopt.error_handler.decorators import category_exceptions, handle_exceptions, track_errors
from dualgpuopt.error_handler.handler import ErrorHandler, get_error_handler, install_global_handler
from dualgpuopt.error_handler.logging import (
    configure_logging,
    get_error_logger,
    log_exception,
    log_system_info,
)
from dualgpuopt.error_handler.ui import (
    create_error_status_widget,
    register_ui_callbacks,
    show_error_dialog,
    show_warning_dialog,
)

# Export all public components
__all__ = [
    # Base types
    "ErrorCategory",
    "ErrorDetails",
    "ErrorSeverity",
    # Decorators
    "handle_exceptions",
    "track_errors",
    "category_exceptions",
    # Handler
    "ErrorHandler",
    "get_error_handler",
    "install_global_handler",
    # Logging
    "configure_logging",
    "get_error_logger",
    "log_exception",
    "log_system_info",
    # UI
    "show_error_dialog",
    "show_warning_dialog",
    "create_error_status_widget",
    "register_ui_callbacks",
]
