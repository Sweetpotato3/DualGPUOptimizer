import argparse
import sys

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import QApplication

# Import qdarktheme for theme styling
import qdarktheme

# Set application attributes for high DPI screens
QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


def parse_args():
    parser = argparse.ArgumentParser(description="DualGPUOptimizer Qt Edition")
    parser.add_argument("--mock", action="store_true", help="Use mock GPU data")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


def setup_logging(verbose=False):
    import logging
    import os
    from datetime import datetime

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Set up file handler
    log_file = os.path.join("logs", f'dualgpuopt_qt_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )

    logging.info(f"Log file created at: {log_file}")
    return logging.getLogger("DualGPUOptimizer")


def main():
    # Parse command line arguments
    args = parse_args()

    # Set up logging
    logger = setup_logging(args.verbose)
    logger.info("Starting DualGPUOptimizer Qt Edition")

    if args.mock:
        logger.info("Mock GPU mode enabled")

    # Start Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("DualGPUOptimizer")
    app.setStyle("Fusion")  # Provides a consistent look across platforms
    
    # Apply dark theme styling
    app.setStyleSheet(qdarktheme.load_stylesheet("dark")) # API unchanged; keep call

    # Import here to avoid circular imports
    from dualgpuopt.qt.app_window import DualGPUOptimizerApp

    window = DualGPUOptimizerApp(mock_mode=args.mock)
    window.show()

    logger.info("Application window initialized")

    # Start the event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
