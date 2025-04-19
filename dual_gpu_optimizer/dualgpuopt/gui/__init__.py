"""
GUI module for the DualGPUOptimizer.

This package contains all the GUI components and functionality.
"""
from __future__ import annotations

# Define public API
__all__ = ["run_app"]

# Define a function that will lazy-load the app module
def run_app(mock_mode: bool = False, theme: str = None):
    """
    Run the DualGPUOptimizer application.
    
    Args:
        mock_mode: Whether to use mock GPU data
        theme: Optional theme name to use
    """
    # Import here to avoid circular imports
    from dualgpuopt.gui.app import run_app as _run_app
    return _run_app(mock_mode=mock_mode, theme=theme)

"""
GUI module initialization with runtime guard for constants.
"""
try:
    from .constants import APP_NAME, THEME
except ImportError as exc:
    raise SystemExit(
        "❌ constants.py missing - reinstall DualGPUOpt package"
    ) from exc

# Import rest of GUI components
from .main_window import MainWindow
from .dashboard import DashboardFrame
from .optimizer import OptimizerFrame