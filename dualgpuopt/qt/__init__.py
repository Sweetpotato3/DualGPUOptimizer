"""
DualGPUOptimizer Qt Interface Module

This module provides a Qt-based graphical user interface for the DualGPUOptimizer
application with real-time GPU monitoring, memory profiling, and model optimization.
"""

__version__ = "1.0.0"
__author__ = "DualGPUOptimizer Team"


# Export tab components

# Export main application components

# Export system tray components

# Version information
VERSION_INFO = {
    "major": 1,
    "minor": 0,
    "patch": 0,
    "release": "stable",
}


def get_version():
    """Return the current version as a string."""
    return f"{VERSION_INFO['major']}.{VERSION_INFO['minor']}.{VERSION_INFO['patch']}-{VERSION_INFO['release']}"
