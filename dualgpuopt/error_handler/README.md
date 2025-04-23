# Error Handler Module

This module provides centralized error handling, logging, and recovery for the DualGPUOptimizer application. It follows a modular design with clear separation of concerns.

## Module Structure

- `__init__.py`: Public API and imports
- `base.py`: Core definitions (ErrorSeverity, ErrorCategory, ErrorDetails)
- `handler.py`: Main ErrorHandler class implementation
- `decorators.py`: Exception handling decorators
- `ui.py`: User interface for error display
- `logging.py`: Specialized logging configuration

## Usage Examples

### Basic Error Handling

```python
from dualgpuopt.error_handler import get_error_handler, ErrorSeverity, ErrorCategory

# Get the singleton handler
error_handler = get_error_handler()

# Handle an error
error_handler.handle_error(
    exception=my_exception,
    component="MyComponent",
    severity=ErrorSeverity.ERROR,
    message="Failed to process data"
)
```

### Using the Decorator

```python
from dualgpuopt.error_handler import handle_exceptions, ErrorSeverity

@handle_exceptions(component="GPUMonitor", severity=ErrorSeverity.ERROR)
def get_gpu_info():
    # This function is protected - any exceptions will be handled
    return gpu_lib.get_info()
```

### Error Callbacks

```python
from dualgpuopt.error_handler import get_error_handler, ErrorSeverity

def on_critical_error(error_details):
    # Do something when a critical error occurs
    print(f"Critical error: {error_details.message}")

# Register the callback
handler = get_error_handler()
handler.register_callback(ErrorSeverity.CRITICAL, on_critical_error)
```

### UI Integration

```python
from dualgpuopt.error_handler import show_error_dialog

# Show an error to the user
show_error_dialog(
    title="Processing Error",
    message="Failed to process the file",
    details="File format not recognized"
)
```
