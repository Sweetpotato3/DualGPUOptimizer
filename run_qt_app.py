#!/usr/bin/env python3
"""
Run script for DualGPUOptimizer Qt Edition
"""
import argparse
import logging
import os
import sys
from pathlib import Path

def setup_logging(verbose=False):
    """Set up logging configuration"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Generate log file name with timestamp
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"dualgpuopt_qt_{timestamp}.log"
    
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    
    logger = logging.getLogger("DualGPUOptimizer")
    logger.setLevel(log_level)
    
    # Add file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Create formatter and add to handlers
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"Log file created at: {log_file}")
    
    return logger

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="DualGPUOptimizer Qt Edition")
    parser.add_argument("--mock", action="store_true", help="Use mock GPU data")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    return parser.parse_args()

def ensure_required_files():
    """Ensure all required directories and files exist"""
    # Create Qt directory if it doesn't exist
    qt_dir = Path("dualgpuopt/qt")
    qt_dir.mkdir(exist_ok=True)
    
    # Required files
    required_files = [
        "dualgpuopt/qt/__init__.py",
        "dualgpuopt/qt/app_window.py", 
        "dualgpuopt/qt/dashboard_tab.py",
        "dualgpuopt/qt/launcher_tab.py",
        "dualgpuopt/qt/optimizer_tab.py",
        "dualgpuopt/qt/system_tray.py"
    ]
    
    # Check each file
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    return missing_files

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    args = parse_args()
    
    # Set up logging
    logger = setup_logging(args.verbose)
    logger.info("Starting DualGPUOptimizer Qt Edition")
    
    # Check for required files
    missing_files = ensure_required_files()
    if missing_files:
        logger.error(f"Missing required files: {missing_files}")
        print(f"Error: The following required files are missing: {missing_files}")
        print("Please make sure all Qt implementation files are present.")
        return 1
    
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