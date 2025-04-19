# Setup development environment for DualGPUOptimizer
Write-Host "Setting up development environment for DualGPUOptimizer..." -ForegroundColor Cyan

# Check if Python is installed
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $pythonCmd) {
    Write-Host "Python not found. Please install Python 3.12 or higher and try again." -ForegroundColor Red
    exit 1
}

# Check Python version
$pythonVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "Found Python version: $pythonVersion" -ForegroundColor Green

# Create and activate virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ./.venv/Scripts/Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -e ./dual_gpu_optimizer
pip install pytest pyinstaller

# Install development dependencies
pip install black flake8 pytest-cov

Write-Host "Development environment setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the application, run:" -ForegroundColor Cyan
Write-Host "python -m dualgpuopt" -ForegroundColor White
Write-Host ""
Write-Host "To build the application with PyInstaller, run:" -ForegroundColor Cyan
Write-Host "pyinstaller dual_gpu_optimizer_app.spec" -ForegroundColor White 