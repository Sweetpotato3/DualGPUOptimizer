# DualGPUOptimizer

DualGPUOptimizer is a specialized application for managing and optimizing dual GPU setups, particularly focused on machine learning workloads.

## Features

- **GPU Monitoring**: Real-time monitoring of GPU metrics including memory usage, utilization, temperature, and power consumption
- **Model Optimization**: Calculates optimal GPU split ratios for large language models
- **Smart Layer Distribution**: Balances model layers across multiple GPUs based on available memory
- **Execution Management**: Controls and monitors model execution on multiple GPUs
- **GPU Telemetry**: Collects and visualizes detailed GPU performance metrics

## New: Graceful Fallbacks for Dependencies

DualGPUOptimizer now features comprehensive compatibility layers that allow the application to run even when certain dependencies are missing:

- **UI Compatibility**: Falls back to simpler UI components when ttkbootstrap or other UI enhancements aren't available
- **GPU Monitoring**: Provides mock GPU data when pynvml is not installed
- **Chat Module**: Shows helpful installation instructions when chat dependencies are missing
- **Simple UI Mode**: Includes a minimal UI that works with just tkinter when other dependencies are unavailable

This ensures the application can run in various environments and gracefully handles missing dependencies.

## Installation

### Requirements

- Python 3.12+ recommended (3.8+ minimum)
- NVIDIA GPUs with CUDA support
- Windows, Linux, or macOS (with limited functionality on Mac)

### Installation Steps

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/DualGPUOptimizer.git
   cd DualGPUOptimizer
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Dependencies

The application has both core and optional dependencies:

### Core Dependencies
- `pynvml`: For NVIDIA GPU monitoring
- `tk`: For the base UI framework
- `psutil`: For system resource monitoring
- `numpy`: For optimization algorithms

### Optional Dependencies
- `ttkbootstrap`: For enhanced UI appearance
- `ttkthemes`: For additional UI themes
- `ttkwidgets`: For additional UI widgets
- `requests` and `sseclient-py`: For chat functionality
- `torch`, `torchvision`, and `torchaudio`: For advanced GPU features

The application will function with graceful fallbacks when optional dependencies are missing.

## Usage

### Running the Direct Application (Recommended)

For the most reliable startup that avoids import complexity:

```
python run_direct_app.py
```

This provides a simplified interface that works regardless of optional dependencies and demonstrates the functioning of the compatibility layers.

### Running in Standard Mode

```
python -m dualgpuopt
```

### Running in Mock Mode (No GPU Required)

```
python -m dualgpuopt --mock
```

### Command-Line Options

- `--mock`: Enable mock GPU mode for testing
- `--cli`: Run in CLI mode instead of GUI
- `--verbose`: Enable verbose logging
- `--model MODEL`: Specify model path or HuggingFace identifier
- `--ctx-size SIZE`: Set context size
- `--quant METHOD`: Set quantization method (e.g., 'awq', 'gptq')
- `--export FILE`: Export environment variables to file

## Key Features

### GPU Dashboard
The Dashboard tab provides real-time monitoring of GPU metrics, including:
- Memory usage
- GPU utilization
- Temperature
- Power consumption
- Clock speeds

### Optimizer
The Optimizer tab helps calculate optimal GPU configurations for ML models:
- Calculates memory requirements based on model parameters
- Determines optimal tensor parallelism settings
- Generates split ratios for uneven GPU memory sizes
- Predicts maximum batch sizes and context lengths

### Launcher
The Launcher tab provides:
- Integration with popular ML frameworks
- Command generation for optimal GPU performance
- Environment variable configuration
- Process monitoring and management

### Chat Interface
The Chat tab offers:
- Basic interface for testing language models
- Streaming response visualization
- Token throughput metrics

## Troubleshooting

### Missing Dependencies

If you encounter errors about missing dependencies, you can install specific packages:

```
# For enhanced UI
pip install ttkbootstrap ttkthemes ttkwidgets

# For chat functionality
pip install requests sseclient-py

# For advanced GPU features
pip install torch torchvision torchaudio
```

### Application Not Starting

If the main application fails to start:

1. Try the direct application first: `python run_direct_app.py`
2. Check the logs in the `logs` directory for specific errors
3. Run with verbose logging: `python -m dualgpuopt --verbose`
4. Ensure all core dependencies are installed: `python check_deps.py`

### GPU Detection Issues

If the application fails to detect your GPUs:

1. Ensure NVIDIA drivers are installed and up-to-date
2. Try running in mock mode with `--mock` flag
3. Check that `pynvml` is installed correctly

## Development

### Project Structure

- `dualgpuopt/`: Main package directory
  - `gpu/`: GPU monitoring and information modules
  - `gui/`: GUI components and widgets
  - `ui/`: UI compatibility layers
  - `services/`: Background services for configuration, events, etc.
  - `batch/`: Batch processing logic
  - `memory/`: Memory management and monitoring
  - `commands/`: Command generation for different frameworks

### Building from Source

```
python build.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.