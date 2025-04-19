"""
DualGPUOptimizer - A tool for optimizing dual GPU setups.
"""
from __future__ import annotations

import os
import sys

# Version information
VERSION = "0.2.0"

# Expose version as package attribute
__version__ = VERSION

# Functions for mock mode control, but don't enable by default
def enable_mock_mode():
    """Enable mock mode for testing without real GPUs."""
    os.environ["DGPUOPT_MOCK_GPUS"] = "1"
    
def disable_mock_mode():
    """Disable mock mode and use real GPUs."""
    if "DGPUOPT_MOCK_GPUS" in os.environ:
        del os.environ["DGPUOPT_MOCK_GPUS"]
    
def is_mock_mode_enabled():
    """Check if mock mode is enabled."""
    return os.environ.get("DGPUOPT_MOCK_GPUS") == "1" 