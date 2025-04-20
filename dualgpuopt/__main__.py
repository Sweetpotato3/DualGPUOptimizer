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
                # Try both the new and old GPU module structure
                try:
                    from dualgpuopt.gpu import set_mock_mode
                except ImportError:
                    from dualgpuopt.gpu_info import set_mock_mode
                
                set_mock_mode(True)
                logger.info("Mock GPU mode enabled")
            except ImportError:
                logger.warning("Could not enable mock GPU mode")
        
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
            
            # Check for required dependencies before importing GUI
            try:
                import tkinter as tk
                # Try to import ttkbootstrap - not required but preferred
                try:
                    import ttkbootstrap
                    logger.info("ttkbootstrap available for enhanced UI")
                except ImportError:
                    logger.warning("ttkbootstrap not found - falling back to standard theme")
                
                # Import and run modern GUI
                try:
                    from dualgpuopt.gui import run_app
                    run_app()
                except ImportError as e:
                    logger.error(f"Failed to import GUI module: {e}")
                    # Try fallback to basic GUI
                    try:
                        # Try multiple possible module paths for backward compatibility
                        try:
                            from dualgpuopt.gui.main_app import run
                        except ImportError:
                            from dualgpuopt.gui.main_application import run
                            
                        logger.info("Using fallback GUI")
                        run()
                    except ImportError as e2:
                        logger.error(f"Failed to import fallback GUI module: {e2}")
                        
                        # Last resort fallback - try simple UI
                        try:
                            from dualgpuopt.ui.simple import run_simple_ui
                            logger.info("Using simple UI fallback")
                            run_simple_ui()
                        except ImportError:
                            logger.error("No compatible UI modules found")
                            sys.exit(1)
                        
            except ImportError as e:
                logger.error(f"Failed to initialize GUI: {e}")
                logger.error("Make sure tkinter is installed")
                sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 