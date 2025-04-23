# Dependency Management System

The DualGPUOptimizer uses a robust dependency management system to handle required and optional dependencies gracefully. This document explains how the system works and how to extend it.

## Table of Contents

1. [Overview](#overview)
2. [Dependency Categories](#dependency-categories)
3. [How It Works](#how-it-works)
4. [Fallback Mechanisms](#fallback-mechanisms)
5. [Runtime Dependency Resolution](#runtime-dependency-resolution)
6. [Extending the System](#extending-the-system)
7. [Troubleshooting](#troubleshooting)

## Overview

The dependency management system enables the application to:

- Run with minimal dependencies while providing fallback functionality
- Automatically detect what optional features can be enabled based on installed packages
- Provide clear instructions for enabling additional features
- Handle graceful degradation when optional dependencies are missing

Central to this system is the `dependency_manager.py` module, which manages the detection, validation, and installation of dependencies.

## Dependency Categories

Dependencies are organized into five categories:

### 1. Required Dependencies

These dependencies are absolutely necessary for the application to run. If any of these are missing, the application will not start:

- **tkinter**: Base UI framework

### 2. Core Dependencies

These dependencies provide core functionality, but the application can run with reduced capabilities if they're missing:

- **pynvml**: NVIDIA GPU monitoring (falls back to mock GPU data)
- **psutil**: System resource monitoring
- **numpy**: Optimization algorithms (falls back to simplified calculations)

### 3. UI Dependencies

These enhance the user interface but have fallbacks to simpler UI components:

- **ttkbootstrap**: Enhanced UI appearance (falls back to standard ttk)
- **ttkthemes**: Additional UI themes (falls back to standard theme)
- **ttkwidgets**: Additional UI widgets (falls back to basic widgets)

### 4. Chat Dependencies

These are required for the chat functionality but aren't needed for the main application:

- **requests**: API communication
- **sseclient-py**: Streaming events

### 5. ML Dependencies

These enable advanced machine learning features but aren't required for basic functionality:

- **torch**: PyTorch for advanced features
- **torchvision**: PyTorch vision utilities
- **torchaudio**: PyTorch audio utilities

## How It Works

### Detection and Validation

At startup, the application:

1. Initializes dependency status using `initialize_dependency_status()`
2. Checks each dependency using `importlib.util.find_spec()` (for most packages) or direct imports (for special cases like tkinter)
3. Tracks availability in the `dependency_status` dictionary
4. For critical dependencies, verifies they work by attempting a test import

### Installation

The system provides installation utilities:

1. `get_missing_dependencies()`: Identifies missing dependencies by category
2. `get_installation_commands()`: Generates appropriate pip commands
3. `install_dependencies()`: Executes installation commands with confirmation

### Integration

The system is integrated at multiple levels:

1. **Direct imports**: UI components import compatibility layers instead of directly importing optional packages
2. **Fallback implementations**: Each module provides its own fallback when dependencies are missing
3. **Dynamic importers**: The `DynamicImporter` class provides methods to import modules with proper fallbacks

## Fallback Mechanisms

### UI Fallbacks

For UI components, fallbacks are implemented through compatibility layers:

```python
# Example of UI compatibility layer use
from dualgpuopt.ui.compat import get_themed_tk, get_meter_widget

# Gets ttkbootstrap Window if available, else standard tk.Tk with styling
root = get_themed_tk()

# Gets a ttkbootstrap Meter if available, else a custom frame with progress bar
meter = get_meter_widget(parent, amounttotal=100, subtext="usage")
```

### GPU Monitoring Fallbacks

The GPU monitoring system falls back to mock data when pynvml is unavailable:

```python
from dualgpuopt.gpu.compat import is_mock_mode

if is_mock_mode():
    # Use mock GPU data
    gpus = generate_mock_gpus(2)
else:
    # Use real GPU data from NVML
    gpus = query_real_gpus()
```

### Chat Dependencies

The chat system uses a compatibility layer to handle missing dependencies:

```python
from dualgpuopt.ui.chat_compat import DEPENDENCIES as CHAT_DEPENDENCIES

# Check if chat is available
if CHAT_DEPENDENCIES["requests"]["available"] and CHAT_DEPENDENCIES["sseclient"]["available"]:
    # Use chat functionality
    requests = CHAT_DEPENDENCIES["requests"]["module"]
    sseclient = CHAT_DEPENDENCIES["sseclient"]["module"]
else:
    # Show fallback UI with installation instructions
```

## Runtime Dependency Resolution

The system supports runtime resolution of dependencies:

1. **Import Wrapper**: `get_import_wrapper()` attempts to import a module and returns a default value if not available
2. **Dynamic Importer**: `DynamicImporter` provides static methods to import modules with appropriate fallbacks
3. **Module Cache**: Imported modules are cached to avoid repeated import attempts

## Extending the System

To add a new dependency:

1. Add it to the appropriate category dictionary:

```python
NEW_DEPENDENCIES = {
    "new_package": {"package": "new_package>=1.0.0", "description": "New feature"},
}

ALL_DEPENDENCIES.update(NEW_DEPENDENCIES)
```

2. Create a compatibility layer for it:

```python
# In a compatibility module
DEPENDENCIES = {
    "new_package": {"available": False, "module": None},
}

try:
    import new_package
    DEPENDENCIES["new_package"]["available"] = True
    DEPENDENCIES["new_package"]["module"] = new_package
except ImportError:
    logger.warning("new_package not installed - some features disabled")
```

3. Add a fallback implementation:

```python
if DEPENDENCIES["new_package"]["available"]:
    # Use the actual implementation
    from new_package import feature
else:
    # Provide a fallback implementation
    class feature:
        def __init__(self):
            self.warning = "Feature not available"
```

## Troubleshooting

### Missing Dependencies

If you encounter issues with missing dependencies:

1. Run `python install_deps.py --check` to see what's missing
2. Install missing dependencies with `python install_deps.py --all`
3. For specific categories, use `--core-only`, `--ui-only`, etc.

### Import Errors

If you encounter import errors:

1. Check if the package is correctly installed using `pip list`
2. Verify Python is using the correct environment
3. Check if the package requires additional system dependencies

### Compatibility Issues

If a dependency works but causes compatibility issues:

1. Create a more robust fallback in the appropriate compatibility layer
2. Add version constraints in the dependency definition
3. Consider making the dependency optional and improving fallback behavior
