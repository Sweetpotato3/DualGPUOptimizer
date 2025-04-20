"""
DualGPUOptimizer - GPU optimization toolkit for ML model inference
"""
import logging
import sys
from pathlib import Path

__version__ = "0.2.0"

# Setup logger
logger = logging.getLogger("DualGPUOpt")

# Set up Python path to include parent directory
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Functions for mock mode control, but don't enable by default
MOCK_MODE = False

def enable_mock_mode():
    """Enable mock mode for testing without GPUs"""
    global MOCK_MODE
    MOCK_MODE = True
    
def disable_mock_mode():
    """Disable mock mode"""
    global MOCK_MODE
    MOCK_MODE = False

def is_mock_mode_enabled():
    """Check if mock mode is enabled."""
    return MOCK_MODE 