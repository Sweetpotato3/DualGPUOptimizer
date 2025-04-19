<<<<<<< HEAD
#!/usr/bin/env python3
"""
Standalone GUI constants module for DualGPUOptimizer.
This script contains all the GUI constants in one place to avoid import issues.
"""

from typing import Dict, Tuple
from __future__ import annotations
from pathlib import Path

# UI Padding constants
PAD = 10  # Standard padding for UI elements
PROGRESSBAR_THICKNESS = 8  # Thickness for progress bars

# Theme Colors (Purple Style based on Icon)
PURPLE_PRIMARY = "#7b1fa2"    # Main purple from icon
PURPLE_HIGHLIGHT = "#9c27b0"  # Lighter purple from icon graph/arrow
BLUE_ACCENT = "#3f51b5"       # Blue background from icon
PINK_ACCENT = "#e91e63"       # Accent color inspired by GPU lights
CYAN_ACCENT = "#00bcd4"       # Accent color inspired by GPU lights
ORANGE_ACCENT = "#ff9800"     # Accent color inspired by GPU lights
DARK_BACKGROUND = "#212121"   # Dark blue-grey background
LIGHT_FOREGROUND = "#f5f5f5"  # Light grey/white foreground
GRID_LINE_COLOR = "#455A64"   # Color for chart grid lines
WARNING_COLOR = "#ff9800"     # Orange for warnings/danger zones

# Chart and Visualization Constants
DEFAULT_CHART_BG = DARK_BACKGROUND
DEFAULT_CHART_FG = LIGHT_FOREGROUND
DEFAULT_CHART_HEIGHT = 150    # Default height for charts
CHART_HISTORY_LENGTH = 60     # Number of data points to keep in history (60 seconds)

# Color mapping for different metrics/GPUs
GPU_COLORS = {
    0: PURPLE_PRIMARY,      # Primary GPU
    1: BLUE_ACCENT,         # Secondary GPU
    2: PINK_ACCENT,         # Additional GPU
    3: CYAN_ACCENT,         # Additional GPU
    "temp": ORANGE_ACCENT,    # Temperature
    "power": CYAN_ACCENT,     # Power
    "memory": PINK_ACCENT,    # Memory
    "utilization": PURPLE_PRIMARY, # Utilization
}

# Font Constants
DEFAULT_FONT = "Segoe UI"     # Default font
DEFAULT_FONT_SIZE = 11        # Default font size

# Update Intervals (milliseconds)
UPDATE_INTERVAL_MS = 1000     # Default interval for UI updates (1 second)
FAST_UPDATE_INTERVAL_MS = 500 # Faster interval for critical components
SLOW_UPDATE_INTERVAL_MS = 2000 # Slower interval for less critical components

# Color constants
COLORS: Dict[str, str] = {
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

# Dashboard refresh rates (ms)
DASHBOARD_REFRESH_RATE = 1000
METRICS_REFRESH_RATE = 2000
IDLE_CHECK_INTERVAL = 5000

# Sizing constants
WIDGET_PADDING = 5
SECTION_PADDING = 10
DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 600

# Temperature thresholds (°C)
TEMP_WARNING = 80
TEMP_DANGER = 90

# Utilization thresholds (%)
UTIL_LOW = 30
UTIL_MEDIUM = 60
UTIL_HIGH = 90

# Status indicators
STATUS_COLORS: Dict[str, str] = {
    "ok": "#4caf50",      # Green
    "warning": "#ff9800", # Orange
    "error": "#f44336",   # Red
    "idle": "#03a9f4",    # Blue
    "disabled": "#9e9e9e" # Gray
}

APP_NAME        = "DualGPUOptimizer"
THEME           = "darkly"
ASSET_DIR       = Path(__file__).parent.parent / "assets"
BASE_FONT       = ("Segoe UI", 10)
STATUS_DURATION = 5000            # ms
VRAM_WARN_MB    = 256             # warn banner if < 256 MB reclaimed 
=======
"""
Common constants for the GUI modules.
This module should be importable by all GUI components without causing circular imports.
"""

# Layout constants
PAD = 16  # Global padding, doubled from original 8
PROGRESSBAR_THICKNESS = 14

# Chart colors for GPU visualization
GPU_COLORS = [
    "#33ff55",  # Lime for GPU-0
    "#00ffff",  # Cyan for GPU-1
    "#ff5500",  # Orange
    "#aa00ff",  # Purple
    "#ffcc00",  # Yellow
    "#ff0066",  # Pink
    "#00ffcc",  # Teal
    "#ffffff",  # White
]

# Default values
DEFAULT_CHART_BG = "#1a2327"
DEFAULT_FONT = "Segoe UI"
DEFAULT_FONT_SIZE = 11

"""
Shared constants for the GUI components of the DualGPUOptimizer.
"""
from __future__ import annotations

# UI Padding constants
PAD = 10  # Standard padding for UI elements

# Chart and visualization constants
DEFAULT_CHART_BG = "#1f1f1f"  # Dark background for charts
DEFAULT_CHART_FG = "#ffffff"  # Light foreground for charts
DEFAULT_CHART_HEIGHT = 150    # Default height for charts

# Color constants
GPU_COLORS = {
    0: "#4287f5",  # Blue for primary GPU
    1: "#f542a7",  # Pink for secondary GPU
    "temp": "#f5a742",  # Orange for temperature
    "power": "#42f584",  # Green for power
    "memory": "#f54242",  # Red for memory
    "utilization": "#42f5f5",  # Cyan for utilization
}

# Update intervals (milliseconds)
UPDATE_INTERVAL_MS = 1000  # Default interval for UI updates
FAST_UPDATE_INTERVAL_MS = 500  # Faster interval for critical components
SLOW_UPDATE_INTERVAL_MS = 2000  # Slower interval for less critical components

# Chart history length
CHART_HISTORY_LENGTH = 60  # Number of data points to keep in history (60 seconds) 
>>>>>>> 199829b (Update documentation for DualGPUOptimizer to provide a high-level overview of GPU optimization and model inference systems. Organized content into key components: Core GPU Management, Model Optimization Engine, Command System, Monitoring Dashboard, and State Management. Enhanced glob patterns for improved file matching and clarified key implementation files, ensuring comprehensive coverage of system functionalities and integration points.)
