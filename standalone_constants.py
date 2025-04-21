#!/usr/bin/env python3
"""
Standalone constants module for testing without circular imports
"""

# Application info
APP_NAME = "DualGPUOptimizer"
APP_VERSION = "0.2.0"

# UI Padding constants
PAD = 10  # Standard padding for UI elements
PROGRESSBAR_THICKNESS = 14  # Thickness for progress bars

# Color constants
COLORS = {
    "primary": "#1e88e5",
    "secondary": "#424242",
    "success": "#4caf50",
    "warning": "#ff9800",
    "danger": "#f44336",
    "info": "#03a9f4",
    "light": "#f5f5f5",
    "dark": "#212121",
}

# Theme constants
DARK_THEME = "darkly"
LIGHT_THEME = "litera"
THEME = DARK_THEME

# Print confirmation when this module is imported directly
if __name__ != "__main__":
    print(f"Standalone constants module loaded: {APP_NAME} v{APP_VERSION}")