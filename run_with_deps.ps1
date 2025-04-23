# Run DualGPUOptimizer with dependency checking

Write-Host "====================================="
Write-Host "DualGPUOptimizer Launcher"
Write-Host "====================================="
Write-Host ""

# Check if Python is installed
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Checking Python version..."
$pythonVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
$pythonCompatible = python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" -ErrorAction SilentlyContinue

if ($LASTEXITCODE -ne 0) {
    Write-Host "Python 3.8 or higher is required." -ForegroundColor Red
    Write-Host "Current version is too old: $pythonVersion" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Python version is compatible: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Create logs directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -Path "logs" -ItemType Directory | Out-Null
    Write-Host "Created logs directory" -ForegroundColor Green
}

# Check for and create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create virtual environment." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "Virtual environment created successfully" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Check for dependencies
Write-Host "Checking dependencies..." -ForegroundColor Yellow
python -m dualgpuopt --check-deps

# Ask if dependencies should be installed
Write-Host ""
$installDeps = Read-Host "Install missing dependencies? [y/N]"

if ($installDeps -eq "y" -or $installDeps -eq "Y") {
    Write-Host ""
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    python -m dualgpuopt --install-deps
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install dependencies." -ForegroundColor Red
        Write-Host "See logs for details." -ForegroundColor Red
        Read-Host "Press Enter to continue"
    }
}

Write-Host ""
Write-Host "====================================="
Write-Host "Starting DualGPUOptimizer..."
Write-Host "====================================="
Write-Host ""

# Check if run_direct_app.py exists
if (Test-Path "run_direct_app.py") {
    Write-Host "Using direct launcher (recommended)..." -ForegroundColor Green
    python run_direct_app.py --mock
} else {
    Write-Host "Using module-based launcher..." -ForegroundColor Yellow
    python -m dualgpuopt --mock
}

Write-Host ""
Write-Host "====================================="
Write-Host "DualGPUOptimizer has exited."
Write-Host "====================================="
Write-Host ""

# Deactivate virtual environment
deactivate

Read-Host "Press Enter to exit"
