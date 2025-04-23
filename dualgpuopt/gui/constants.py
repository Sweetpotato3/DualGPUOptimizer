"""
Constants for the GUI components
"""
from pathlib import Path

# Application info
APP_NAME = "DualGPUOptimizer"
APP_VERSION = "0.2.0"

# UI settings
THEME = "darkly"
STATUS_DURATION = 5000  # duration to show status messages in ms
VRAM_WARN_MB = 256  # minimum MB reclaimed to show as success

# Asset paths - use relative path from this file
ASSET_DIR = Path(__file__).parent / "assets"

# UI metrics
UPDATE_INTERVAL = 1000  # GUI update interval in ms
GRAPH_UPDATE_INTERVAL = 2000  # Graph update interval in ms
TELEMETRY_INTERVAL = 500  # Telemetry polling interval in ms

# Color definitions
COLORS = {
    "primary": "#3498db",
    "success": "#2ecc71",
    "warning": "#f39c12",
    "danger": "#e74c3c",
    "info": "#3498db",
    "light": "#ecf0f1",
    "dark": "#2c3e50",
    "text": "#2c3e50",
    "background": "#ecf0f1",
}
