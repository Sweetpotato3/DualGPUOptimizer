# PowerShell script to build and verify DualGPUOptimizer
# Usage: .\build_and_verify.ps1

Write-Host "=== DualGPUOptimizer Build & Verification ===" -ForegroundColor Cyan

# 1. Ensure virtual environment is activated
Write-Host "Ensuring dependencies are installed..." -ForegroundColor Yellow
& python -m pip install -r requirements.txt

# 2. Run the PyInstaller build
Write-Host "`nBuilding application with PyInstaller..." -ForegroundColor Yellow
& python -m PyInstaller build.spec --clean

# Check if build succeeded
if (-not $?) {
    Write-Host "❌ Build failed! See error messages above." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Build completed successfully!" -ForegroundColor Green

# 3. Verify the build
Write-Host "`nVerifying build integrity..." -ForegroundColor Yellow
& python test_bundle.py

# Check if verification succeeded
if (-not $?) {
    Write-Host "❌ Verification failed! See error messages above." -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Build and verification completed successfully!" -ForegroundColor Green
Write-Host "Application is available at: $((Get-Location).Path)\dist\DualGPUOptimizer" -ForegroundColor Cyan

# Output onefile build command for reference
Write-Host "`n=== For OneFile Build ===" -ForegroundColor Yellow
Write-Host "If you need a single EXE file, run:" -ForegroundColor Yellow
Write-Host "pyinstaller build.spec --onefile --add-data '%TORCH_HOME%;torch.libs' --collect-submodules torch" -ForegroundColor White

exit 0 