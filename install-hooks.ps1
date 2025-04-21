# PowerShell script to install Git hooks
Write-Host "Installing Git hooks..." -ForegroundColor Green

# Check if .git directory exists
if (-not (Test-Path ".git")) {
    Write-Host "Error: .git directory not found. Are you in the root of the repository?" -ForegroundColor Red
    exit 1
}

# Create hooks directory if it doesn't exist
if (-not (Test-Path ".git\hooks")) {
    Write-Host "Creating hooks directory..." -ForegroundColor Yellow
    New-Item -Path ".git\hooks" -ItemType Directory -Force | Out-Null
}

# Copy pre-commit hook
Write-Host "Installing pre-commit hook..." -ForegroundColor Yellow
Copy-Item -Path "pre-commit-hook.py" -Destination ".git\hooks\pre-commit-hook.py" -Force
Copy-Item -Path "pre-commit.bat" -Destination ".git\hooks\pre-commit" -Force

# Check if autoflake is installed
try {
    $null = & python -m pip show autoflake 2>$null
    Write-Host "Autoflake is already installed." -ForegroundColor Green
} catch {
    Write-Host "Installing autoflake..." -ForegroundColor Yellow
    & python -m pip install autoflake
}

Write-Host "Git hooks installation complete!" -ForegroundColor Green
Write-Host "The pre-commit hook will now run whenever you commit changes." -ForegroundColor Cyan 