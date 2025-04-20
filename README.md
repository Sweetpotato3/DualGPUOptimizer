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

## Next Steps

Future development priorities:

1. **Code Cleanup**: Fix linter issues related to trailing whitespace
2. **Improved Error Handling**: Better error reporting when `calc_max_ctx` or other functions are missing
3. **Additional Model Profiles**: Support for newer models like Llama 3, Phi-3, and Claude-optimized variants
4. **Enhanced Memory Management**: More aggressive VRAM optimization and recovery
5. **Advanced Layer Balancing**: Better algorithms for layer distribution across heterogeneous GPUs
6. **Documentation Improvements**: Detailed API docs and usage examples

## License

MIT