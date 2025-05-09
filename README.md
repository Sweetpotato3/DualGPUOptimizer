# DualGPUOptimizer

DualGPUOptimizer is a specialized application for managing and optimizing dual GPU setups, particularly focused on machine learning workloads.

## Features

- **GPU Monitoring**: Real-time monitoring of GPU metrics including memory usage, utilization, temperature, and power consumption via efficient, signal-based updates.
- **Simplified Alert System**: Clear **WARNING** and **CRITICAL** alerts integrated with system tray notifications and a status bar badge.
- **Unified Model Engine**: Automatically detects model format (`gguf`, `awq`, HF Transformers) and uses the appropriate backend (llama.cpp, vLLM, Transformers) via a single `Engine` interface.
- **Unified Preset System**: Manage model configurations, prompt templates, and personas through a single JSON-based preset system accessible via a dedicated dock widget.
- **Execution Management**: Controls and monitors model execution using the unified engine.
- **Advanced Tools Dock**: Optional, hideable dock containing advanced diagnostic tools like the Memory Timeline, keeping the main interface clean.
- **GPU Telemetry**: Collects detailed GPU performance metrics without UI polling.
- **Model Optimization**: Calculates optimal GPU split ratios for large language models
- **Smart Layer Distribution**: Balances model layers across multiple GPUs based on available memory
- **Enhanced Memory Profiling**: Interactive memory timeline with zooming, filtering, and event markers
- **Advanced Chart Functionality**: Export capabilities, timeline markers, and zoom controls
- **Direct Settings Application**: One-click transfer of optimal settings from Optimizer to Launcher
- **Configuration Presets**: Save and load optimized configurations for quick reuse
- **Enhanced Alert System**: Multi-level GPU alert classification with priority-based notifications
- **Telemetry History**: Historical metrics storage with time-based filtering capabilities
- **Improved Event System**: Robust typed events for GPU telemetry with enhanced testing support
- **Thread-Safe Caching System**: High-performance caching for memory-intensive operations with comprehensive monitoring

## Recent Improvements

### Hot-Swapping Engine Pool (2025)

- **LRU Model Cache**: Keeps up to two models in memory for instant switching between frequently used models
- **Automatic Health Monitoring**: Periodically checks model health and automatically restarts crashed backends
- **Alert Integration**: Publishes CRITICAL alerts through the event system when backends need to be restarted
- **Zero-Latency Model Switching**: Switching between cached models happens instantly, eliminating wait times
- **Thread-Safe Implementation**: All operations are thread-safe with proper synchronization and lock-free health checks
- **Backend-Specific Health Probes**: Custom health checks for each backend type (vLLM, llama.cpp, HuggingFace)
- **Background Loading**: Model loading operations run in a separate thread pool to avoid blocking the UI
- **Graceful Shutdown**: Proper cleanup of resources during application exit via atexit handlers
- **Seamless Integration**: Simply replace `Engine()` with `EnginePool.get(model_path, **kwargs)`
- **Cache Monitoring**: UI dock widget for real-time monitoring and management of cached models
- **Global Exception Handling**: System-wide exception catching with user-friendly error dialogs
- **Performance Metrics**: Optional Prometheus integration for tracking cache hits, load times, and health status
- **Benchmark Database**: Thread-safe SQLite database with WAL journaling for performance tracking

The Engine Pool makes it possible to instantly switch between different models and personas without waiting for models to load, significantly improving the user experience. It also automatically recovers from model crashes, enhancing system stability.

### Engine Pool Enhancements (2025 Update)

The Engine Pool system has been enhanced with several critical improvements:

#### Enhanced Thread Safety

- **Lock-Free Health Checks**: Health verification occurs outside critical sections to prevent blocking
- **Careful Lock Hierarchy**: Avoids deadlocks when checking model health during eviction
- **Thread-Local Metrics Updates**: Lock isolation for statistical updates from health checks
- **Atomic Operations**: Where appropriate, atomic counters replace lock-guarded integers

#### Improved Cache Management

- **Real-Time Cache Monitor**: New Qt dock widget visualizes current model caching status
- **Manual Eviction Controls**: Directly evict specific models from the UI when needed
- **Auto-Refreshing View**: Automatically updates every 2.5 seconds with current cache state
- **Leak Prevention**: Proper widget cleanup to prevent memory leaks during refreshes

