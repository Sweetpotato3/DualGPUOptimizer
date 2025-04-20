# DualGPUOptimizer

A Tkinter GUI application for optimizing and managing dual GPU setups for large language model inference.

## Requirements

- Python 3.12 or higher
- NVIDIA GPUs with CUDA support
- NVIDIA drivers >= 535.xx

## Installation

### Install dependencies

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# OR
.venv\Scripts\activate     # On Windows

# Install required dependencies
pip install -e .

# Install PyTorch with CUDA support
# For Python 3.12+ users:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# For Python 3.11 or earlier:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu122
```

### Notes for Windows PowerShell users

When installing PyTorch in PowerShell, use backtick (`) for line continuation instead of backslash:

```powershell
pip install torch torchvision torchaudio `
  --index-url https://download.pytorch.org/whl/cu121
```

Do NOT use backslash (\) as it can cause PowerShell to send the root directory "\" as a package name.

## Running the application

```bash
python run_optimizer.py
```

## Building executable

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --name=DualGPUOptimizer --windowed run_optimizer.py
```

## Architecture Overview

The DualGPUOptimizer consists of several key components:

### GPU Management and Monitoring
- Probes and validates GPU configurations through NVML integration
- Collects real-time telemetry including memory, utilization, and power usage
- Provides mock GPU mode for testing without hardware

### Model Optimization Engine
- Calculates optimal memory splits between GPUs based on model requirements
- Implements layer distribution algorithms for transformer models
- Supports framework-specific command generation for llama.cpp and vLLM

### Model Profiles and Memory Management
- Maintains detailed profiles for popular LLM models (Llama 2, Mistral, Mixtral)
- Estimates memory requirements based on model architecture and quantization
- Recommends optimal GPU splits for different VRAM configurations
- Applies model-specific optimizations using the `apply_profile` function

### Execution Management
- Controls model execution across multiple GPUs
- Provides real-time resource monitoring through an interactive dashboard
- Implements idle detection and optimization alerts

### Code Organization
- Follows a modular architecture with separation of concerns
- Recently completed refactoring of `launcher.py` into smaller, focused components
- Completed refactoring of `settings.py` into a modular structure with separate components for appearance, overclocking, and application settings
- Completed refactoring of `error_handler.py` into a modular structure with base definitions, core handler, decorators, UI components, and logging
- Added comprehensive documentation and unit tests for refactored components
- Ongoing initiative to refactor large modules (>500 lines) for improved maintainability
- See `dualgpuopt/REFACTORING.md` for details on the refactoring strategy

## Refactoring Progress and Testing Status

### Recent Refactorings

Since the project start, we've been focused on modularizing the codebase to improve maintainability and testability. Recent work includes:

- ✅ **GPU Module**: Refactored `gpu_info.py` into a modular structure with distinct components:
  - `gpu/info.py`: Core GPU querying functionality
  - `gpu/mock.py`: Mock GPU generation for testing
  - `gpu/monitor.py`: Specialized monitoring functions
  - `gpu/common.py`: Shared functionality and constants
  - `gpu/compat.py`: Backward compatibility layer
  - Added unit tests to validate functionality

- ✅ `memory_monitor.py` (769 lines) - Refactored into multiple components
- ✅ `settings.py` (722 lines) - Refactored into appearance, overclocking, and application settings components
- ✅ `error_handler.py` (558 lines) - Refactored into base, handler, decorators, UI, and logging components
- ✅ `theme.py` (549 lines) - Refactored into colors, dpi, styling, compatibility, and core components
- ✅ `launcher.py` (1000+ lines) - Refactored into controller, parameter resolver, model validation, process monitor, and config handler components

### Test Status for Refactored Modules

- ✅ **GPU Module**: Unit tests for query, monitoring, and compatibility
- ✅ **Error Handler Module**: All 10 tests pass successfully
- ✅ **Memory Module**: Tests for monitor, metrics, alerts, recovery, and prediction
- ✅ **Launcher Module**: Tests for controller, parameter resolver, model validation, process monitor, and config handler
- ✅ **Theme Module**: Tests for colors, DPI, styling, core, and compatibility
- ✅ **Settings Module**: Tests for appearance, overclocking, and application settings

### Next Steps
1. **Testing Improvements**:
   - Setup continuous integration with automated test runs
   - Implement test coverage reports
   - Add integration tests for the full application

2. **Additional Model Profiles**: Support for newer models like Llama 3, Phi-3, and Claude-optimized variants

3. **Enhanced Memory Management**: More aggressive VRAM optimization and recovery

4. **Advanced Layer Balancing**: Better algorithms for layer distribution across heterogeneous GPUs

5. **Documentation Improvements**: Detailed API docs and usage examples

## Supported Models

The application includes built-in profiles for various language models:

- **Llama 2 Family**: 7B, 13B, and 70B parameter variants
- **Mistral 7B**: With sliding window attention support
- **Mixtral 8x7B**: With Mixture-of-Experts architecture support
- **Custom Models**: User-defined model parameters

Each profile contains memory estimates, optimal batch sizes, and layer distribution recommendations specifically tuned for dual-GPU setups.

## PyTorch Compatibility

The application requires PyTorch with CUDA support:

- Python 3.12+: PyTorch 2.5.1 with CUDA 12.1
- Python 3.11 or earlier: PyTorch 2.3.1 with CUDA 12.2

If PyTorch is not detected, the application will attempt to install the appropriate version automatically.

## License

MIT