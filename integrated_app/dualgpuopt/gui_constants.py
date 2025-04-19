#!/usr/bin/env python3
"""
Standalone GUI constants module for DualGPUOptimizer.
This script contains all the GUI constants in one place to avoid import issues.
"""

# UI Padding constants
PAD = 10  # Standard padding for UI elements
PROGRESSBAR_THICKNESS = 8  # Thickness for progress bars

# Theme Colors (Purple Style based on Icon)
PURPLE_PRIMARY = "#7E57C2"    # Main purple from icon
PURPLE_HIGHLIGHT = "#AB47BC"  # Lighter purple from icon graph/arrow
BLUE_ACCENT = "#42A5F5"       # Blue background from icon
PINK_ACCENT = "#EC407A"       # Accent color inspired by GPU lights
CYAN_ACCENT = "#26C6DA"       # Accent color inspired by GPU lights
ORANGE_ACCENT = "#FFA726"     # Accent color inspired by GPU lights
DARK_BACKGROUND = "#263238"   # Dark blue-grey background
LIGHT_FOREGROUND = "#ECEFF1"  # Light grey/white foreground
GRID_LINE_COLOR = "#455A64"   # Color for chart grid lines
WARNING_COLOR = "#FFA726"     # Orange for warnings/danger zones

# Chart and Visualization Constants
DEFAULT_CHART_BG = DARK_BACKGROUND
DEFAULT_CHART_FG = LIGHT_FOREGROUND
DEFAULT_CHART_HEIGHT = 150    # Default height for charts
CHART_HISTORY_LENGTH = 60     # Number of data points to keep in history (60 seconds)

# Color mapping for different metrics/GPUs
GPU_COLORS = {
    0: PURPLE_PRIMARY,      # Primary GPU
    1: PURPLE_HIGHLIGHT,    # Secondary GPU
    2: PINK_ACCENT,         # Additional GPU
    3: CYAN_ACCENT,         # Additional GPU
    "temp": ORANGE_ACCENT,    # Temperature
    "power": CYAN_ACCENT,     # Power
    "memory": PINK_ACCENT,    # Memory
    "utilization": PURPLE_PRIMARY, # Utilization
}

# Font Constants
DEFAULT_FONT = "Segoe UI"     # Default font
DEFAULT_FONT_SIZE = 10        # Default font size

# Update Intervals (milliseconds)
UPDATE_INTERVAL_MS = 1000     # Default interval for UI updates (1 second)
FAST_UPDATE_INTERVAL_MS = 500 # Faster interval for critical components
SLOW_UPDATE_INTERVAL_MS = 2000 # Slower interval for less critical components 