#### Robust Error Handling

- **Global Exception Dialog**: System-wide exception handler catches and displays errors in dialogs
- **Health-Based Recovery**: Automatic unloading and reloading of unhealthy models
- **Progressive Fault Tolerance**: Models are only restarted after multiple consecutive failures
- **Graceful Application Exit**: Proper cleanup of all resources during shutdown

#### Performance Tracking

- **WAL-Mode Database**: Thread-safe SQLite database using Write-Ahead Logging
- **Connection Pooling**: Single global connection with proper locking
- **Benchmark History**: Tracks model performance metrics across sessions
- **Safe Label Handling**: Prometheus metrics use sanitized model names as labels

#### Production-Grade Metrics

- **Conditional Prometheus Server**: Only starts when explicitly enabled via environment variable
- **Clean Label Handling**: Sanitizes and truncates model paths for metric labels
- **Delta-Based Updates**: Efficient counter updates tracking only changes
- **Resource Usage Monitoring**: Tracks cache size, hit rates, and memory usage

These enhancements make the Engine Pool robust enough for extended production use, with proper resource management, error recovery, and performance monitoring.

### Streamlined Architecture (Refactor 2024)

- **Signal-Based Telemetry System**: Migrated from event-based telemetry to a Qt Signal-based architecture for GPU metric updates (util, VRAM, temp, power). This reduces CPU usage, improves UI responsiveness, and provides real-time updates without polling.
- **Simplified Alert System**: Streamlined from four tiers to two essential levels (**WARNING** and **CRITICAL**), directly integrated with the status bar badge and system tray notifications.
- **Unified Preset Management**: Consolidated separate systems for model configurations, personas, and templates into a single JSON-based preset format managed via a dedicated dock widget (`~/.dualgpuopt/presets/`).
- **Advanced Tools Dock**: Moved diagnostic tools like the Memory Timeline into a separate, hideable dock widget accessible via the "View" menu, decluttering the main interface.
- **Unified Backend Engine**: Replaced separate command generation with a single `Engine` class that auto-detects model types and manages the appropriate backend, simplifying model loading and execution.

### Implementation Details

The refactored architecture introduces several key implementation improvements:

#### Signal-Based GPU Monitoring

- **Efficient Qt Signals**: Each GPU metric (utilization, VRAM, temperature, power) is updated via dedicated Qt signals
- **Reduced CPU Usage**: Eliminated polling loops in favor of event-driven updates
- **Improved Responsiveness**: UI components connect directly to telemetry signals for immediate updates
- **Thread Safety**: Worker thread handles GPU communication while UI thread processes signals

#### Direct UI Component Communication

- **Memory Timeline Sharing**: Memory Timeline component shared between Memory Profiler tab and Advanced Tools dock
- **Engine Integration**: Unified Engine provides model operations directly to the Launcher tab
- **Alert Propagation**: Alert Service directly updates status bar and system tray through Qt signals
- **Preset System**: Centralized preset management with access from all tabs

#### Hybrid Communication Architecture

The application utilizes a hybrid communication approach:

- **Core Telemetry (GPU Metrics):** Uses direct Qt Signals (`util_updated`, `vram_updated`, etc.) emitted by `TelemetryWorker` for optimal performance and responsiveness.
- **Other Communication:** Uses the Event Bus for less frequent or broader messages like configuration changes, preset loading requests, or complex state updates.

This balances performance for high-frequency data with the flexibility of an event bus for other system communication.

### Thread-Safe Caching System

We've implemented a comprehensive thread-safe caching system to optimize performance across the application:

- **Optimized Memory Calculations**: Significant performance improvements for memory-intensive operations:

  - Up to 1000x speedup for recursive calculations like optimization algorithms
  - 90%+ cache hit ratios in real-world usage scenarios
  - Thread-safe operation with proper synchronization

- **Two Specialized Cache Decorators**:

  - `thread_safe_cache`: For global functions with shared cache
  - `method_cache`: Specifically designed for class methods with instance-specific caching

- **Memory-Efficient Implementation**:

  - True LRU (Least Recently Used) eviction policy
  - Automatic cache size management to prevent memory bloat
  - Proper memory cleanup to prevent leaks

