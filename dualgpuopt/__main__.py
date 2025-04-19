"""
Main entry point for DualGPUOptimizer
"""
import sys
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dualgpuopt.log')
    ]
)

logger = logging.getLogger("DualGPUOptimizer")


def setup_environment():
    """Set up the environment for the application"""
    # Add the parent directory to sys.path if running as a module or standalone
    parent_dir = str(Path(__file__).resolve().parent.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        
    # Create necessary directories
    for dir_path in ['batch', 'services']:
        Path(__file__).parent.joinpath(dir_path).mkdir(exist_ok=True)
        
        # Create __init__.py in subdirectories if it doesn't exist
        init_path = Path(__file__).parent.joinpath(dir_path, '__init__.py')
        if not init_path.exists():
            init_path.write_text('"""Package for {}."""'.format(dir_path))


def main():
    """Main entry point"""
    try:
        # Set up environment
        setup_environment()
        
        # Try to import and run the GUI application
        try:
            from dualgpuopt.gui.main_app import run
            logger.info("Starting DualGPUOptimizer")
            run()
        except ImportError:
            # Fallback to simplified GUI
            logger.error("Failed to import main application, trying simplified GUI")
            try:
                from dualgpuopt.gui import run
                run()
            except ImportError:
                logger.error("Failed to import GUI module")
                print("Failed to import GUI module, please ensure the application is properly installed.")
                return 1
    
    except Exception as e:
        logger.error(f"Error running DualGPUOptimizer: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 