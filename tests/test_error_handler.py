"""
Tests for the refactored error_handler module.

These tests verify the functionality of the error handling system,
including core components, decorators, and UI integration.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add the parent directory to sys.path to make dualgpuopt importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from dualgpuopt.error_handler import (
    ErrorCategory, ErrorDetails, ErrorSeverity,
    handle_exceptions, track_errors
)


class TestErrorTypes(unittest.TestCase):
    """Test error type definitions"""

    def test_error_severity_values(self):
        """Test that all error severity levels are defined"""
        self.assertTrue(hasattr(ErrorSeverity, "INFO"))
        self.assertTrue(hasattr(ErrorSeverity, "WARNING"))
        self.assertTrue(hasattr(ErrorSeverity, "ERROR"))
        self.assertTrue(hasattr(ErrorSeverity, "CRITICAL"))
        self.assertTrue(hasattr(ErrorSeverity, "FATAL"))

    def test_error_category_values(self):
        """Test that key error categories are defined"""
        self.assertTrue(hasattr(ErrorCategory, "GPU_ERROR"))
        self.assertTrue(hasattr(ErrorCategory, "MEMORY_ERROR"))
        self.assertTrue(hasattr(ErrorCategory, "FILE_ERROR"))
        # Add more as needed


class TestErrorDetails(unittest.TestCase):
    """Test ErrorDetails container"""

    def test_init_with_minimal_args(self):
        """Test ErrorDetails initialization with minimal arguments"""
        details = ErrorDetails()
        self.assertEqual(details.component, "unknown")
        self.assertEqual(details.severity, ErrorSeverity.ERROR)
        self.assertEqual(details.category, ErrorCategory.UNKNOWN_ERROR)
        self.assertEqual(details.message, "Unknown error")
        self.assertIsNotNone(details.user_message)

    def test_init_with_exception(self):
        """Test ErrorDetails initialization with an exception"""
        exception = ValueError("Test error")
        details = ErrorDetails(exception=exception)
        self.assertEqual(details.message, "Test error")
        self.assertEqual(details.exception, exception)

    def test_category_detection(self):
        """Test automatic category detection"""
        details = ErrorDetails(exception=ValueError("Invalid value"))
        self.assertEqual(details.category, ErrorCategory.VALIDATION_ERROR)

        details = ErrorDetails(exception=FileNotFoundError("File not found"))
        self.assertEqual(details.category, ErrorCategory.FILE_ERROR)

        details = ErrorDetails(exception=MemoryError("Out of memory"))
        self.assertEqual(details.category, ErrorCategory.MEMORY_ERROR)


class TestErrorHandler(unittest.TestCase):
    """Test cases for error handling system"""

    def setUp(self):
        """Set up test environment, reset cached modules"""
        # Clear any modules loaded by previous tests
        modules_to_clear = [
            'dualgpuopt.error_handler',
        ]
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]

        # Import error handler
        from dualgpuopt.error_handler import ErrorCategory, ErrorSeverity
        self.ErrorCategory = ErrorCategory
        self.ErrorSeverity = ErrorSeverity

        # Patch logging
        self.log_patcher = patch('dualgpuopt.error_handler.logging')
        self.mock_logging = self.log_patcher.start()
        self.mock_logger = MagicMock()
        self.mock_logging.getLogger.return_value = self.mock_logger

    def tearDown(self):
        """Clean up after tests"""
        self.log_patcher.stop()

    def test_error_categories_and_severities(self):
        """Test error categories and severities are correctly defined"""
        # Verify that error categories are correctly defined
        self.assertIsNotNone(self.ErrorCategory.GPU)
        self.assertIsNotNone(self.ErrorCategory.NETWORK)
        self.assertIsNotNone(self.ErrorCategory.FILE_SYSTEM)
        self.assertIsNotNone(self.ErrorCategory.CONFIGURATION)
        self.assertIsNotNone(self.ErrorCategory.APPLICATION)
        self.assertIsNotNone(self.ErrorCategory.DEPENDENCY)

        # Verify that error severities are correctly defined
        self.assertIsNotNone(self.ErrorSeverity.INFO)
        self.assertIsNotNone(self.ErrorSeverity.WARNING)
        self.assertIsNotNone(self.ErrorSeverity.ERROR)
        self.assertIsNotNone(self.ErrorSeverity.CRITICAL)

    def test_handle_exceptions(self):
        """Test exception handling decorator"""
        from dualgpuopt.error_handler import handle_exceptions

        # Create a test function that raises an exception
        @handle_exceptions(category=self.ErrorCategory.GPU,
                          severity=self.ErrorSeverity.ERROR,
                          recovery_fn=lambda e: "recovered")
        def test_function():
            raise ValueError("Test error")

        # Call the function and verify it recovers from the exception
        result = test_function()
        self.assertEqual(result, "recovered")

        # Verify that the error was logged
        self.mock_logger.error.assert_called()

        # Create a test function without recovery
        @handle_exceptions(category=self.ErrorCategory.NETWORK,
                          severity=self.ErrorSeverity.CRITICAL)
        def test_function_no_recovery():
            raise ValueError("Critical error")

        # Call the function and verify it re-raises the exception
        with self.assertRaises(ValueError):
            test_function_no_recovery()

    def test_error_handler(self):
        """Test error handling function"""
        from dualgpuopt.error_handler import handle_error

        # Test handling different types of errors with different severities

        # Test handling INFO severity
        handle_error(
            Exception("Info error"),
            category=self.ErrorCategory.APPLICATION,
            severity=self.ErrorSeverity.INFO
        )
        self.mock_logger.info.assert_called_with("Info error")

        # Test handling WARNING severity
        handle_error(
            Exception("Warning error"),
            category=self.ErrorCategory.CONFIGURATION,
            severity=self.ErrorSeverity.WARNING
        )
        self.mock_logger.warning.assert_called_with("Warning error")

        # Test handling ERROR severity
        handle_error(
            Exception("Error message"),
            category=self.ErrorCategory.FILE_SYSTEM,
            severity=self.ErrorSeverity.ERROR
        )
        self.mock_logger.error.assert_called_with("Error message")

        # Test handling CRITICAL severity
        handle_error(
            Exception("Critical error"),
            category=self.ErrorCategory.GPU,
            severity=self.ErrorSeverity.CRITICAL
        )
        self.mock_logger.critical.assert_called_with("Critical error")

    @patch('dualgpuopt.error_handler.MAX_RETRY_COUNT', 3)
    def test_recovery_manager(self):
        """Test recovery manager functionality"""
        from dualgpuopt.error_handler import RecoveryManager

        # Create a recovery manager
        manager = RecoveryManager(self.ErrorCategory.GPU)

        # Create a mock recovery strategy
        mock_strategy = MagicMock()
        mock_strategy.return_value = True

        # Add it to the manager
        manager.register_strategy("test_strategy", mock_strategy)

        # Test that the strategy is called when recovering
        error = Exception("Test error")
        success = manager.attempt_recovery(error)

        self.assertTrue(success)
        mock_strategy.assert_called_once_with(error)

        # Test retry count limiting
        mock_strategy.reset_mock()
        mock_strategy.return_value = False  # Make the strategy fail

        # Should make multiple attempts up to the limit
        for _ in range(5):  # More than MAX_RETRY_COUNT
            manager.attempt_recovery(error)

        # Should be called exactly MAX_RETRY_COUNT times
        self.assertEqual(mock_strategy.call_count, 3)

    def test_error_telemetry(self):
        """Test error telemetry collection"""
        from dualgpuopt.error_handler import ErrorTelemetry

        # Create telemetry collector
        telemetry = ErrorTelemetry()

        # Log some errors
        telemetry.record_error(self.ErrorCategory.GPU, self.ErrorSeverity.ERROR, "GPU error")
        telemetry.record_error(self.ErrorCategory.NETWORK, self.ErrorSeverity.WARNING, "Network warning")
        telemetry.record_error(self.ErrorCategory.GPU, self.ErrorSeverity.ERROR, "Another GPU error")

        # Get error counts
        counts = telemetry.get_error_counts()

        # Verify the counts
        self.assertEqual(counts[self.ErrorCategory.GPU], 2)
        self.assertEqual(counts[self.ErrorCategory.NETWORK], 1)

        # Get errors by category
        gpu_errors = telemetry.get_errors_by_category(self.ErrorCategory.GPU)

        # Verify the errors
        self.assertEqual(len(gpu_errors), 2)
        self.assertIn("GPU error", gpu_errors[0])

        # Clear errors
        telemetry.clear()

        # Verify the counts are reset
        counts = telemetry.get_error_counts()
        self.assertEqual(sum(counts.values()), 0)


class TestErrorDecorators(unittest.TestCase):
    """Test error handling decorators"""

    def test_handle_exceptions_decorator(self):
        """Test handle_exceptions decorator"""

        @handle_exceptions("TestComponent")
        def function_that_raises():
            raise ValueError("Test error")

        @handle_exceptions("TestComponent")
        def function_with_return() -> int:
            return 42

        # Function that raises should not propagate the exception
        result = function_that_raises()
        self.assertIsNone(result)

        # Function with return should work normally
        result = function_with_return()
        self.assertEqual(result, 42)

    def test_track_errors_decorator(self):
        """Test track_errors decorator"""

        @track_errors
        def function_that_raises():
            raise ValueError("Test error")

        # Function should propagate the exception
        with self.assertRaises(ValueError):
            function_that_raises()


if __name__ == "__main__":
    unittest.main()