- **Comprehensive Statistics**:

  - Hit/miss ratio tracking for performance optimization
  - Cache usage analytics for tuning cache sizes
  - Per-cache monitoring for targeted optimization

- **Memory Usage Reduction**:
  - Significant memory savings through intelligent caching
  - Reduced pressure on garbage collection
  - More efficient use of GPU memory during model execution

The caching system is used throughout memory prediction, batch calculation, and optimization modules to dramatically improve performance while maintaining thread safety in multi-threaded environments.

### Enhanced Event Bus System

We've significantly improved the event bus system used for component communication:

- **Universal Subscribe Method**: Simplified subscription API that accepts both class types and string event names
- **Enhanced Event Type Support**: Improved handling of event class hierarchies for better type safety
- **Test-Friendly Events**: Added specialized event classes for testing with rich metrics dictionaries
- **Backward Compatibility**: Maintained compatibility with existing event consumers
- **GPU Metrics Event Enhancement**: Added support for comprehensive GPU metrics data in events
- **Thread-Safe Event Distribution**: Improved synchronization for concurrent event publishing
- **Event Priority System**: Ensures critical events are processed before less important ones
- **Robust Error Handling**: Better isolation of error handling between event handlers

The enhanced event system provides a more robust foundation for component communication throughout the application, improving reliability and testability of the GPU monitoring and telemetry subsystems.

### Advanced GPU Alert System

We've implemented a comprehensive alert system for GPU monitoring:

- **Two-Tier Alert Classification**:
  - WARNING: Approaching thresholds (e.g., 75% memory, 70°C)
  - CRITICAL: Threshold exceeded (e.g., 90% memory, 80°C)
- **Composite Alert Detection**: Combines multiple metrics (memory, temperature, power) for accurate risk assessment.

The enhanced alert system provides earlier warnings of potential issues and more accurate classification of GPU conditions, helping prevent out-of-memory errors and thermal throttling.

### Telemetry History Functionality

We've added comprehensive telemetry history tracking:

- **Rolling 60-Second History**: Maintains a complete 60-second history of all GPU metrics
- **Time-Window Filtering**: Retrieve metrics from specific time windows (e.g., last 30 seconds)
- **GPU-Specific History**: Access historical data for individual GPUs or all GPUs
- **Memory-Optimized Storage**: Efficient storage with automatic trimming to prevent memory leaks
- **Thread-Safe Implementation**: Concurrent access support for history data across components

The telemetry history enables more sophisticated trend analysis, pattern detection, and visualization of GPU performance over time.

### Improved Telemetry Memory Management

We've optimized the telemetry system's memory usage:

- **Enhanced LRU Cache Controls**: Implemented type-safe caching with optimized cache sizes
- **Automatic History Trimming**: Prevents unbounded growth of historical data
- **Fixed Memory Leaks**: Addressed potential memory leaks in long-running telemetry processes
- **Optimized Thread Synchronization**: Reduced lock contention in multi-component access patterns
- **Circular Buffer Implementation**: Efficient storage for high-frequency metric collection

These optimizations ensure stable performance even during extended monitoring sessions, particularly important for long-running model inference processes.

### Simplified Settings Application Workflow

We've significantly improved the workflow for generating and applying optimal GPU settings:

- **Configuration Presets**: Save and load optimized configurations for quick reuse through the unified preset system
- **Parameter Validation**: Smart validation ensures applied settings are compatible with the current environment
- **Comprehensive Parameters**: Automatically transfers all relevant settings including context sizes, GPU splits, and precision settings

### Configuration Preset System

The unified preset system allows you to save and reuse optimized configurations:

- **Named Presets**: Save configurations with custom names (.json files in `~/.dualgpuopt/presets/`)
- **One-Click Loading**: Load entire configurations via the Preset Dock (double-click)
- **Persistent Storage**: Presets are saved between application sessions
- **Combined Parameters**: Presets now store model path, prompt template, persona, and GPU settings together
- **Easy Management**: Create, delete, and refresh presets directly from the dock toolbar

The preset system makes it simple to switch between different model configurations without reconfiguring settings each time.

### Enhanced Memory Profiling System

We've significantly enhanced the memory profiling system with the following features:

