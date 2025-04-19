"""
GUI package for DualGPUOptimizer
Handles UI components, dashboard, and visualization
"""
import importlib.util
import sys
from pathlib import Path

# Safe import for constants - ensures it works both in development and when bundled
try:
    from . import constants
except ImportError:
    # If running from bundle, make sure constants.py is in the path
    if getattr(sys, 'frozen', False):
        module_path = Path(sys._MEIPASS) / "dualgpuopt" / "gui" / "constants.py"
        if module_path.exists():
            spec = importlib.util.spec_from_file_location("dualgpuopt.gui.constants", module_path)
            constants = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(constants)
            sys.modules["dualgpuopt.gui.constants"] = constants

# Import UI components - these are lazily loaded when needed
from . import main_app  # Main application entry point
from . import dashboard  # GPU monitoring dashboard
from . import optimizer_tab  # GPU split optimizer interface

from dualgpuopt.gui.dashboard import DashboardView
from dualgpuopt.gui.optimizer_tab import OptimizerTab
from dualgpuopt.gui.launcher import LauncherTab
from dualgpuopt.gui.main_app import MainApplication, run

__all__ = [
    'DashboardView',
    'OptimizerTab',
    'LauncherTab',
    'MainApplication',
    'run'
]

# Check for required modules to provide better error messages
try:
    import dualgpuopt.vram_reset
    import dualgpuopt.ctx_size
    import dualgpuopt.mpolicy
    import dualgpuopt.layer_balance
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    import logging
    logging.getLogger("DualGPUOpt.GUI").warning(f"Advanced optimization features not available: {e}")
    ADVANCED_FEATURES_AVAILABLE = False 