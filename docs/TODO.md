# DualGPUOptimizer TODO List

This document outlines specific tasks for improving the DualGPUOptimizer project.

## Code Cleanup

- [ ] Fix trailing whitespace issues in:
  - `dualgpuopt/ctx_size.py`
  - `dualgpuopt/gui/theme.py`
  - `dualgpuopt/gui/dashboard.py`
  - `dualgpuopt/model_profiles.py`
- [ ] Standardize indentation across all files (4 spaces)
- [ ] Ensure consistent line endings (LF)
- [ ] Remove unused imports
- [ ] Fix SyntaxWarnings in third-party dependencies

## Improved Error Handling

- [ ] Fix import errors related to `calc_max_ctx` function
- [ ] Add fallback mechanisms when advanced optimization modules are not available
- [ ] Implement better error reporting in the GUI
- [ ] Create descriptive error messages for common issues
- [ ] Add logging for all critical errors with detailed context
- [ ] Implement graceful failures for missing PyTorch/CUDA

## Additional Model Profiles

- [ ] Add profiles for Llama 3 models (8B, 70B)
- [ ] Add profiles for Phi-3 models
- [ ] Add profiles for Claude-optimized models
- [ ] Update existing models with more accurate memory estimates
- [ ] Add profiles for specialist models (e.g., code models, vision models)
- [ ] Add support for multi-modal models

## Enhanced Memory Management

- [ ] Implement more aggressive VRAM optimization techniques
- [ ] Add tiered recovery mechanisms for out-of-memory conditions
- [ ] Improve memory monitoring precision
- [ ] Add memory visualization in dashboard
- [ ] Implement dynamic batch size adjustment based on memory pressure
- [ ] Create memory presets for different use cases

## Advanced Layer Balancing

- [ ] Improve algorithms for layer distribution across heterogeneous GPUs
- [ ] Implement better weight distribution for uneven GPU setups
- [ ] Add profile-based performance optimization for specific model architectures
- [ ] Create visualizations for layer distribution
- [ ] Implement custom device maps for complex models
- [ ] Support more than two GPUs for very large models

## Documentation Improvements

- [ ] Create API documentation for all public functions
- [ ] Add usage examples for common scenarios
- [ ] Create troubleshooting guide for common issues
- [ ] Add architecture diagram explaining component interactions
- [ ] Create video tutorials for key features
- [ ] Improve in-app help functionality
- [ ] Document advanced configuration options

## Build and Deployment

- [ ] Fix PyInstaller warnings
- [ ] Reduce executable size by optimizing included dependencies
- [ ] Add automatic update checking
- [ ] Create installer package for easier deployment
- [ ] Add compatibility checks for different CUDA versions
- [ ] Improve startup time
- [ ] Add detailed version information

## Testing

- [ ] Create comprehensive test suite covering core functionality
- [ ] Add integration tests for GUI components
- [ ] Implement performance benchmarks
- [ ] Add testing for different GPU configurations
- [ ] Create mock GPU environment for testing without hardware
- [ ] Add stress tests for memory handling

## User Experience

- [ ] Improve theme consistency
- [ ] Add dark/light mode toggle
- [ ] Create more intuitive workflow for new users
- [ ] Add tooltips and help buttons
- [ ] Improve status reporting during long operations
- [ ] Create wizard for first-time setup 