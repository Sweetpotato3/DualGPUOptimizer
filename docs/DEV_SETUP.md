# Developer Setup Guide

This document provides instructions for setting up a development environment for DualGPUOptimizer.

## Requirements

- Python 3.9-3.11 (officially supported versions)
- Git
- NVIDIA GPU(s) with CUDA support (for non-mock mode)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/DualGPUOptimizer.git
cd DualGPUOptimizer
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

#### Regular installation

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install theme dependencies
python install_theme.py
```

#### Windows users behind proxies

If you're behind a corporate proxy and having trouble downloading PySide6 from PyPI, you can use Qt's official wheelhouse:

```bash
pip install --extra-index-url=https://download.qt.io/official_releases/QtForPython PySide6==6.5.3
pip install PyQtDarkTheme==2.1.0
```

### 4. Run the application

```bash
# Run with GUI (with real GPU monitoring)
python -m dualgpuopt.qt.app_window

# Run in mock mode (no real GPUs required)
python -m dualgpuopt.qt.app_window --mock
```

## Development Workflow

### Running tests

```bash
pytest
```

### Code formatting

```bash
black .
isort .
```

### Building documentation

```bash
cd docs
sphinx-build -b html . _build/html
```

## Continuous Integration

The CI pipeline runs on GitHub Actions and tests against Python 3.9, 3.10, and 3.11.

## Version Compatibility Notes

- Python 3.9-3.11: Fully supported
- Python 3.12+: Limited support, some wheels may be missing
- PySide6 6.5.3: LTS version with stable API
- PyQtDarkTheme 2.1.0: Last version before Python 3.12 incompatibility 