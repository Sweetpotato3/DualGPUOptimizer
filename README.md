# DualGPUOptimizer

DualGPUOptimizer is a specialized application for managing and optimizing dual GPU setups, particularly focused on machine learning workloads.

## Features

- **GPU Monitoring**: Real-time monitoring of GPU metrics including memory usage, utilization, temperature, and power consumption
- **Model Optimization**: Calculates optimal GPU split ratios for large language models
- **Smart Layer Distribution**: Balances model layers across multiple GPUs based on available memory
- **Execution Management**: Controls and monitors model execution on multiple GPUs
- **GPU Telemetry**: Collects and visualizes detailed GPU performance metrics

## Recent Improvements

### Performance Optimizations

- **Enhanced Telemetry System**:
  - Improved GPU metrics collection with caching and reduced lock contention
  - Parallel batch collection for faster multi-GPU monitoring
  - Optimized data distribution to UI components
  - Thread-safe metrics processing with reduced overhead

- **Optimized Model Calculation Engine**:
  - Vectorized memory calculations using NumPy when available
  - Intelligent caching for repeated operations like context size calculations
  - Reduced redundant GPU information queries
  - Enhanced memory estimation algorithm with improved accuracy

- **Accelerated Layer Balancing**:
  - Multiprocessing GPU profiling for faster layer distribution
  - Thread pool implementation for parallel operations
  - Optimized contiguous block algorithm for better memory locality
  - Improved dynamic programming approach for layer assignments

- **Memory Management Improvements**:
  - Advanced batch prediction using vectorized operations
  - LRU caching for memory profiles and calculations
  - Optimized token usage prediction with time-series analysis
  - Memory-efficient projections for large models

These optimizations significantly improve performance, particularly when working with multiple GPUs and large language models, enabling smoother operation and faster response times throughout the application.

### Circular Import Resolution

- Fixed circular dependencies between telemetry and GPU modules
- Created independent local classes to avoid import cycles
- Improved module initialization with proper error handling

### Robust Chat Dependency Management

- Implemented a compatibility layer for chat module dependencies
- Added fallback functionality when chat dependencies are missing
- Provided helpful installation instructions for users

### Simplified Dependency Installation

- Added a new standalone `install_deps.py` script for easy dependency management
- Support for targeted installation of specific dependency categories (core, UI, chat, ML)
- Clearer feedback about missing dependencies and installation status
- Automatic environment detection and configuration

### Better Application Startup

- Graceful startup even with minimal dependencies
- Clearer error messages when dependencies are missing
- Added fallback UI mode when optional UI packages are unavailable

### Code Quality Enhancements

- Eliminated trailing whitespace and fixed linter errors throughout codebase
- Improved type hints and docstrings for better code readability
- Enhanced error handling with proper exception messages
- Implemented consistent coding style across all modules

### Enhanced UI Component Stability

- Created comprehensive fallback widgets for missing UI dependencies
- Added retry functionality for component initialization failures
- Implemented error explanations with detailed diagnostic information
- Improved widget creation with safe fallback mechanisms

### Completed Event-Driven Architecture

- Fully implemented event bus system for component communication
- Added typed event classes for GPU metrics, configuration changes, and UI updates
- Ensured all components properly subscribe to relevant events
- Implemented event priority system for critical updates

## New: Enhanced Dependency Management System

DualGPUOptimizer now features a robust dependency management system that:

- **Gracefully Handles Missing Dependencies**: The application will run even with minimal dependencies, falling back to basic functionality
- **Auto-Detects Available Modules**: Identifies which optional features can be enabled based on installed packages
- **Provides Clear Installation Instructions**: Shows exactly what to install to enable specific features
- **Supports Command-Line Installation**: Run `python -m dualgpuopt --install-deps` to install missing dependencies
- **Includes Fallback UI**: A minimal UI will run even when optional UI packages are unavailable

The dependency system categorizes dependencies into:

- **Required**: Application won't start without these (e.g., tkinter)
- **Core**: Application works with fallbacks if missing (e.g., pynvml, numpy)
- **Optional**: Enhanced functionality when available (e.g., ttkbootstrap, torch)

## New: Enhanced Error Handling & Recovery System

DualGPUOptimizer now features a comprehensive error handling and recovery system:

- **Centralized Error Management**: All errors are processed through a unified handler with severity levels and categorization
- **Automatic Recovery**: The system attempts to recover from common errors like GPU communication failures
- **Smart Fallbacks**: When components fail, the application gracefully degrades to alternatives rather than crashing
- **Environment Variable Configuration**: System behavior can be controlled through environment variables
- **Detailed Logging**: Enhanced logging captures error context for easier troubleshooting

The recovery system includes strategies for:

- NVML initialization errors
- GPU memory issues
- Configuration problems
- File access failures
- External API communication errors

