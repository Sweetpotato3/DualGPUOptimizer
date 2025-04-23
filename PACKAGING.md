# DualGPUOptimizer Packaging Guide

This document describes how to package the DualGPUOptimizer application into a standalone executable using PyInstaller.

## Requirements

- Python 3.13+
- PyInstaller 6.13.0+
- All dependencies installed in your environment (see requirements.txt)

## Quick Start

The simplest way to build the application is:

```powershell
# Run the build and verification script
.\build_and_verify.ps1
```

This will:
1. Ensure dependencies are installed
2. Build the application using our optimized spec file
3. Run verification tests to ensure the build works correctly

The built application will be in `dist/DualGPUOptimizer/`.

## Known Issues and Solutions

The packaging process addresses three main issues:

1. **PyInstaller + PyTorch integration**: PyInstaller's analysis phase has issues with torch modules, especially `torch._inductor` and `torch._dynamo` modules which generate code on-the-fly or require CUDA tools during import.

2. **Missing Module Error**: The GUI constants module needs to be explicitly included in the build.

3. **Missing DLLs**: CUDA/MKL libraries from the torch wheel's internal .libs directory need to be manually copied.

## How Our Solution Works

Our build system uses a custom approach that:

1. **Custom Hook for PyTorch**: A specialized hook in `hooks/hook-torch.py` that excludes problematic modules while still collecting all required functionality.

2. **Package Data Collection**: The build.spec file uses `collect_data_files('dualgpuopt.gui')` to ensure constants.py and other data files are included.

3. **Binary Collection**: We use `collect_dynamic_libs("torch")` to find and include all necessary CUDA/MKL DLLs.

4. **Defensive Programming**: We've added fail-fast error handling that provides clear error messages if anything is missing.

5. **Build Verification**: A test script checks the build for common issues before distribution.

## Build Types

### Directory Build (Default)

The default build produces a directory containing the executable and all required files. This is more reliable for large applications with many dependencies like DualGPUOptimizer:

```powershell
pyinstaller build.spec
```

### Single-File Build (Optional)

If you need a single executable file, you can use:

```powershell
pyinstaller build.spec --onefile --add-data "%TORCH_HOME%;torch.libs" --collect-submodules torch
```

Note that this produces a larger file and may take longer to start up.

## Testing the Build

You can test the built application in several ways:

1. **Mock Mode**: Run without real GPU detection
   ```powershell
   .\dist\DualGPUOptimizer\DualGPUOptimizer.exe --mock
   ```

2. **Real Mode**: Run with actual GPU detection
   ```powershell
   .\dist\DualGPUOptimizer\DualGPUOptimizer.exe
   ```

3. **CLI Mode**: Run in command-line mode
   ```powershell
   .\dist\DualGPUOptimizer\DualGPUOptimizer.exe --cli
   ```

## Troubleshooting

If you encounter issues:

1. **Build Failures**: Look for specific error messages mentioning missing modules or files.

2. **Runtime Errors**: Run with the `--verbose` flag to see detailed logging:
   ```powershell
   .\dist\DualGPUOptimizer\DualGPUOptimizer.exe --verbose
   ```

3. **Missing GUI**: Check that all GUI constants and assets are properly collected in the build.

4. **Missing DLLs**: Ensure PyInstaller is collecting all necessary DLLs, especially for CUDA support.

## Distribution

Once built and verified, you can distribute the application in several ways:

1. **Directory**: Zip the entire `dist/DualGPUOptimizer/` directory.

2. **Installer**: Use NSIS or Inno Setup to create a Windows installer.

## Advanced: Technical Details

Our solution works through these key elements:

1. **Exclusion Pattern**: We identify and exclude torch modules that cause PyInstaller to crash.

2. **Recursive Import Prevention**: The custom hook avoids recursive imports that lead to stack overflows.

3. **Dynamic Library Collection**: We ensure all required DLLs are included, not just Python modules.

4. **Package Structure Preservation**: We maintain the package structure so imports work correctly.

5. **Import Guards**: Early detection of missing modules prevents confusing errors deep in the call stack.

This approach produces a reliable, reproducible build that works across different development environments.

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
