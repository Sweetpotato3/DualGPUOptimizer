"""
GUI package for DualGPUOptimizer
Handles UI components, dashboard, and visualization
"""
import importlib.util
import sys
from pathlib import Path
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("DualGPUOpt.GUI")

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
from . import modern_ui  # Modern ttkbootstrap UI (2025 update)

from dualgpuopt.gui.dashboard import DashboardView
from dualgpuopt.gui.optimizer_tab import OptimizerTab
from dualgpuopt.gui.launcher import LauncherTab
from dualgpuopt.gui.main_app import MainApplication, run
from dualgpuopt.gui.modern_ui import ModernApp, run_modern_app

__all__ = [
    'DashboardView',
    'OptimizerTab',
    'LauncherTab',
    'MainApplication',
    'ModernApp',
    'run',
    'run_modern_app'
]

# Check for required modules to provide better error messages
try:
    import dualgpuopt.vram_reset
    import dualgpuopt.ctx_size
    import dualgpuopt.mpolicy
    import dualgpuopt.layer_balance
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Advanced optimization features not available: {e}")
    ADVANCED_FEATURES_AVAILABLE = False

# Check for optional advanced features
try:
    import torch
    TORCH_AVAILABLE = True
    logger.info("PyTorch detected")
except ImportError:
    logger.warning("PyTorch not found - some features will be limited")
    TORCH_AVAILABLE = False

# Import modern GUI components
try:
    # Import directly from the module, not relative import
    from dualgpuopt.gui import modern_ui
    
    # Provide the run function
    def run_app(config: Optional[Dict[str, Any]] = None) -> None:
        """Run the modern UI application (directly)"""
        # Import here to avoid circular imports
        from dualgpuopt.gui.modern_ui import run_modern_app
        run_modern_app()
except ImportError as e:
    logger.warning(f"Could not import modern UI: {e}")
    
    # Fallback for modern UI
    def run_app(config: Optional[Dict[str, Any]] = None) -> None:
        """Fallback for running the modern UI"""
        logger.warning("Using fallback UI launcher")
        # Try with different imports
        try:
            # Try importing from module
            from dualgpuopt.gui.main_app import run
            logger.info("Falling back to legacy UI")
            run()
        except ImportError:
            logger.error("Failed to load UI - no suitable module found")
            sys.exit(1)

def run_app() -> None:
    """
    Run the appropriate GUI application based on availability.
    Tries to load the modern UI first, falling back to legacy UI if needed.
    """
    # First try to run the modern UI version
    try:
        # Check if modern_ui module exists before attempting to import
        if importlib.util.find_spec("dualgpuopt.gui.modern_ui") is not None:
            logger.info("Loading modern UI implementation")
            from dualgpuopt.gui.modern_ui import run_modern_app
            run_modern_app()
            return
        else:
            logger.warning("Modern UI module not found, falling back to legacy UI")
    except ImportError as e:
        logger.warning(f"Failed to import modern UI: {e}")
    except Exception as e:
        logger.error(f"Error running modern UI: {e}", exc_info=True)
    
    # Fall back to legacy UI if modern UI fails
    try:
        logger.info("Loading legacy UI implementation")
        from dualgpuopt.gui.main_app import run
        run()
    except ImportError as e:
        logger.error(f"Failed to import legacy UI: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running legacy UI: {e}", exc_info=True)
        sys.exit(1) 