This robust error handling ensures the application remains functional across different environments and hardware configurations, even when facing unpredictable issues.

## New: Event-Driven Architecture

The direct application now implements a fully event-driven architecture that:

- **Decouples Components**: Dashboard and optimizer components communicate through events rather than direct method calls
- **Improves Extensibility**: New features can subscribe to existing events without modifying the original code
- **Enhances Responsiveness**: Real-time updates flow through the system via events
- **Centralizes Communication**: The event bus serves as a central message broker between components
- **Provides Status Updates**: A status bar shows real-time event information

Event types include:

- `GPUMetricsEvent`: Real-time GPU metrics updates
- `ModelSelectedEvent`: Fired when a model is selected in the optimizer
- `SplitCalculatedEvent`: Contains calculated GPU split configurations
- `ConfigChangedEvent`: Triggered when configuration values change

This architecture follows the same patterns used in the main application, ensuring consistent behavior and making the direct app more maintainable and scalable.

## Complete Functionality in Direct Application

The direct application features a full-featured tabbed interface with:

### Dashboard Tab

- Enhanced GPU metrics visualization with progress bars
- Temperature monitoring with color-coded warnings
- Power usage tracking with limit indicators
- PCIe bandwidth monitoring
- GPU clock speed visualization
- Memory reset capabilities

### Optimizer Tab

- Model selection for popular LLMs (Llama, Mistral, Mixtral)
- Automatic GPU memory split ratio calculation
- Context length optimization
- Custom model parameter configuration
- Command generation for frameworks like llama.cpp and vLLM

Both tabs feature graceful fallbacks when components are unavailable, ensuring the application can run in any environment while providing helpful guidance for enabling full functionality.

## Graceful Fallbacks for Dependencies

DualGPUOptimizer features comprehensive compatibility layers that allow the application to run even when certain dependencies are missing:

- **UI Compatibility**: Falls back to simpler UI components when ttkbootstrap or other UI enhancements aren't available
- **GPU Monitoring**: Provides mock GPU data when pynvml is not installed
- **Chat Module**: Shows helpful installation instructions when chat dependencies are missing
- **Simple UI Mode**: Includes a minimal UI that works with just tkinter when other dependencies are unavailable

This ensures the application can run in various environments and gracefully handles missing dependencies.

## Environment Variable Configuration

DualGPUOptimizer now supports configuration through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DUALGPUOPT_MOCK_GPU` | Force mock GPU mode | `false` |
| `DUALGPUOPT_GPU_COUNT` | Override detected GPU count | Auto-detect |
| `DUALGPUOPT_POLL_INTERVAL` | Telemetry polling interval (seconds) | `1.0` |
| `DUALGPUOPT_MOCK_TELEMETRY` | Force mock telemetry data | `false` |
| `DUALGPUOPT_MAX_RECOVERY` | Maximum recovery attempts | `3` |
| `DUALGPUOPT_SYSTEM_OVERHEAD` | System memory overhead (MB) | `2048` |
| `DUALGPUOPT_SAFETY_MARGIN` | Memory safety margin | `0.1` |
| `DUALGPUOPT_TP_OVERHEAD` | Tensor parallelism overhead | `0.2` |
| `DUALGPUOPT_KV_CACHE_FACTOR` | KV cache size multiplier | `2.0` |
| `DUALGPUOPT_MIN_CONTEXT` | Minimum context size | `128` |
| `DUALGPUOPT_METRIC_CACHE_TTL` | Metrics cache lifetime (seconds) | `0.05` |
| `DUALGPUOPT_OPT_CACHE_TIMEOUT` | Optimizer cache timeout (seconds) | `30` |
| `DUALGPUOPT_PROFILE_CACHE` | Memory profile cache size | `64` |

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

2. Create a virtual environment (recommended):

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Use the dependency installer to install required packages:

   ```
   # Install core dependencies only
   python install_deps.py --core-only

   # Install all dependencies including optional ones
   python install_deps.py --all

   # Install specific dependency categories
   python install_deps.py --ui-only
   python install_deps.py --chat-only
   python install_deps.py --ml-only

   # Or use the module-based installer
   python -m dualgpuopt --install-deps
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

### Recommended: Run the Direct Application

For the most stable experience with the simplest setup, use the direct application:

```
python run_direct_app.py
```

This provides the most reliable startup with complete functionality in a streamlined interface:

- **Automatic dependency detection** - uses what's available and provides fallbacks
- **Simplified architecture** - avoids complex module imports that might cause issues
- **Full-featured interface** - includes both dashboard and optimizer in a tabbed UI
- **Robust error handling** - better recovery from dependency or hardware issues
- **Event-driven design** - more responsive interface with real-time updates

