@echo off
REM Run DualGPUOptimizer with dependency checking

echo ===================================
echo DualGPUOptimizer Launcher
echo ===================================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

echo Checking Python version...
python -c "import sys; print('Python', sys.version); sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python 3.8 or higher is required.
    echo Current version is too old.
    pause
    exit /b 1
)

echo Python version is compatible.
echo.

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

REM Check for and create virtual environment if it doesn't exist
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check for dependencies
echo Checking dependencies...
python -m dualgpuopt --check-deps

REM Ask if dependencies should be installed
echo.
set /p install_deps=Install missing dependencies? [y/N]:

if /i "%install_deps%"=="y" (
    echo.
    echo Installing dependencies...
    python -m dualgpuopt --install-deps
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install dependencies.
        echo See logs for details.
        pause
        exit /b 1
    )
)

echo.
echo ===================================
echo Starting DualGPUOptimizer...
echo ===================================
echo.

REM Check if run_direct_app.py exists
if exist run_direct_app.py (
    echo Using direct launcher (recommended)...
    python run_direct_app.py --mock
) else (
    echo Using module-based launcher...
    python -m dualgpuopt --mock
)

echo.
echo ===================================
echo DualGPUOptimizer has exited.
echo ===================================
echo.

REM Deactivate virtual environment
call deactivate

pause
