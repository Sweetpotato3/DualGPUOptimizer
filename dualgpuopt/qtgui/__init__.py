"""
DualGPUOptimizer Qt GUI components.

This package provides a Qt-based user interface for the DualGPUOptimizer,
offering advanced real-time visualizations, interactive controls, and
better threading support compared to the original implementation.
"""

from pathlib import Path

# Package version
__version__ = "0.1.0"

# Ensure resource directories exist
RESOURCE_DIR = Path.home() / ".dualgpuopt"
PRESETS_DIR = RESOURCE_DIR / "presets"
EXPORTS_DIR = RESOURCE_DIR / "exports"

# Create directories if they don't exist
for directory in [RESOURCE_DIR, PRESETS_DIR, EXPORTS_DIR]:
    directory.mkdir(exist_ok=True) 