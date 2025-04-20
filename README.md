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

### Completed Refactorings
- ✅ `memory_monitor.py` (769 lines) - Refactored into multiple components
- ✅ `settings.py` (722 lines) - Refactored into appearance, overclocking, and application settings components
- ✅ `error_handler.py` (558 lines) - Refactored into base, handler, decorators, UI, and logging components

### Test Results for Refactored Modules
- ✅ **Error Handler Module**: All 10 tests pass successfully
- ⚠️ **Settings Module**: Tests require fixing merge conflicts in constants.py
- ⚠️ **Memory Module**: No dedicated test files found
- ⚠️ **Launcher Module**: No dedicated test files found

### Next Steps
1. **Module Refactoring**: Continue with remaining modules >500 lines:
   - `theme.py` (549 lines) - Next priority

2. **Testing Improvements**:
   - Fix import issues and merge conflicts in existing tests
   - Add unit tests for memory and launcher modules
   - Implement test coverage reports

3. **Code Quality**: Fix linter issues related to trailing whitespace

4. **Additional Model Profiles**: Support for newer models like Llama 3, Phi-3, and Claude-optimized variants

5. **Enhanced Memory Management**: More aggressive VRAM optimization and recovery

6. **Advanced Layer Balancing**: Better algorithms for layer distribution across heterogeneous GPUs

7. **Documentation Improvements**: Detailed API docs and usage examples

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