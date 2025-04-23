# Real Hardware Setup Guide for DualGPUOptimizer

This guide will help you set up DualGPUOptimizer to work with your actual NVIDIA GPUs.

## Prerequisites

1. **NVIDIA GPUs**: You need at least 2 NVIDIA GPUs for proper dual-GPU optimization
2. **NVIDIA Drivers**: Latest drivers for your GPU (460.x or newer recommended)
3. **CUDA Toolkit**: Version 11.7 or newer recommended (not required but helpful)
4. **Python 3.13**: The application is built for Python 3.13

## Installation Steps

### 1. Install Required Python Packages

```powershell
# Activate your virtual environment
.\venv\Scripts\Activate.ps1

# Install required packages
pip install torch
pip install psutil
pip install nvidia-ml-py3
```

### 2. Verify GPU Detection

Run the following command to verify your GPUs are detected:

```powershell
# Run in CLI mode
.\dist\DualGPUOptimizer.exe --cli
```

You should see output that includes your GPU names, memory, and other information.

### 3. Running With Real Hardware

The application automatically detects your NVIDIA GPUs. Simply run:

```powershell
# GUI Mode
.\dist\DualGPUOptimizer.exe

# CLI Mode
.\dist\DualGPUOptimizer.exe --cli --model-path "C:\path\to\your\model"
```

## Troubleshooting

### No GPUs Detected

If no GPUs are detected:

1. Verify NVIDIA drivers are properly installed
   ```powershell
   nvidia-smi
   ```

2. Check that the NVIDIA Management Library is accessible
   ```powershell
   # Run with verbose logging
   .\dist\DualGPUOptimizer.exe --verbose
   ```

3. Try running in mock mode for testing
   ```powershell
   .\dist\DualGPUOptimizer.exe --mock
   ```

### PyTorch Features Disabled

If you see warnings about PyTorch features being disabled:

1. Install PyTorch with CUDA support
   ```powershell
   pip install torch
   ```

2. Verify PyTorch can access your GPUs
   ```python
   import torch
   print(torch.cuda.is_available())
   print(torch.cuda.device_count())
   ```

## Advanced Options

### Reducing Log Verbosity

If you see too many log messages (especially when running the GUI), you can:

1. Edit the `logconfig.py` file to adjust log levels for specific modules
2. Run with `--no-splash` to reduce startup messages

### Monitoring GPU Performance

The application includes real-time GPU monitoring. You can:

1. View detailed metrics in the GUI dashboard
2. Use the CLI with `--verbose` for additional debug information

## Hardware Requirements

For optimal performance:

- At least 2 NVIDIA GPUs (ideally same model family)
- 8GB+ VRAM on each GPU for most LLMs
- PCIe 3.0 x16 or better for optimal inter-GPU communication
- Windows 10/11 or Linux (Ubuntu 20.04+)
