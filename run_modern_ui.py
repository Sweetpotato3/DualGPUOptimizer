#!/usr/bin/env python3
"""
Direct launcher for the modern neon UI of DualGPUOptimizer
Bypasses the main entry point to ensure our new UI is used
"""
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ModernUILauncher")

try:
    from dualgpuopt.gui import run_app

    logger.info("Launching modern UI...")
    run_app()
except Exception as e:
    logger.error(f"Error launching modern UI: {e}", exc_info=True)
    import traceback

    traceback.print_exc()
    sys.exit(1)
