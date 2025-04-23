"""
Backward compatibility layer for the error_handler module.

This module re-exports the old API from the original error_handler.py
file to ensure that existing code continues to work without modification.
"""

# Re-export all public components from the refactored modules
from dualgpuopt.error_handler.base import ErrorCategory, ErrorDetails, ErrorSeverity
from dualgpuopt.error_handler.decorators import handle_exceptions
from dualgpuopt.error_handler.handler import ErrorHandler, get_error_handler, install_global_handler
from dualgpuopt.error_handler.ui import show_error_dialog

# For backward compatibility
__all__ = [
    "ErrorCategory",
    "ErrorDetails",
    "ErrorSeverity",
    "ErrorHandler",
    "handle_exceptions",
    "get_error_handler",
    "install_global_handler",
    "show_error_dialog",
]
