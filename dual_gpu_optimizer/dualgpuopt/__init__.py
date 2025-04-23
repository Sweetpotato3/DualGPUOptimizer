"""
DualGPUOptimizer - A tool for optimizing dual GPU setups.
"""
from __future__ import annotations

import os

# Version information
VERSION = "0.2.0"

# Expose version as package attribute
__version__ = VERSION


# Set environment variable for mock mode if requested
def enable_mock_mode():
    """Enable mock mode for testing without real GPUs."""
    os.environ["DGPUOPT_MOCK_GPUS"] = "1"


def is_mock_mode_enabled():
    """Check if mock mode is enabled."""
    return os.environ.get("DGPUOPT_MOCK_GPUS") == "1"


# Define public API
__all__ = [
    "VERSION",
    "__version__",
    "enable_mock_mode",
    "is_mock_mode_enabled",
]

# Don't import modules here to avoid circular imports
# Instead, users should import specific modules as needed:
# from dualgpuopt import gpu_info
# from dualgpuopt.gui import run_app
