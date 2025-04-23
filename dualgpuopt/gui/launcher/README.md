# Launcher Module

The launcher module provides functionality for launching and managing models on multiple GPUs with optimized parameters.

## Refactoring Overview

This module was recently refactored from a monolithic `launcher.py` file (1000+ lines) into a modular architecture to improve:

- **Maintainability**: Smaller, focused components are easier to maintain
- **Testability**: Individual components can be tested in isolation
- **Performance**: More efficient resource management
- **Extensibility**: Easy to add new features in specific areas

## Architecture

The module is now organized into these components:

- `launch_controller.py`: Core controller for launching and managing model processes
- `parameter_resolver.py`: Handles parameter resolution for different frameworks
- `model_validation.py`: Validates model paths and parameters
- `process_monitor.py`: Monitors and manages running processes
- `config_handler.py`: Handles configuration saving and loading
- `ui_components.py`: UI components for the launcher tab
- `launcher_compat.py`: Compatibility layer for backward compatibility

## Component Relationships

```
┌──────────────────┐      ┌───────────────────┐
│                  │      │                   │
│  LauncherTab     │◄─────┤  LaunchController │
│  (ui_components) │      │                   │
│                  │      └────────┬──────────┘
└──────────────────┘               │
                                   │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼─────────┐      ┌────────▼────────┐      ┌─────────▼─────────┐
│                 │      │                 │      │                   │
│ ParameterResolver│      │ ModelValidator  │      │  ProcessMonitor   │
│                 │      │                 │      │                   │
└─────────────────┘      └─────────────────┘      └───────────────────┘
                                                           │
                                                  ┌────────▼────────┐
                                                  │                 │
                                                  │ ConfigHandler   │
                                                  │                 │
                                                  └─────────────────┘
```

## Backward Compatibility

For backward compatibility, we provide:

1. A compatibility layer in `launcher_compat.py` that maintains the original API
2. The original `launcher.py` file now imports from these modules to maintain its interface
3. The `ModelRunner` class is preserved with its original API

## Usage

### Modern Usage

```python
from dualgpuopt.gui.launcher import LaunchController, ParameterResolver

# Create a controller
controller = LaunchController(gpus)

# Launch a model
success, process_id, error = controller.launch_model(
    model_path="models/llama-7b.gguf",
    framework="llama.cpp",
    parameters={
        "ctx_size": 4096,
        "gpu_split": "60,40",
        "batch_size": 1
    }
)

# Stop a model
controller.stop_model(process_id)
```

### Legacy Usage

```python
from dualgpuopt.gui.launcher import LauncherTab, ModelRunner

# Create launcher tab in UI
launcher_tab = LauncherTab(parent_frame)

# Create model runner
log_queue = queue.Queue()
runner = ModelRunner(log_queue)
runner.start(command, env)
```

## Future Improvements

- Add unit tests for each component
- Improve error handling and recovery mechanisms
- Add support for additional frameworks
- Enhance GPU memory management strategies
