"""
GUI package for DualGPUOptimizer
Handles UI components, dashboard, and visualization
"""
import importlib.util
import sys
from pathlib import Path
import logging

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

# We'll import the components lazily as needed to avoid circular imports
__all__ = [
    'DashboardView',
    'OptimizerTab',
    'LauncherTab',
    'MainApplication',
    'ModernApp',
    'run',
    'run_modern_app'
]

# Forward declarations of classes to avoid circular imports
DashboardView = None
OptimizerTab = None
LauncherTab = None
MainApplication = None
ModernApp = None
run = None
run_modern_app = None

def _import_component(name):
    """Import a component on demand to avoid circular dependencies"""
    try:
        return importlib.import_module(f"dualgpuopt.gui.{name}")
    except ImportError as e:
        logger.warning(f"Could not import {name}: {e}")
        return None

def get_dashboard_view():
    """Get the DashboardView class, importing it if necessary"""
    global DashboardView
    if DashboardView is None:
        module = _import_component("dashboard")
        if module:
            DashboardView = module.DashboardView
    return DashboardView

def get_optimizer_tab():
    """Get the OptimizerTab class, importing it if necessary"""
    global OptimizerTab
    if OptimizerTab is None:
        module = _import_component("optimizer_tab")
        if module:
            OptimizerTab = module.OptimizerTab
    return OptimizerTab

def get_launcher_tab():
    """Get the LauncherTab class, importing it if necessary"""
    global LauncherTab
    if LauncherTab is None:
        module = _import_component("launcher")
        if module:
            LauncherTab = module.LauncherTab
    return LauncherTab

def get_main_application():
    """Get the MainApplication class, importing it if necessary"""
    global MainApplication, run
    if MainApplication is None:
        module = _import_component("main_app")
        if module:
            MainApplication = module.MainApplication
            run = module.run
    return MainApplication

def get_modern_app():
    """Get the ModernApp class, importing it if necessary"""
    global ModernApp, run_modern_app
    if ModernApp is None:
        module = _import_component("modern_ui")
        if module:
            ModernApp = module.ModernApp
            run_modern_app = module.run_modern_app
    return ModernApp

# Check for required modules to provide better error messages
try:
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Advanced optimization features not available: {e}")
    ADVANCED_FEATURES_AVAILABLE = False

# Check for optional advanced features
try:
    TORCH_AVAILABLE = True
    logger.info("PyTorch detected")
except ImportError:
    logger.warning("PyTorch not found - some features will be limited")
    TORCH_AVAILABLE = False

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
            modern_app = get_modern_app()
            if modern_app and run_modern_app:
                run_modern_app()
                return
            else:
                logger.warning("Modern UI classes not found, falling back to legacy UI")
        else:
            logger.warning("Modern UI module not found, falling back to legacy UI")
    except ImportError as e:
        logger.warning(f"Failed to import modern UI: {e}")
    except Exception as e:
        logger.error(f"Error running modern UI: {e}", exc_info=True)

    # Fall back to legacy UI if modern UI fails
    try:
        logger.info("Loading legacy UI implementation")
        main_app = get_main_application()
        if main_app and run:
            run()
        else:
            logger.error("Failed to load legacy UI classes")
            sys.exit(1)
    except ImportError as e:
        logger.error(f"Failed to import legacy UI: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running legacy UI: {e}", exc_info=True)
        sys.exit(1)