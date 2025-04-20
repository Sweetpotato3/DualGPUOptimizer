@echo off
REM Direct application launcher for DualGPUOptimizer
REM This batch file launches the direct application entry point
REM which provides a full-featured interface with event-driven architecture

echo ===================================================
echo DualGPUOptimizer - Direct Launcher with Event System
echo ===================================================
echo.
echo This launcher provides:
echo - Simple startup without complex imports
echo - Event-driven architecture for component communication
echo - Tabbed interface with multiple features:
echo   * GPU Dashboard with real-time metrics and visualizations
echo   * Optimizer for calculating GPU memory splits
echo   * Command generation for LLM frameworks
echo - Enhanced visualization with progress bars
echo - Temperature and power monitoring with alerts
echo - Advanced metrics including PCIe bandwidth and clock speeds
echo - Status bar showing real-time event information
echo.
echo Starting application...
echo.

REM Check if Python is in PATH
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python not found in PATH. Please install Python and add it to your PATH.
    pause
    exit /b 1
)

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

REM Launch the direct application
python run_direct_app.py

echo.
echo Application closed.
pause 