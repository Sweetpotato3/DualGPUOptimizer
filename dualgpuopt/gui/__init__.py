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