- **Interactive Memory Timeline**: Zoom in/out, pan, and filter time periods for detailed analysis
- **Timeline Markers**: Add custom markers to annotate important events in the memory timeline
- **Time-Based Filtering**: Filter memory data by time periods (30 seconds, 1 minute, 5 minutes, or all data)
- **Pattern Analysis**: Sophisticated detection of memory usage patterns with severity indicators
- **Memory Usage Recommendations**: Actionable recommendations based on detected memory patterns
- **GPU Memory Comparison**: Visual comparison of memory usage between GPUs with efficiency metrics
- **Interactive Zooming**: Click and drag on the chart to zoom into specific time periods
- **Extended Export Capabilities**: Export memory data as CSV or chart images as PNG/PDF

The enhanced Memory Profiler provides a more comprehensive toolset for diagnosing memory issues and optimizing memory usage in large language models.

### Enhanced Chart Functionality

We've added significant enhancements to all charts throughout the application:

- **Interactive Zoom Controls**: Zoom in/out and reset buttons for all charts
- **Timeline Markers**: Add custom event markers to correlate events with metric changes
- **Export Capabilities**: Export chart data as CSV or images as PNG
- **Auto-Scaling**: Automatic Y-axis scaling based on displayed data
- **Improved Visibility**: Better labeling and axis formatting for clearer data visualization
- **Chart Filtering**: Show/hide specific data series on charts
- **Interactive Selection**: Click and drag to zoom into specific regions of charts

These chart enhancements enable more detailed analysis and easier sharing of performance data.

### Pattern Analysis for Memory Usage

The Memory Profiler now includes sophisticated pattern analysis capabilities:

- **Memory Imbalance Detection**: Identifies uneven memory distribution between GPUs
- **Growth Pattern Analysis**: Detects steady memory growth indicating potential leaks
- **Efficiency Metrics**: Calculates memory efficiency in terms of tokens processed per GB
- **Fragmentation Detection**: Identifies patterns suggesting memory fragmentation
- **Severity Classification**: Categorizes issues by severity (high, medium, low)
- **Actionable Recommendations**: Provides specific recommendations for each detected pattern
- **Priority-Based Reporting**: Groups recommendations by priority for efficient issue resolution

These new analysis capabilities help users optimize their models for better memory efficiency.

### Qt-Based Interface Migration

We've completed a comprehensive migration to a Qt-based interface with the following benefits:

- **Modern UI Design**: Clean, intuitive interface with consistent styling and improved layout
- **Enhanced Data Visualization**: Real-time charts for historical GPU metrics and performance tracking
- **System Tray Integration**: Minimize to system tray with notifications for critical events
- **Settings Panel**: Configurable application preferences with theme selection
- **Improved Stability**: More robust UI components with better error handling
- **Enhanced Multi-Monitor Support**: Better high DPI screen handling and scaling
- **Streamlined Dependencies**: Simplified dependencies, replacing multiple Tkinter add-ons with PySide6

The new Qt-based interface provides a significantly improved user experience while maintaining all the functionality of the original application.

### Memory Profiling System

We've added a comprehensive memory profiling system with the following features:

- **Memory Timeline Visualization**: Real-time visualization of GPU memory usage during inference
- **Memory Leak Detection**: Identifies potential memory leaks during and after model inference
- **Pattern Analysis**: Detects unusual memory growth patterns and allocation spikes
- **Inference Session Tracking**: Records memory usage specific to inference sessions
- **Actionable Reports**: Provides recommendations based on memory usage analysis
- **CSV Export**: Exports memory timeline data for external analysis

The Memory Profiler is accessible through the Advanced Tools dock and helps optimize memory usage for large language models by identifying inefficient memory patterns.

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

## Enhanced Dependency Management System

DualGPUOptimizer now features a robust dependency management system that:

- **Gracefully Handles Missing Dependencies**: The application will run even with minimal dependencies, falling back to basic functionality
- **Auto-Detects Available Modules**: Identifies which optional features can be enabled based on installed packages
- **Provides Clear Installation Instructions**: Shows exactly what to install to enable specific features
- **Supports Command-Line Installation**: Run `python -m dualgpuopt --install-deps` to install missing dependencies
- **Includes Fallback UI**: A minimal UI will run even when optional UI packages are unavailable

The dependency system categorizes dependencies into:

