# Packaging DualGPUOptimizer

This document provides instructions for packaging DualGPUOptimizer into a standalone executable using PyInstaller.

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