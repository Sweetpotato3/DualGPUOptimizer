@echo off
echo Building DualGPUOptimizer Modern UI executable...
python build_modern_app.py

if not exist dist\DualGPUOptimizer.exe (
  echo Build failed or executable not found!
  pause
  exit /b 1
)

echo.
echo Build successful! Running the application...
echo.
start "" "dist\DualGPUOptimizer.exe" 