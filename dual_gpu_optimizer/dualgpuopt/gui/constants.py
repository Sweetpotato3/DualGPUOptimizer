"""
Common constants for the GUI modules.
This module should be importable by all GUI components without causing circular imports.
"""

# Layout constants
PAD = 10  # Standard padding for UI elements
PROGRESSBAR_THICKNESS = 8  # Thickness for progress bars in app.py

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

# --- Theme Colors (Purple Style based on Icon) ---
PURPLE_PRIMARY = "#7E57C2"    # Main purple from icon
PURPLE_HIGHLIGHT = "#AB47BC" # Lighter purple from icon graph/arrow
BLUE_ACCENT = "#42A5F5"      # Blue background from icon
PINK_ACCENT = "#EC407A"      # Accent color inspired by GPU lights
CYAN_ACCENT = "#26C6DA"      # Accent color inspired by GPU lights
ORANGE_ACCENT = "#FFA726"     # Accent color inspired by GPU lights
DARK_BACKGROUND = "#263238"  # Dark blue-grey background
LIGHT_FOREGROUND = "#ECEFF1" # Light grey/white foreground
GRID_LINE_COLOR = "#455A64"  # Color for chart grid lines
WARNING_COLOR = "#FFA726"    # Orange for warnings/danger zones

# --- Chart and Visualization Constants ---
DEFAULT_CHART_BG = DARK_BACKGROUND
DEFAULT_CHART_FG = LIGHT_FOREGROUND
DEFAULT_CHART_HEIGHT = 150    # Default height for charts
CHART_HISTORY_LENGTH = 60  # Number of data points to keep in history (e.g., 60 seconds)

# Color mapping for different metrics/GPUs
# Using purples and accents derived from the icon
GPU_COLORS = {
    0: PURPLE_PRIMARY,      # Primary GPU
    1: PURPLE_HIGHLIGHT,    # Secondary GPU
    # Colors for additional GPUs (can add more if needed)
    2: PINK_ACCENT,
    3: CYAN_ACCENT,
    # Colors for specific metrics (optional, can use GPU colors or specific ones)
    "temp": ORANGE_ACCENT,    # Temperature
    "power": CYAN_ACCENT,     # Power
    "memory": PINK_ACCENT,    # Memory
    "utilization": PURPLE_PRIMARY, # Utilization (matches primary GPU)
}

# --- Font Constants ---
DEFAULT_FONT = "Segoe UI"  # Consider platform variations if needed
DEFAULT_FONT_SIZE = 10      # Slightly smaller default font size

# --- Update Intervals (milliseconds) ---
UPDATE_INTERVAL_MS = 1000  # Default interval for UI updates (1 second)
FAST_UPDATE_INTERVAL_MS = 500  # Faster interval for critical components
SLOW_UPDATE_INTERVAL_MS = 2000  # Slower interval for less critical components 