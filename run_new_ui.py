#!/usr/bin/env python3
"""
Direct launcher for our modern neon UI
This launcher bypasses all import mechanisms and directly runs our gui.py module
"""
import importlib.util
import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ModernUILauncher")

# Directly import our GUI module by file path
try:
    # Load and execute gui.py directly
    gui_path = Path(__file__).parent / "dualgpuopt" / "gui.py"
    logger.info(f"Loading UI from: {gui_path}")

    # Import the module
    spec = importlib.util.spec_from_file_location("direct_gui", gui_path)
    if spec is None:
        raise ImportError(f"Could not load spec from {gui_path}")

    gui_module = importlib.util.module_from_spec(spec)
    sys.modules["direct_gui"] = gui_module
    spec.loader.exec_module(gui_module)

    # Run the UI
    logger.info("Launching modern UI...")
    gui_module.run_app()
except Exception as e:
    logger.error(f"Error launching modern UI: {e}", exc_info=True)
    import traceback

    traceback.print_exc()
    sys.exit(1)
