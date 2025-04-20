"""
Main entry point for DualGPUOptimizer
"""
import sys
import logging
import argparse
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger("DualGPUOpt.Main")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="DualGPUOptimizer - GPU optimization for ML model inference")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument("-m", "--model", help="Model path or HuggingFace identifier")
    parser.add_argument("-c", "--ctx-size", type=int, help="Context size")
    parser.add_argument("-q", "--quant", help="Quantization method (e.g., 'awq', 'gptq')")
    parser.add_argument("-e", "--export", help="Export environment variables to file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--mock", action="store_true", help="Enable mock GPU mode for testing")
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Set verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    try:
        # Enable mock mode if requested
        if args.mock:
            try:
                # Try different module locations for the set_mock_mode function
                mock_mode_set = False
                exceptions = []
                
                # Try the compatibility layer
                try:
                    from dualgpuopt.gpu.compat import set_mock_mode
                    set_mock_mode(True)
                    mock_mode_set = True
                    logger.info("Mock GPU mode enabled via compatibility layer")
                except ImportError as e:
                    exceptions.append(f"Error importing from compatibility layer: {e}")
                
                # Try the refactored module structure
                if not mock_mode_set:
                    try:
                        from dualgpuopt.gpu.mock import set_mock_mode
                        set_mock_mode(True)
                        mock_mode_set = True
                        logger.info("Mock GPU mode enabled via refactored module")
                    except ImportError as e:
                        exceptions.append(f"Error importing from refactored module: {e}")
                
                # Try the legacy module structure
                if not mock_mode_set:
                    try:
                        from dualgpuopt.gpu import set_mock_mode
                        set_mock_mode(True)
                        mock_mode_set = True
                        logger.info("Mock GPU mode enabled via module init")
                    except ImportError as e:
                        exceptions.append(f"Error importing from module init: {e}")
                
                # Lastly try the gpu_info module
                if not mock_mode_set:
                    try:
                        from dualgpuopt.gpu_info import set_mock_mode
                        set_mock_mode(True)
                        mock_mode_set = True
                        logger.info("Mock GPU mode enabled via legacy module")
                    except ImportError as e:
                        exceptions.append(f"Error importing from legacy module: {e}")
                
                # If we still couldn't set mock mode, log all the errors
                if not mock_mode_set:
                    logger.warning("Could not enable mock GPU mode. Errors:")
                    for err in exceptions:
                        logger.warning(f"  - {err}")
                    logger.warning("Continuing with real GPU detection...")
            except Exception as e:
                logger.warning(f"Could not enable mock GPU mode: {e}")
        
        # Handle CLI mode
        if args.cli:
            logger.info("Running in CLI mode")
            
            # Import launcher after checking CLI mode
            try:
                from dualgpuopt.llm_launcher import main as launch_cli
            except ImportError:
                logger.error("CLI mode requires dualgpuopt.llm_launcher module")
                sys.exit(1)
            
            # Build CLI arguments
            cli_args = []
            if args.model:
                cli_args.extend(["--model", args.model])
            if args.ctx_size:
                cli_args.extend(["--ctx-size", str(args.ctx_size)])
            if args.quant:
                cli_args.extend(["--quant", args.quant])
            if args.export:
                cli_args.extend(["--export", args.export])
                
            # Launch CLI
            launch_cli(cli_args)
        
        # Default to GUI mode
        else:
            logger.info("Starting GUI application")
            
            # Check for tkinter first
            try:
                import tkinter as tk
                logger.debug("tkinter is available")
            except ImportError:
                logger.error("tkinter is not installed - required for GUI mode")
                logger.error("Please install tkinter (usually available in system packages)")
                sys.exit(1)
            
            # Try to use our compatibility UI module first
            try:
                from dualgpuopt.ui import get_themed_tk
                logger.debug("UI compatibility layer loaded")
                
                # Try to run the application using our compatible run_app
                try:
                    from dualgpuopt.gui import run_app
                    run_app()
                    return
                except ImportError as e:
                    logger.error(f"Failed to import GUI module: {e}")
            except ImportError as e:
                logger.warning(f"UI compatibility layer not available: {e}")
            
            # Fallback to traditional imports if compatibility layer fails
            logger.info("Trying alternative GUI initialization methods...")
            
            # Try to import ttkbootstrap for enhanced UI
            try:
                import ttkbootstrap
                logger.info("ttkbootstrap available for enhanced UI")
            except ImportError:
                logger.warning("ttkbootstrap not found - falling back to standard theme")
            
            # Import and run GUI - try multiple paths for backward compatibility
            gui_errors = []
            
            # Attempt 1: Modern GUI via run_app
            try:
                from dualgpuopt.gui import run_app
                run_app()
                return
            except ImportError as e:
                gui_errors.append(f"Failed to import modern GUI module: {e}")
            except Exception as e:
                gui_errors.append(f"Error running modern GUI: {e}")
            
            # Attempt 2: Legacy main_app.run
            try:
                from dualgpuopt.gui.main_app import run
                logger.info("Using legacy GUI via main_app")
                run()
                return
            except ImportError as e:
                gui_errors.append(f"Failed to import main_app: {e}")
            except Exception as e:
                gui_errors.append(f"Error running main_app: {e}")
            
            # Attempt 3: Legacy main_application.run
            try:
                from dualgpuopt.gui.main_application import run
                logger.info("Using legacy GUI via main_application")
                run()
                return
            except ImportError as e:
                gui_errors.append(f"Failed to import main_application: {e}")
            except Exception as e:
                gui_errors.append(f"Error running main_application: {e}")
            
            # Attempt 4: Simple UI
            try:
                from dualgpuopt.ui.simple import run_simple_ui
                logger.info("Using simple UI fallback")
                run_simple_ui()
                return
            except ImportError as e:
                gui_errors.append(f"Failed to import simple UI: {e}")
            except Exception as e:
                gui_errors.append(f"Error running simple UI: {e}")
            
            # If we get here, all GUI options failed
            logger.error("All GUI initialization attempts failed:")
            for err in gui_errors:
                logger.error(f"  - {err}")
            logger.error("No compatible UI modules found")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 