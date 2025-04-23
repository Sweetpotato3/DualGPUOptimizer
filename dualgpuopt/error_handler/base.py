"""
Core error handler definitions for the DualGPUOptimizer.

This module contains the base classes and enums for the error handling system,
including severity levels, error categories, and the ErrorDetails container.
"""

import time
import traceback
from enum import Enum, auto
from typing import Any, Dict, Optional


class ErrorSeverity(Enum):
    """Severity levels for errors"""

    INFO = auto()  # Informational message, not an error
    WARNING = auto()  # Warning, operation can continue
    ERROR = auto()  # Error, operation failed but system can continue
    CRITICAL = auto()  # Critical error, may require user intervention
    FATAL = auto()  # Fatal error, system cannot continue


class ErrorCategory(Enum):
    """Categories of errors for grouping and handling"""

    GPU_ERROR = auto()  # GPU-related errors (driver, NVML, etc.)
    MEMORY_ERROR = auto()  # Memory allocation or OOM errors
    FILE_ERROR = auto()  # File I/O errors
    NETWORK_ERROR = auto()  # Network-related errors
    CONFIG_ERROR = auto()  # Configuration errors
    PROCESS_ERROR = auto()  # Process management errors
    GUI_ERROR = auto()  # GUI-related errors
    API_ERROR = auto()  # External API errors
    VALIDATION_ERROR = auto()  # Input validation errors
    INTERNAL_ERROR = auto()  # Internal logic errors
    UNKNOWN_ERROR = auto()  # Uncategorized errors


class ErrorDetails:
    """Container for detailed error information"""

    def __init__(
        self,
        exception: Optional[Exception] = None,
        component: str = "unknown",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: Optional[ErrorCategory] = None,
        message: str = "",
        user_message: str = "",
        traceback_str: str = "",
        context: Dict[str, Any] = None,
        timestamp: float = None,
    ):
        """
        Initialize error details

        Args:
        ----
            exception: The original exception
            component: Component or module where the error occurred
            severity: Error severity level
            category: Error category for grouping
            message: Detailed technical message
            user_message: User-friendly message
            traceback_str: String representation of the traceback
            context: Additional context information
            timestamp: Error timestamp (if None, will be set when logged)

        """
        self.exception = exception
        self.component = component
        self.severity = severity
        self.category = category or self._detect_category(exception)
        self.message = message or (str(exception) if exception else "Unknown error")
        self.user_message = user_message or self._generate_user_message()
        self.traceback_str = traceback_str or (
            "".join(
                traceback.format_exception(
                    type(exception),
                    exception,
                    exception.__traceback__,
                )
            )
            if exception
            else ""
        )
        self.context = context or {}
        self.timestamp = timestamp or time.time()

    def _detect_category(self, exception: Optional[Exception]) -> ErrorCategory:
        """Detect error category based on exception type"""
        if exception is None:
            return ErrorCategory.UNKNOWN_ERROR

        ex_type = type(exception).__name__.lower()

        # GPU and CUDA errors
        if any(kw in ex_type for kw in ["cuda", "gpu", "nvml", "driver"]):
            return ErrorCategory.GPU_ERROR

        # Memory errors
        if any(kw in ex_type for kw in ["memory", "outofmemory", "oom"]) or isinstance(
            exception, MemoryError
        ):
            return ErrorCategory.MEMORY_ERROR

        # File errors
        if any(kw in ex_type for kw in ["file", "io", "path", "notfound"]) or isinstance(
            exception, (IOError, FileNotFoundError)
        ):
            return ErrorCategory.FILE_ERROR

        # Network errors
        if any(kw in ex_type for kw in ["network", "connection", "timeout", "http"]):
            return ErrorCategory.NETWORK_ERROR

        # Config errors
        if any(kw in ex_type for kw in ["config", "setting", "option"]):
            return ErrorCategory.CONFIG_ERROR

        # Process errors
        if any(kw in ex_type for kw in ["process", "subprocess", "thread", "runtime"]):
            return ErrorCategory.PROCESS_ERROR

        # GUI errors
        if any(kw in ex_type for kw in ["gui", "ui", "window", "widget", "tk"]):
            return ErrorCategory.GUI_ERROR

        # API errors
        if any(kw in ex_type for kw in ["api", "http", "response", "request"]):
            return ErrorCategory.API_ERROR

        # Validation errors
        if any(
            kw in ex_type for kw in ["validation", "invalid", "typeerror", "valueerror"]
        ) or isinstance(exception, (ValueError, TypeError)):
            return ErrorCategory.VALIDATION_ERROR

        # Default to internal error for known Python exceptions
        if isinstance(exception, Exception) and exception.__class__.__module__ == "builtins":
            return ErrorCategory.INTERNAL_ERROR

        return ErrorCategory.UNKNOWN_ERROR

    def _generate_user_message(self) -> str:
        """Generate a user-friendly error message"""
        if self.severity == ErrorSeverity.INFO:
            return self.message

        if self.severity == ErrorSeverity.WARNING:
            return f"Warning: {self.message}"

        if self.severity == ErrorSeverity.ERROR:
            return f"An error occurred in {self.component}: {self.message}"

        if self.severity == ErrorSeverity.CRITICAL:
            return f"Critical error in {self.component}. Please check the logs for details."

        if self.severity == ErrorSeverity.FATAL:
            return f"Fatal error: {self.message}. The application may need to restart."

        return f"Unexpected error in {self.component}"

    def format_for_log(self) -> str:
        """Format the error details for logging"""
        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))

        # Basic info
        lines = [
            f"[{timestamp_str}] {self.severity.name} in {self.component}",
            f"Category: {self.category.name}",
            f"Message: {self.message}",
        ]

        # Add context if available
        if self.context:
            lines.append("Context:")
            for key, value in self.context.items():
                lines.append(f"  {key}: {value}")

        # Add traceback if available
        if self.traceback_str:
            lines.append("Traceback:")
            lines.append(self.traceback_str)

        return "\n".join(lines)
