#!/bin/bash
# Run DualGPUOptimizer with dependency checking

echo "==================================="
echo "DualGPUOptimizer Launcher"
echo "==================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in PATH."
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

echo "Checking Python version..."
python3 -c "import sys; print('Python', sys.version); sys.exit(0 if sys.version_info >= (3, 8) else 1)"
if [ $? -ne 0 ]; then
    echo "Python 3.8 or higher is required."
    echo "Current version is too old."
    exit 1
fi

echo "Python version is compatible."
echo

# Create logs directory if it doesn't exist
mkdir -p logs

# Check for and create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check for dependencies
echo "Checking dependencies..."
python -m dualgpuopt --check-deps

# Ask if dependencies should be installed
echo
read -p "Install missing dependencies? [y/N]: " install_deps

if [[ $install_deps == "y" || $install_deps == "Y" ]]; then
    echo
    echo "Installing dependencies..."
    python -m dualgpuopt --install-deps
    if [ $? -ne 0 ]; then
        echo "Failed to install dependencies."
        echo "See logs for details."
        exit 1
    fi
fi

echo
echo "==================================="
echo "Starting DualGPUOptimizer..."
echo "==================================="
echo

# Check if run_direct_app.py exists
if [ -f "run_direct_app.py" ]; then
    echo "Using direct launcher (recommended)..."
    python run_direct_app.py --mock "$@"
else
    echo "Using module-based launcher..."
    python -m dualgpuopt --mock "$@"
fi

echo
echo "==================================="
echo "DualGPUOptimizer has exited."
echo "==================================="
echo

# Deactivate virtual environment
deactivate
