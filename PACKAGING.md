# DualGPUOptimizer Packaging Guide

This document describes how to package the DualGPUOptimizer application into a standalone executable using PyInstaller.

## Requirements

- Python 3.13+
- PyInstaller 6.13.0+
- All required dependencies installed in your environment

## Known Issues and Solutions

The packaging process encounters two main issues:

1. **PyInstaller + PyTorch integration**: PyInstaller's analysis phase has issues with torch modules, especially the `torch._inductor` and `torch._dynamo` modules which generate code on-the-fly or require CUDA tools during import.

2. **Missing Module Error**: When running with the `--mock` flag, there was an import error for the `dualgpuopt.gui.constants` module.

## Solution

The `build_no_hook.py` script bypasses the built-in PyInstaller hooks for torch and creates a custom minimal hook that:

1. Avoids collecting problematic torch modules like `torch._inductor` and `torch._dynamo`.
2. Includes only the essential torch modules needed by the application.
3. Manually copies required torch DLLs to the distribution directory.
4. Includes all GUI constants and assets.

## Build Steps

1. Make sure all dependencies are installed:
    ```
    pip install -r requirements.txt
    ```

2. Run the build script:
    ```
    python build_no_hook.py
    ```

3. The executable and all required files will be created in the `dist/DualGPUOptimizer` directory.

## Testing the Build

To test the built application with mock GPU data:
```
dist\DualGPUOptimizer\DualGPUOptimizer.exe --mock
```

To run the built application with real GPU data:
```
dist\DualGPUOptimizer\DualGPUOptimizer.exe
```

## Advanced: How It Works

The build script performs the following key steps:

1. Creates a temporary directory with custom hooks that override the built-in hooks.
2. Uses PyInstaller to build the application with these custom hooks.
3. Manually copies necessary torch DLLs to the distribution directory.
4. Includes all necessary assets and presets folders.

### Custom Hooks
The custom hook for torch:
```python
# Minimal torch hook
hiddenimports = [
    'torch', 
    'torch.cuda',
]
excludedimports = [
    'torch._dynamo',
    'torch._inductor',
    'torch._functorch',
    'torch.distributed',
    'torch.testing',
    'torch.utils.tensorboard',
]
```

## Troubleshooting

If you encounter issues with the build:

1. **Missing DLLs**: Make sure your environment has all necessary dependencies installed.
2. **Path Issues**: Verify that all paths in the build script are correct for your environment.
3. **CUDA Issues**: If you need CUDA functionality, you may need to manually copy additional CUDA DLLs.

## Distribution

The built application is a directory containing:
- `DualGPUOptimizer.exe` - The main executable
- `_internal/` - Directory containing Python modules and resources
- `torch/lib/` - Directory containing torch DLLs

## Prerequisites

- Python 3.12 or higher
- PyInstaller (`pip install pyinstaller`)
- A properly set up development environment (run `setup_dev_environment.ps1` if needed)

## Adding an Icon

Before packaging, you should add an application icon to enhance the professional appearance:

1. Create an icon file (ICO format for Windows)
2. Save it to `dual_gpu_optimizer/dualgpuopt/assets/app_icon.ico`

## Building the Package

### Using the Spec File (Recommended)

We've included a PyInstaller spec file that's already configured for the application. To build using this spec file:

```powershell
pyinstaller dual_gpu_optimizer_app.spec
```

This will create a `dist/DualGPUOptimizer` directory containing the packaged application.

### Manual Build (Alternative)

If you need to customize the build, you can run PyInstaller directly:

```powershell
pyinstaller --name="DualGPUOptimizer" --windowed --icon=dual_gpu_optimizer/dualgpuopt/assets/app_icon.ico --add-data="dual_gpu_optimizer/dualgpuopt/assets;dualgpuopt/assets" dual_gpu_optimizer/dualgpuopt/__main__.py
```

## Testing the Package

After building, test the packaged application by running:

```powershell
./dist/DualGPUOptimizer/DualGPUOptimizer.exe
```

Verify that:
- The application starts correctly
- The GUI appears
- GPU detection works properly
- All features function as expected

## Distribution

To distribute the application:

1. Compress the entire `dist/DualGPUOptimizer` directory into a ZIP file
2. Optionally, create an installer using a tool like NSIS or Inno Setup
3. Distribute to users

## Troubleshooting

If the packaged application doesn't work correctly:

1. Try running with console enabled to see error messages:
   ```
   pyinstaller --name="DualGPUOptimizer" --console --icon=dual_gpu_optimizer/dualgpuopt/assets/app_icon.ico dual_gpu_optimizer/dualgpuopt/__main__.py
   ```

2. Check for missing dependencies in the hidden imports section of the spec file

3. Ensure all required assets are included in the `datas` section of the spec file

4. Verify that the application works correctly when run from source (`python -m dualgpuopt`)

## System Requirements for End Users

- Windows 10 or higher
- NVIDIA drivers installed (for real GPU detection)
- At least 2 NVIDIA GPUs recommended (can run in mock mode with fewer) 