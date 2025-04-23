"""
Core ErrorHandler implementation for the DualGPUOptimizer.

This module provides the main ErrorHandler class that manages error handling,
logging, callbacks, and error statistics collection.
"""

import logging
import sys
from typing import Any, Callable, Dict, List, Optional

from dualgpuopt.error_handler.base import ErrorCategory, ErrorDetails, ErrorSeverity

# Type for error callbacks
ErrorCallback = Callable[[ErrorDetails], None]

# Initialize module-level logger
logger = logging.getLogger("DualGPUOpt.ErrorHandler")


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

        self._error_counts: Dict[ErrorCategory, int] = {category: 0 for category in ErrorCategory}

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
        import traceback

        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        # Handle as a critical error
        self.handle_error(
            exception=exc_value,
            component="UnhandledExceptionHandler",
            severity=ErrorSeverity.CRITICAL,
            message=f"Unhandled exception: {exc_value}",
            context={"traceback": tb_str},
        )


# Function to get the singleton instance
def get_error_handler() -> ErrorHandler:
    """Get or create singleton error handler instance"""
    return ErrorHandler()


def install_global_handler():
    """Install global exception handler for unhandled exceptions"""
    handler = ErrorHandler()
    sys.excepthook = handler.handle_exception
    logger.info("Global exception handler installed")