- **Required**: Application won't start without these (e.g., PySide6)
- **Core**: Application works with fallbacks if missing (e.g., pynvml, numpy)
- **Optional**: Enhanced functionality when available (e.g., torch)

## Enhanced Error Handling & Recovery System

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

## Complete Qt-Based Interface

The Qt-based interface features a full-featured tabbed layout with:

### Dashboard Tab

- Real-time GPU metrics visualization with progress bars
- Temperature monitoring with color-coded warnings
- Power usage tracking with limit indicators
- PCIe bandwidth monitoring
- GPU clock speed visualization
- Memory reset capabilities
- Historical metrics charts with selectable metrics

### Optimizer Tab

- Model selection via preset loading
- Automatic GPU memory split ratio calculation
- Context length optimization
- Model parameter configuration managed within presets
- Command generation handled internally by the unified `Engine`

### Memory Profiler (Advanced Tools Dock)

- Memory timeline visualization
- Leak detection with pattern analysis
- Memory session tracking
- Detailed memory statistics
- **Note: This is now located in the "Advanced Tools" dock, hidden by default.**

### Launcher Tab

- Model execution interface
- Process monitoring and management
- Command-line output display
- Environment variable configuration

### Settings Tab

- Theme selection and customization
- Application behavior configuration
- Notification preferences
- Directory and path settings

All tabs feature graceful fallbacks when components are unavailable, ensuring the application can run in any environment while providing helpful guidance for enabling full functionality.

## Environment Variable Configuration

DualGPUOptimizer now supports configuration through environment variables:

| Variable                       | Description                          | Default     |
| ------------------------------ | ------------------------------------ | ----------- |
| `DUALGPUOPT_MOCK_GPU`          | Force mock GPU mode                  | `false`     |
| `DUALGPUOPT_GPU_COUNT`         | Override detected GPU count          | Auto-detect |
| `DUALGPUOPT_POLL_INTERVAL`     | Telemetry polling interval (seconds) | `1.0`       |
| `DUALGPUOPT_MOCK_TELEMETRY`    | Force mock telemetry data            | `false`     |
| `DUALGPUOPT_MAX_RECOVERY`      | Maximum recovery attempts            | `3`         |
| `DUALGPUOPT_SYSTEM_OVERHEAD`   | System memory overhead (MB)          | `2048`      |
| `DUALGPUOPT_SAFETY_MARGIN`     | Memory safety margin                 | `0.1`       |
| `DUALGPUOPT_TP_OVERHEAD`       | Tensor parallelism overhead          | `0.2`       |
| `DUALGPUOPT_KV_CACHE_FACTOR`   | KV cache size multiplier             | `2.0`       |
| `DUALGPUOPT_MIN_CONTEXT`       | Minimum context size                 | `128`       |
| `DUALGPUOPT_METRIC_CACHE_TTL`  | Metrics cache lifetime (seconds)     | `0.05`      |
| `DUALGPUOPT_OPT_CACHE_TIMEOUT` | Optimizer cache timeout (seconds)    | `30`        |
| `DUALGPUOPT_PROFILE_CACHE`     | Memory profile cache size            | `64`        |
| `DUALGPUOPT_METRICS_PORT`      | Prometheus metrics server port       | `0` (off)   |

## New: Test System Enhancements

We have significantly improved the testing infrastructure to ensure stability and correctness:

### Successfully Implemented Testing Categories

- **Property-Based Testing**: Comprehensive Hypothesis-based tests verify optimizer algorithms across random inputs
- **Telemetry Unit Tests**: Detailed verification of GPU metrics collection, alert levels, and history management
- **Alert System Tests**: Validated multi-tier alert classification system with complex condition handling
- **VRAM Resource Planning**: Tests for optimal model placement across VRAM, RAM, and disk with various GPU configurations
- **Backend Command Generation**: Verification of correct command-line flags for different model backends
- **HuggingFace Download Integrity**: Tests for file download resumption and SHA-256 checksum verification

### Import Structure Optimization

- Fixed import paths in integration and unit tests to match current module structure
- Adapted test stubs to use available classes and methods rather than outdated interfaces
- Restructured test dependencies for better modularity and isolation

### Test Coverage Improvements

