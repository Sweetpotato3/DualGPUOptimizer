"""
Error handling decorators for the DualGPUOptimizer.

This module provides decorators that can be applied to functions to
automatically handle exceptions and apply appropriate error handling.
"""

import functools
import logging
from typing import Any, Callable, Dict, Optional, Union

from dualgpuopt.error_handler.base import ErrorCategory, ErrorSeverity
from dualgpuopt.error_handler.handler import get_error_handler

# Initialize module-level logger
logger = logging.getLogger("DualGPUOpt.ErrorDecorators")


def handle_exceptions(component: str,
                     severity: ErrorSeverity = ErrorSeverity.ERROR,
                     reraise: bool = False):
    """
    Decorator to handle exceptions in a function

    Args:
        component: Component or module name for error tracking
        severity: Default severity level for caught exceptions
        reraise: Whether to reraise the exception after handling

    Example:
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
                handler = get_error_handler()
                handler.handle_error(
                    exception=e,
                    component=component,
                    severity=severity,
                    message=f"Error in {func.__name__}: {e}"
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
                    elif return_type is int:
                        return 0
                    elif return_type is float:
                        return 0.0
                    elif return_type is str:
                        return ""
                    elif return_type is list or (hasattr(return_type, "__origin__") and return_type.__origin__ is list):
                        return []
                    elif return_type is dict or (hasattr(return_type, "__origin__") and return_type.__origin__ is dict):
                        return {}

                return None

        return wrapper
    return decorator


def track_errors(func=None, *, component: Optional[str] = None):
    """
    Decorator to track errors without interfering with normal exception flow.
    This decorator logs errors but doesn't catch them - they will continue to propagate.

    Can be used with or without arguments:
    @track_errors
    def my_func():
        ...

    @track_errors(component="CustomComponent")
    def my_other_func():
        ...
    """
    def decorator(fn):
        _component = component or fn.__module__

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                # Log the error but don't handle it
                handler = get_error_handler()
                handler.handle_error(
                    exception=e,
                    component=_component,
                    severity=ErrorSeverity.ERROR,
                    message=f"Error tracked in {fn.__name__}: {e}"
                )
                # Re-raise the exception
                raise
        return wrapper

    # Handle both @track_errors and @track_errors(component="...")
    if func is not None:
        return decorator(func)
    return decorator


def category_exceptions(category: ErrorCategory):
    """
    Decorator to categorize exceptions raised by a function.

    Args:
        category: The category to assign to any exceptions raised

    Example:
        @category_exceptions(ErrorCategory.GPU_ERROR)
        def get_gpu_memory():
            # This function's exceptions will be categorized as GPU_ERROR
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = get_error_handler()
                handler.handle_error(
                    exception=e,
                    component=func.__module__,
                    category=category,
                    message=f"Error in {func.__name__}: {e}"
                )
                raise
        return wrapper
    return decorator