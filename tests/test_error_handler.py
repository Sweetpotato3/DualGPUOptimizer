"""
Tests for the refactored error_handler module.

These tests verify the functionality of the error handling system,
including core components, decorators, and UI integration.
"""

import unittest
from unittest.mock import MagicMock, patch

from dualgpuopt.error_handler import (
    ErrorCategory, ErrorDetails, ErrorSeverity,
    handle_exceptions, track_errors, 
    get_error_handler
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
    """Test ErrorHandler class"""
    
    def test_singleton_pattern(self):
        """Test that ErrorHandler follows singleton pattern"""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        self.assertIs(handler1, handler2)
        
    def test_error_handling(self):
        """Test basic error handling"""
        handler = get_error_handler()
        
        # Clear previous errors
        handler.clear_error_history()
        
        # Handle a test error
        error_details = handler.handle_error(
            exception=ValueError("Test error"),
            component="TestComponent",
            message="A test error occurred"
        )
        
        # Get error summary
        summary = handler.get_error_summary()
        self.assertEqual(summary["total_errors"], 1)
        
        # Get recent errors
        recent = handler.get_recent_errors(max_count=1)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].message, "A test error occurred")
        
    def test_callbacks(self):
        """Test error callbacks"""
        handler = get_error_handler()
        
        # Create a mock callback
        callback = MagicMock()
        
        # Register the callback
        handler.register_callback(ErrorSeverity.ERROR, callback)
        
        # Handle an error
        handler.handle_error(
            exception=ValueError("Test error"),
            component="TestComponent",
            severity=ErrorSeverity.ERROR
        )
        
        # Check that callback was called
        callback.assert_called_once()
        
        # Unregister the callback
        handler.unregister_callback(ErrorSeverity.ERROR, callback)
        
        # Reset the mock
        callback.reset_mock()
        
        # Handle another error
        handler.handle_error(
            exception=ValueError("Another test error"),
            component="TestComponent",
            severity=ErrorSeverity.ERROR
        )
        
        # Check that callback was not called
        callback.assert_not_called()


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