To run in mock mode (no GPU required):

```
python run_direct_app.py --mock
```

### Alternative: Module-Based Approach

If you prefer the module-based approach:

```
python -m dualgpuopt
```

To run in mock mode:

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
- `--check-deps`: Check dependencies and exit
- `--install-deps`: Install missing dependencies

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

### Error Recovery System

The error recovery system provides:

- Automatic recovery from GPU driver issues
- Memory pressure detection and mitigation
- Intelligent fallbacks when components fail
- Detailed error reporting with context

## Troubleshooting

### Missing Dependencies

If you encounter missing dependency errors, use the built-in dependency installer:

```
# Check which dependencies are missing
python install_deps.py --check

# Install missing dependencies
python install_deps.py --all

# Or use the module-based installer
python -m dualgpuopt --install-deps
```

For manual installation of specific package groups:

```
# For core functionality
pip install pynvml psutil numpy

# For enhanced UI
pip install ttkbootstrap ttkthemes ttkwidgets

# For chat functionality
pip install requests sseclient-py

# For advanced GPU features
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1
```

### Application Not Starting

If the application fails to start:

1. Try the direct application first: `python run_direct_app.py`
2. Check the logs in the `logs` directory for specific errors
3. Run with verbose logging: `python -m dualgpuopt --verbose`
4. Verify dependencies are installed: `python install_deps.py --check`

### GPU Detection Issues

If the application fails to detect your GPUs:

1. Ensure NVIDIA drivers are installed and up-to-date
2. Try running in mock mode with `--mock` flag or set `DUALGPUOPT_MOCK_GPU=1`
3. Check that `pynvml` is installed correctly
4. Check driver logs for GPU-related errors

### Environment Variable Configuration

If you need to override default behavior:

1. Set environment variables before running the application
2. For permanent changes, add them to your system environment
3. For testing, use mock mode: `DUALGPUOPT_MOCK_GPU=1 python run_direct_app.py`

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
  - `error_handler/`: Error handling and recovery system
  - `dependency_manager.py`: Dependency management system

### Building from Source

```
python build.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Recently Fixed Issues

### Enhanced Dependency Management

- **Improved Installer Script**: Fixed and enhanced the dependency installer with better error handling
- **Clear Dependency Organization**: Properly categorized dependencies into core, UI, chat, and ML groups
- **Automatic Recovery**: Added fallback paths when optional dependencies are missing
- **Better User Feedback**: Improved console output with color-coded status messages

### Resolved Import Errors

- **Fixed Circular Imports**: Resolved issues between telemetry and GPU modules
- **Standardized Class Naming**: Ensured consistent naming of GPUMetrics class across modules
- **Local Class Declaration**: Used local class declarations to avoid import dependencies

### Improved UI Compatibility Layer

- **Theme Application Support**: Fixed theme application errors in MainApplication
- **Status Variable Handling**: Added ensure_status_var function to prevent 'status_var' not found errors
- **Graceful Fallbacks**: Improved fallback mechanisms when UI enhancement packages are unavailable
- **Consistent Error Handling**: Better handling of UI initialization failures

### Enhanced Error Recovery

- **Component Retry System**: Added retry capability for failed component initialization
- **Detailed Error Reporting**: Improved error messages with context and recovery instructions
- **Event-Based State Synchronization**: Fixed state synchronization issues using events
- **Fallback Widget System**: Implemented comprehensive fallback widgets for all UI components

These improvements create a more stable foundation, enabling the application to run in a wider range of environments with better error recovery.

## New: Comprehensive Testing Framework

DualGPUOptimizer now includes a comprehensive testing framework to ensure code quality and prevent regressions:

### Testing Architecture

The testing framework is organized into three main levels:

- **Unit Tests**: Testing individual components in isolation
- **Integration Tests**: Testing interactions between components
- **Functional Tests**: End-to-end testing of complete features

### Key Test Features

- **Mock GPU Support**: Tests run without requiring actual GPU hardware
- **Event System Testing**: Comprehensive tests for the event-driven architecture
- **Memory Prediction Tests**: Validation of memory allocation calculations
- **Telemetry Verification**: Tests for real-time monitoring accuracy
- **Error Recovery Verification**: Tests that error recovery works correctly

### Running Tests

```bash
# Run only unit tests (fastest)
make test-unit

# Run integration tests
make test-integration

# Run all tests with coverage report
make test-coverage

# Run all tests
make test-all
```

### Test Coverage Goals

The project aims for high test coverage in critical areas:

- Core GPU optimization logic: >90% coverage
- Memory management system: >85% coverage
- Command generation: >80% coverage
- Event system: >85% coverage
- Error handling: >90% coverage

The comprehensive test suite ensures the application remains stable and reliable, even as new features are added or components are refactored.
