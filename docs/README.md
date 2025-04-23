# DualGPUOptimizer Documentation

Welcome to the DualGPUOptimizer documentation. This directory contains detailed information about the project, its components, and how to use it effectively.

## System Requirements

- Python 3.8 or higher (Python 3.12 fully supported)
- NVIDIA GPUs with CUDA support
- PySide6 ≥ 6.6 (tested on 6.8) for the Qt-based GUI 

## Available Documentation

- [Quick Start Guide](QUICK_START.md) - Get up and running quickly
- [Model Profiles Documentation](MODEL_PROFILES.md) - Details on model memory profiles and optimization
- [TODO List](TODO.md) - Planned improvements and development roadmap

## Core Concepts

The DualGPUOptimizer is built around several key concepts:

1. **GPU Memory Management** - Efficient allocation of VRAM across multiple GPUs
2. **Model Layer Distribution** - Optimized placement of transformer layers
3. **Memory Profiling** - Accurate estimation of model memory requirements
4. **Framework Integration** - Specialized support for llama.cpp and vLLM

## Main Components

| Component | Description |
|-----------|-------------|
| Model Profiles | Standardized memory consumption patterns for ML models |
| GPU Telemetry | Real-time monitoring of GPU metrics |
| Optimization Engine | Algorithms for optimal resource allocation |
| Launcher | Execution management for inference processes |
| Dashboard | Visual monitoring of GPU performance |

## Project Structure

```
DualGPUOptimizer/
├── dualgpuopt/           # Main module
│   ├── batch/           # Batch processing optimization
│   ├── commands/        # Framework-specific command generation
│   ├── gui/             # Tkinter GUI components
│   ├── qt/              # PySide6/Qt GUI components
│   ├── resources/       # Icons and assets
│   ├── services/        # Core services (config, events)
│   ├── ctx_size.py      # Context size calculation
│   ├── gpu_info.py      # GPU detection and information
│   ├── layer_balance.py # Layer distribution optimization
│   ├── model_profiles.py # Model memory profiles
│   ├── telemetry.py     # Real-time GPU metrics collection
│   └── ...
├── docs/                # Documentation (you are here)
├── tests/               # Test suite
└── ...
```

## Further Reading

For more detailed information about specific components, refer to the module docstrings in the source code. Each key module includes comprehensive documentation explaining its purpose and usage.

## Contributing to Documentation

Documentation improvements are always welcome! To contribute:

1. Fork the repository
2. Add or update documentation in the `docs/` directory
3. Submit a pull request

Please maintain the existing documentation style and format.
