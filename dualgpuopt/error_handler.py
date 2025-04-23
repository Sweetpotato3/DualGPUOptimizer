"""
Error handling system for DualGPUOptimizer.

This module has been refactored into a package structure for better
maintainability. This file provides backward compatibility with existing code.

The new module structure is:
- error_handler/base.py: Core error types
- error_handler/handler.py: ErrorHandler implementation
- error_handler/decorators.py: Exception handling decorators
- error_handler/ui.py: User interface components
- error_handler/logging.py: Logging configuration
"""

import logging
import warnings

# Show deprecation warning
warnings.warn(
    "Importing directly from error_handler.py is deprecated. "
    "Please import from dualgpuopt.error_handler instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from the compatibility layer
from dualgpuopt.error_handler.compat import *

# Initialize module-level logger for backward compatibility
logger = logging.getLogger("DualGPUOpt.ErrorHandler")

import functools
import sys
import traceback
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Union


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
        import time

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
        import time

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


# Type for error callbacks
ErrorCallback = Callable[[ErrorDetails], None]


class ErrorHandler:
    """
    Centralized error handler for the application.

    Provides methods for handling, logging, and recovering from errors
    with support for custom callbacks and recovery strategies.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton implementation"""
        if cls._instance is None:
            cls._instance = super(ErrorHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_file: Optional[str] = None):
        """Initialize error handler"""
        if self._initialized:
            return

        self._initialized = True
        self._callbacks: Dict[ErrorSeverity, List[ErrorCallback]] = {
            severity: [] for severity in ErrorSeverity
        }

        self._error_counts: Dict[ErrorCategory, int] = dict.fromkeys(ErrorCategory, 0)

        self._recent_errors: List[ErrorDetails] = []
        self._max_recent_errors = 100

        # Set up error log file if provided
        if log_file:
            self._setup_file_logging(log_file)

    def _setup_file_logging(self, log_file: str):
        """Set up file logging for errors"""
        try:
            # Create a file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.ERROR)

            # Create a formatter
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(formatter)

            # Add the handler to the logger
            logger.addHandler(file_handler)
            logger.info(f"Error logging initialized to file: {log_file}")

        except Exception as e:
            logger.error(f"Failed to set up error log file: {e}")

    def register_callback(self, severity: ErrorSeverity, callback: ErrorCallback):
        """
        Register a callback for a specific error severity

        Args:
        ----
            severity: Error severity level to trigger callback
            callback: Function to call when error occurs

        """
        # Support wildcard '*' to register for all severity levels
        if severity == "*":
            for sev in ErrorSeverity:
                self._callbacks[sev].append(callback)
            logger.debug("Registered error callback for all severity levels")
        else:
            self._callbacks[severity].append(callback)
            logger.debug(f"Registered error callback for severity {severity.name}")

    def unregister_callback(self, severity: ErrorSeverity, callback: ErrorCallback) -> bool:
        """
        Unregister a callback

        Args:
        ----
            severity: Error severity level of the callback
            callback: Callback function to remove

        Returns:
        -------
            True if callback was removed, False if not found

        """
        # Support wildcard '*' to unregister from all severity levels
        if severity == "*":
            removed = False
            for sev in ErrorSeverity:
                if callback in self._callbacks[sev]:
                    self._callbacks[sev].remove(callback)
                    removed = True
            if removed:
                logger.debug("Unregistered error callback from all severity levels")
            return removed

        if callback in self._callbacks[severity]:
            self._callbacks[severity].remove(callback)
            logger.debug(f"Unregistered error callback for severity {severity.name}")
            return True
        return False

    def handle_error(
        self,
        exception: Optional[Exception] = None,
        component: str = "unknown",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: Optional[ErrorCategory] = None,
        message: str = "",
        user_message: str = "",
        context: Dict[str, Any] = None,
    ) -> ErrorDetails:
        """
        Handle an error

        Args:
        ----
            exception: The original exception
            component: Component or module where the error occurred
            severity: Error severity level
            category: Error category for grouping
            message: Detailed technical message
            user_message: User-friendly message
            context: Additional context information

        Returns:
        -------
            ErrorDetails object with complete error information

        """
        # Create error details
        error_details = ErrorDetails(
            exception=exception,
            component=component,
            severity=severity,
            category=category,
            message=message,
            user_message=user_message,
            context=context or {},
        )

        # Log the error
        self._log_error(error_details)

        # Update statistics
        self._error_counts[error_details.category] += 1

        # Store in recent errors
        self._recent_errors.append(error_details)
        if len(self._recent_errors) > self._max_recent_errors:
            self._recent_errors.pop(0)

        # Trigger callbacks
        self._trigger_callbacks(error_details)

        return error_details

    def _log_error(self, error_details: ErrorDetails):
        """Log error with appropriate severity"""
        log_message = error_details.message

        if error_details.component:
            log_message = f"[{error_details.component}] {log_message}"

        if error_details.exception:
            log_message = f"{log_message} - Exception: {type(error_details.exception).__name__}: {error_details.exception}"

        if error_details.severity == ErrorSeverity.INFO:
            logger.info(log_message)
        elif error_details.severity == ErrorSeverity.WARNING:
            logger.warning(log_message)
        elif error_details.severity == ErrorSeverity.ERROR:
            logger.error(log_message)
        elif error_details.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error_details.severity == ErrorSeverity.FATAL:
            logger.critical(f"FATAL: {log_message}")

        # For severe errors, log the full details to the debug log
        if error_details.severity in [
            ErrorSeverity.ERROR,
            ErrorSeverity.CRITICAL,
            ErrorSeverity.FATAL,
        ]:
            logger.debug(error_details.format_for_log())

    def _trigger_callbacks(self, error_details: ErrorDetails):
        """Trigger registered callbacks for this error"""
        # Call callbacks for the specific severity
        for callback in self._callbacks[error_details.severity]:
            try:
                callback(error_details)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors"""
        return {
            "total_errors": sum(self._error_counts.values()),
            "by_category": {category.name: count for category, count in self._error_counts.items()},
            "recent_count": len(self._recent_errors),
            "recent_severities": {
                severity.name: sum(1 for e in self._recent_errors if e.severity == severity)
                for severity in ErrorSeverity
            },
        }

    def get_recent_errors(
        self,
        max_count: int = 10,
        severity_filter: Optional[List[ErrorSeverity]] = None,
        category_filter: Optional[List[ErrorCategory]] = None,
    ) -> List[ErrorDetails]:
        """
        Get recent errors with optional filtering

        Args:
        ----
            max_count: Maximum number of errors to return
            severity_filter: Only include errors with these severities
            category_filter: Only include errors in these categories

        Returns:
        -------
            List of matching error details

        """
        filtered = self._recent_errors

        if severity_filter:
            filtered = [e for e in filtered if e.severity in severity_filter]

        if category_filter:
            filtered = [e for e in filtered if e.category in category_filter]

        # Return most recent first
        return list(reversed(filtered))[-max_count:]

    def clear_error_history(self):
        """Clear error history and reset counters"""
        self._recent_errors.clear()
        for category in self._error_counts:
            self._error_counts[category] = 0

        logger.info("Error history cleared")

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Global exception handler for unhandled exceptions

        Args:
        ----
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback

        """
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't handle keyboard interrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Format the traceback
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        # Handle as a critical error
        self.handle_error(
            exception=exc_value,
            component="UnhandledExceptionHandler",
            severity=ErrorSeverity.CRITICAL,
            message=f"Unhandled exception: {exc_value}",
            context={"traceback": tb_str},
        )


def handle_exceptions(
    component: str, severity: ErrorSeverity = ErrorSeverity.ERROR, reraise: bool = False
):
    """
    Decorator to handle exceptions in a function

    Args:
    ----
        component: Component or module name for error tracking
        severity: Default severity level for caught exceptions
        reraise: Whether to reraise the exception after handling

    Example:
    -------
        @handle_exceptions("GPUMonitor", ErrorSeverity.ERROR)
        def get_gpu_info():
            # Function body that might raise exceptions

    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = ErrorHandler()
                handler.handle_error(
                    exception=e,
                    component=component,
                    severity=severity,
                    message=f"Error in {func.__name__}: {e}",
                )

                if reraise:
                    raise

                # Return a default value based on return type annotation if available
                if hasattr(func, "__annotations__") and "return" in func.__annotations__:
                    return_type = func.__annotations__["return"]

                    # Handle Optional types
                    if hasattr(return_type, "__origin__") and return_type.__origin__ is Union:
                        # Handle Optional[X] which is Union[X, None]
                        if type(None) in return_type.__args__:
                            return None

                    # Handle basic types
                    if return_type is bool:
                        return False
                    if return_type is int:
                        return 0
                    if return_type is float:
                        return 0.0
                    if return_type is str:
                        return ""
                    if return_type is list or (
                        hasattr(return_type, "__origin__") and return_type.__origin__ is list
                    ):
                        return []
                    if return_type is dict or (
                        hasattr(return_type, "__origin__") and return_type.__origin__ is dict
                    ):
                        return {}

                return None

        return wrapper

    return decorator


def install_global_handler():
    """Install global exception handler for unhandled exceptions"""
    handler = ErrorHandler()
    sys.excepthook = handler.handle_exception
    logger.info("Global exception handler installed")


# Function to get the singleton instance
def get_error_handler() -> ErrorHandler:
    """Get or create singleton error handler instance"""
    return ErrorHandler()


# Add missing function
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
