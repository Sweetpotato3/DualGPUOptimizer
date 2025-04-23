# Dual GPU Optimizer

A toolkit for optimizing Large Language Model (LLM) inference workloads across multiple NVIDIA GPUs, with specialized support for `llama.cpp` and `vLLM` implementations.

## Features

- **Automatic GPU Resource Allocation**: Intelligently distributes model layers across available GPUs
- **Memory Split Optimization**: Calculates optimal tensor parallel splits based on GPU memory
- **Command Generation**: Creates execution commands for llama.cpp and vLLM frameworks
- **Real-time Monitoring**: Tracks GPU utilization, memory usage, and PCIe bandwidth
- **Resource Efficiency Alerts**: Provides notifications for underutilized GPU resources
- **Model Presets**: Quick configuration for popular LLM models

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/dual-gpu-optimizer.git
cd dual-gpu-optimizer

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m dualgpuopt
```

## Usage

### GUI Mode

The default mode launches a graphical interface:

```bash
python -m dualgpuopt
```

### Command Line Mode

For headless environments or scripting:

```bash
# Generate optimization parameters
python -m dualgpuopt --cli -m path/to/model.gguf -c 65536

# Save environment variables to a file
python -m dualgpuopt --cli -m path/to/model.gguf -e env.sh

# Enable verbose logging
python -m dualgpuopt --cli -v
```

## How It Works

The optimizer analyzes available GPU resources and calculates the optimal distribution of model layers across multiple GPUs. It generates specialized configuration strings for different LLM implementations:

1. **llama.cpp**: Uses the `--gpu-split` parameter to assign specific memory proportions to each GPU
2. **vLLM**: Configures tensor parallelism settings for distributed inference

The real-time monitoring system tracks GPU utilization and provides alerts when resources are being underutilized.

## Requirements

- Python 3.12 or higher
- NVIDIA GPUs with CUDA support
- NVIDIA drivers with NVML support

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
