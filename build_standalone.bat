@echo off
echo Building DualGPUOptimizer executable...
python build_exe.py
if %ERRORLEVEL% NEQ 0 (
    echo Build failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)
echo.
echo Build completed successfully!
echo The executable can be found in the dist\DualGPUOptimizer directory.
pause
