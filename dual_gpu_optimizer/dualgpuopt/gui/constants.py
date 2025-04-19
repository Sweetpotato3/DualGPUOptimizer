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