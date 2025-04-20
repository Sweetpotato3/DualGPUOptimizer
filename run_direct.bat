@echo off
title DualGPUOptimizer Direct Launcher
echo Starting DualGPUOptimizer Direct Application...
echo.

REM Check if Python is available
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check for logs directory
if not exist logs mkdir logs

REM Run the direct application
python run_direct_app.py

REM In case of error
if %ERRORLEVEL% neq 0 (
    echo.
    echo Application exited with errors.
    echo Check logs\direct_app.log for details.
    pause
)

exit /b %ERRORLEVEL% 