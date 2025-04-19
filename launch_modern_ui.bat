@echo off
REM Launch script for the Modern UI of DualGPUOptimizer
REM This checks for the icon and ensures it's in the correct location before launching

echo Checking for icon file...

IF EXIST integrated_app\dualgpuopt\assets\windowsicongpu.ico (
    echo Found icon in integrated_app, copying to assets...
    copy /Y integrated_app\dualgpuopt\assets\windowsicongpu.ico dualgpuopt\assets\ > nul
) ELSE IF EXIST dual_gpu_optimizer\dualgpuopt\assets\windowsicongpu.ico (
    echo Found icon in dual_gpu_optimizer, copying to assets...
    copy /Y dual_gpu_optimizer\dualgpuopt\assets\windowsicongpu.ico dualgpuopt\assets\ > nul
)

echo Launching DualGPUOptimizer Modern UI...
python run_modern_ui.py 