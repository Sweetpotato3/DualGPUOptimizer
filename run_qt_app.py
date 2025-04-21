#!/usr/bin/env python3
"""
DualGPUOptimizer Qt Launcher

This script launches the Qt version of DualGPUOptimizer with proper
environment setup and command-line argument handling.
"""

import sys
import os
import argparse
import logging
from datetime import datetime

def setup_logging(verbose=False):
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Set up file handler
    log_file = os.path.join('logs', f'dualgpuopt_qt_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger('DualGPUOptimizer')
    logger.info(f"Log file created at: {log_file}")
    return logger

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='DualGPUOptimizer Qt Edition')
    parser.add_argument('--mock', action='store_true', help='Use mock GPU data')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    args = parse_args()

    # Set up logging
    logger = setup_logging(args.verbose)
    logger.info("Starting DualGPUOptimizer Qt Edition")

    # Configure environment variables
    if args.mock:
        logger.info("Mock GPU mode enabled")
        os.environ['DUALGPUOPT_MOCK_GPU'] = '1'

    try:
        # Import Qt modules
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt, QCoreApplication
        except ImportError:
            logger.error("PySide6 is not installed. Please install it with: pip install PySide6==6.5.2")
            print("Error: PySide6 is not installed. Please install it with: pip install PySide6==6.5.2")
            return 1

        # Set application attributes for high DPI screens
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        # Start Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("DualGPUOptimizer")
        app.setStyle("Fusion")  # Provides a consistent look across platforms

        # Import here to avoid circular imports
        try:
            from dualgpuopt.qt.app_window import DualGPUOptimizerApp
            window = DualGPUOptimizerApp(mock_mode=args.mock)
            window.show()

            logger.info("Application window initialized")

            # Start the event loop
            return app.exec()
        except ImportError as e:
            logger.error(f"Failed to import required modules: {e}")
            print(f"Error: Failed to import required modules: {e}")
            return 1

    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())