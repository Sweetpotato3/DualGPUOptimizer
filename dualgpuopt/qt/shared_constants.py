"""
Shared constants for the Qt GUI components.
"""

# Default appearance settings
DEFAULT_FONT = "Segoe UI"
DEFAULT_FONT_SIZE = 10
PAD = 6
UPDATE_INTERVAL_MS = 500  # unified for Qt & Tk
PRODUCT_NAME = "DualGPUOptimizer"

# Chart/visualization constants
CHART_BG = "#2b2b2b"
CHART_FG = "#e0e0e0"
CHART_GRID = "#404040"
CHART_HEIGHT = 150

# Color scheme
GPU_COLORS = {
    0: "#7e57c2",  # Primary purple
    1: "#26a69a",  # Teal accent
    2: "#ec407a",  # Pink accent
    3: "#42a5f5",  # Blue accent
    "memory": "#ec407a",  # Pink for memory
    "temp": "#ff9800",    # Orange for temperature
    "power": "#26a69a",   # Teal for power
} 