- Core optimizer module: Testing for split configurations, context sizing, and cache consistency
- Telemetry system: Verification of metrics collection, alert levels, and historical data management
- Alert classification: Validation of threshold detection for memory, temperature, and power metrics
- Model execution backends: Verification of correct flags for llama.cpp and vLLM backends
- VRAM fitting algorithms: Testing of GPU memory allocation and offloading strategies
- Download safety: Validation of checksum verification during model downloads

### Lean Test Implementation

The testing infrastructure is designed for speed and reliability:

- **Mock-Based Testing**: All tests run offline without GPU or network dependencies
- **Sub-Second Execution**: Each test suite executes in milliseconds, not seconds
- **No Subprocess Spawning**: Backend processes are mocked rather than launched
- **Simulation-Based Coverage**: Tests use simulated environments to validate all code paths
- **Focused Test Scope**: Each test validates exactly one component with minimal dependencies

### Next Steps for Testing

We're continuing to enhance the test suite with these upcoming improvements:

1. **Event System Testing**: Complete integration tests for the event bus system and event priorities
2. **Mock GPU Enhancements**: Better simulation of GPU hardware for testing without physical devices
3. **Memory Prediction Testing**: Improved tests for memory usage projections with different model types
4. **Stress Testing**: Simulation of high load and error conditions to verify recovery mechanisms

These testing enhancements provide better validation of core functionality, ensuring reliability during model execution and preventing potential memory or performance issues.

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
- `psutil`: For system resource monitoring
- `numpy`: For optimization algorithms
- `PySide6`: For the Qt-based UI framework (new requirement)

### Optional Dependencies

- `torch`, `torchvision`, and `torchaudio`: For advanced GPU features

The application will function with graceful fallbacks when optional dependencies are missing.

## Usage

### Running the Qt Application

To run the new Qt-based interface:

```
python run_qt_app.py
```

To run in mock mode (no GPU required):

```
python run_qt_app.py --mock
```

### Module-Based Approach

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

# For Qt UI
pip install PySide6==6.5.2

# For advanced GPU features
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1
```

### Application Not Starting

If the application fails to start:

1. Try running with verbose logging: `python run_qt_app.py --verbose`
2. Check the logs in the `logs` directory for specific errors
3. Verify dependencies are installed: `python install_deps.py --check`

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
3. For testing, use mock mode: `DUALGPUOPT_MOCK_GPU=1 python run_qt_app.py`

## Development

### Project Structure

- `dualgpuopt/`: Main package directory
  - `gpu/`: GPU monitoring and information modules
  - `qt/`: Qt UI components for the new interface
  - `gui/`: Legacy GUI components and widgets
  - `ui/`: UI compatibility layers
  - `services/`: Background services (telemetry, alerts, presets)
  - `batch/`: Batch processing logic
  - `memory/`: Memory management and monitoring
  - `engine/`: Unified engine for model execution
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

### Telemetry System Improvements

- **Fixed Memory Leaks**: Addressed potential memory leaks in telemetry caching system
- **Added Alert System**: Implemented multi-level alert classification for GPU events
- **Enhanced History Storage**: Added 60-second history buffer with time-based filtering
- **Improved Test Coverage**: Added comprehensive tests for telemetry functionality

These improvements create a more stable foundation, enabling the application to run in a wider range of environments with better error recovery.

## Quick Start

To quickly get started with DualGPUOptimizer:

1. **Install dependencies**:

```bash
pip install PySide6==6.5.2 pynvml psutil numpy
```

2. **Run the application**:

```bash
# With real GPU monitoring (requires NVIDIA GPUs)
python run.py

# In mock mode (no real GPUs required for testing)
python run.py --mock
```

3. **Using the interface**:
   - The **Dashboard** tab shows real-time GPU metrics
   - The **Optimizer** tab calculates memory splits for models
   - The **Launcher** tab controls model execution
   - The **View > Advanced Tools** menu reveals the memory timeline and advanced diagnostics
   - The **View > Engine Pool** option shows the model cache monitor for managing loaded models

For developers, you can also run directly with:

```bash
python run_qt_app.py --mock --verbose
```

For Prometheus metrics, set the environment variable before running:

```bash
# Linux/macOS
export DUALGPUOPT_METRICS_PORT=9090
python run.py

# Windows
set DUALGPUOPT_METRICS_PORT=9090
python run.py
```
