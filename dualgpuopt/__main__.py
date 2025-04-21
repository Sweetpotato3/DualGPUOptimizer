"""
Main entry point for DualGPUOptimizer
"""
import sys
import logging
import argparse
import traceback
from pathlib import Path
import importlib.util

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger("DualGPUOpt.Main")

# Create a logs directory if it doesn't exist
try:
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    # Add file handler to log to a file as well
    file_handler = logging.FileHandler(logs_dir / "dualgpuopt.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)
    logger.info(f"Logging to {(logs_dir / 'dualgpuopt.log').absolute()}")
except Exception as e:
    logger.warning(f"Could not set up file logging: {e}")

def check_module_availability(module_name):
    """Check if a Python module is available

    Args:
        module_name: Name of the module to check

    Returns:
        True if the module is available, False otherwise
    """
    return importlib.util.find_spec(module_name) is not None

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
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies and exit")
    parser.add_argument("--install-deps", action="store_true", help="Install missing dependencies")
    return parser.parse_args()

def setup_mock_mode(args):
    """Set up mock mode if requested

    Args:
        args: Command line arguments

    Returns:
        True if mock mode was successfully enabled, False otherwise
    """
    if not args.mock:
        return False

    # Try multiple methods to enable mock mode for maximum compatibility
    try:
        # Try dependency manager first
        if check_module_availability("dualgpuopt.dependency_manager"):
            try:
                from dualgpuopt.dependency_manager import DynamicImporter
                gpu_compat = DynamicImporter.import_gpu_compat()
                gpu_compat["set_mock_mode"](True)
                logger.info("Mock GPU mode enabled via dependency manager")
                return True
            except Exception as e:
                logger.debug(f"Could not enable mock mode via dependency manager: {e}")

        # Try direct import methods in order of preference
        methods = [
            # (module, function, message)
            ("dualgpuopt.gpu.compat", "set_mock_mode", "via compatibility layer"),
            ("dualgpuopt.gpu.mock", "set_mock_mode", "via refactored module"),
            ("dualgpuopt.gpu", "set_mock_mode", "via module init"),
            ("dualgpuopt.gpu_info", "set_mock_mode", "via legacy module")
        ]

        for module_name, function_name, message in methods:
            try:
                module = importlib.import_module(module_name)
                set_mock_mode = getattr(module, function_name)
                set_mock_mode(True)
                logger.info(f"Mock GPU mode enabled {message}")
                return True
            except (ImportError, AttributeError) as e:
                logger.debug(f"Could not enable mock mode {message}: {e}")

        # None of the methods worked
        logger.warning("Could not enable mock GPU mode via any known method")
        logger.warning("Continuing with real GPU detection...")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error setting up mock mode: {e}")
        return False

def check_and_warn_missing_modules():
    """Check for commonly needed optional modules and warn if missing

    Returns:
        Dictionary mapping module names to their availability status
    """
    modules = {
        "pynvml": {"available": False, "message": "GPU monitoring will be limited"},
        "numpy": {"available": False, "message": "Optimization features will be limited"},
        "torch": {"available": False, "message": "Advanced GPU features will be unavailable"},
        "requests": {"available": False, "message": "Chat functionality will be unavailable"},
        "sseclient": {"available": False, "message": "Chat streaming will be unavailable"},
        "ttkbootstrap": {"available": False, "message": "UI will use basic theming"},
        "ttkthemes": {"available": False, "message": "Theme options will be limited"},
        "ttkwidgets": {"available": False, "message": "Some UI widgets will be unavailable"}
    }

    for module_name in modules:
        modules[module_name]["available"] = check_module_availability(module_name)
        if not modules[module_name]["available"]:
            logger.warning(f"{module_name} is not installed - {modules[module_name]['message']}")

    return modules

def handle_chat_module():
    """Patch the chat module import to handle missing dependencies gracefully

    Makes sure the chat tab can be loaded even when requests or sseclient are missing
    """
    # Only proceed if chat_tab.py exists but requests or sseclient are missing
    chat_path = Path(__file__).parent / "chat_tab.py"
    if not chat_path.exists():
        return

    requests_available = check_module_availability("requests")
    sseclient_available = check_module_availability("sseclient")

    if requests_available and sseclient_available:
        logger.debug("Chat dependencies are available - no patching needed")
        return

    logger.info("Ensuring chat module can load despite missing dependencies")

    try:
        import sys
        from types import ModuleType

        # Create mock modules if needed
        if not requests_available:
            requests_mock = ModuleType("requests")
            requests_mock.post = lambda *args, **kwargs: None
            sys.modules["requests"] = requests_mock
            logger.debug("Created mock requests module")

        if not sseclient_available:
            sseclient_mock = ModuleType("sseclient")
            sseclient_mock.SSEClient = lambda *args, **kwargs: []
            sys.modules["sseclient"] = sseclient_mock
            logger.debug("Created mock sseclient module")

        logger.info("Chat module dependencies have been mocked for graceful loading")
    except Exception as e:
        logger.warning(f"Could not patch chat module dependencies: {e}")

def main():
    """Main entry point"""
    args = parse_args()

    # Set verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Print application header
    logger.info("==== DualGPUOptimizer ====")

    try:
        # Import dependency_manager first - will be the same regardless of other imports
        try:
            from dualgpuopt.dependency_manager import (
                initialize_dependency_status,
                verify_core_dependencies,
                print_dependency_status,
                get_missing_dependencies,
                install_dependencies,
                DynamicImporter
            )
            logger.debug("Dependency manager imported successfully")

            # Initialize dependency state
            initialize_dependency_status()

            # Handle dependency checking and installation if requested
            if args.check_deps:
                print_dependency_status(include_errors=args.verbose)
                return

            if args.install_deps:
                missing = get_missing_dependencies()
                if missing:
                    logger.info("Installing missing dependencies...")
                    success = install_dependencies(missing)
                    if success:
                        logger.info("Dependencies installed successfully")
                    else:
                        logger.error("Some dependencies could not be installed")
                else:
                    logger.info("All dependencies are already installed")
                return

            # Verify required dependencies first
            core_available, critical_missing = verify_core_dependencies()
            if not core_available:
                logger.error(f"Critical dependencies missing: {', '.join(critical_missing)}")
                logger.error("Run with --install-deps to attempt installation")
                sys.exit(1)

        except ImportError as e:
            logger.error(f"Could not import dependency manager: {e}")
            logger.warning("Continuing with basic dependency checks...")
            # Run our own basic dependency check
            dependency_status = check_and_warn_missing_modules()

        # Enable mock mode if requested
        mock_enabled = setup_mock_mode(args)
        if args.mock and not mock_enabled:
            logger.warning("Mock mode was requested but could not be enabled")

        # Handle missing chat module dependencies
        handle_chat_module()

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

            # Try to use our new dependency manager for tkinter checking
            try:
                if "DynamicImporter" in locals():
                    ttk = DynamicImporter.import_ui()
                    logger.debug("UI module imported via dependency manager")
                else:
                    # Check for tkinter directly
                    logger.debug("tkinter is available")
            except ImportError:
                logger.error("tkinter is not installed - required for GUI mode")
                logger.error("Please install tkinter (usually available in system packages)")
                sys.exit(1)

            # FIRST ATTEMPT: Try direct app approach (most reliable)
            # This is the recommended approach
            try:
                # Try to import the direct app from the module
                import run_direct_app
                logger.info("Running direct application (most stable approach)")
                # Call the main function with mock mode flag
                if hasattr(run_direct_app, "main"):
                    logger.debug("Using run_direct_app.main()")
                    if args.mock:
                        # Pass any other arguments here if needed
                        run_direct_app.main(mock=True)
                    else:
                        run_direct_app.main()
                    return
                elif args.mock:
                    # Set the module-level mock flag if it exists
                    if hasattr(run_direct_app, "MOCK_MODE"):
                        run_direct_app.MOCK_MODE = True
                return
            except ImportError as e:
                logger.warning(f"Direct app module not available: {e}")
            except Exception as e:
                logger.error(f"Error running direct app module: {e}")
                logger.debug(traceback.format_exc())

            # SECOND ATTEMPT: Try using our direct launcher
            try:
                # Import the direct app launcher which has better dependency handling
                from dualgpuopt.direct_launcher import run_direct_app
                logger.info("Using direct application launcher with improved dependency handling")
                run_direct_app(mock=args.mock)
                return
            except ImportError as e:
                logger.warning(f"Direct app launcher not available: {e}")
            except Exception as e:
                logger.error(f"Error running direct app launcher: {e}")
                logger.debug(traceback.format_exc())

            # THIRD ATTEMPT: Try modern UI with compatibility layer
            try:
                logger.debug("UI compatibility layer loaded")

                # Try to run the application using our compatible run_app
                try:
                    from dualgpuopt.gui import run_app
                    logger.info("Using modern GUI with compatibility layer")
                    run_app()
                    return
                except ImportError as e:
                    logger.error(f"Failed to import GUI module: {e}")
                except Exception as e:
                    logger.error(f"Error running GUI module: {e}")
                    logger.debug(traceback.format_exc())
            except ImportError as e:
                logger.warning(f"UI compatibility layer not available: {e}")

            # FOURTH ATTEMPT: Try multiple fallback approaches
            # Keep track of attempted methods and errors
            gui_attempts = []

            # Import and run GUI - try multiple paths for backward compatibility
            logger.info("Trying alternative GUI initialization methods...")

            # Try to import ttkbootstrap for enhanced UI - just informational
            try:
                logger.info("ttkbootstrap available for enhanced UI")
            except ImportError:
                logger.warning("ttkbootstrap not found - falling back to standard theme")

            # Attempt 1: Modern GUI via run_app
            try:
                from dualgpuopt.gui import run_app
                logger.info("Using modern GUI via direct import")
                gui_attempts.append(("Modern GUI", None))
                run_app()
                return
            except ImportError as e:
                error_msg = f"Failed to import modern GUI module: {e}"
                gui_attempts.append(("Modern GUI", error_msg))
                logger.warning(error_msg)
            except Exception as e:
                error_msg = f"Error running modern GUI: {e}"
                gui_attempts.append(("Modern GUI", error_msg))
                logger.warning(error_msg)
                logger.debug(traceback.format_exc())

            # Attempt 2: Legacy main_app.run
            try:
                from dualgpuopt.gui.main_app import run
                logger.info("Using legacy GUI via main_app")
                gui_attempts.append(("Legacy main_app", None))
                run()
                return
            except ImportError as e:
                error_msg = f"Failed to import main_app: {e}"
                gui_attempts.append(("Legacy main_app", error_msg))
                logger.warning(error_msg)
            except Exception as e:
                error_msg = f"Error running main_app: {e}"
                gui_attempts.append(("Legacy main_app", error_msg))
                logger.warning(error_msg)
                logger.debug(traceback.format_exc())

            # Attempt 3: Legacy main_application.run
            try:
                from dualgpuopt.gui.main_application import run
                logger.info("Using legacy GUI via main_application")
                gui_attempts.append(("Legacy main_application", None))
                run()
                return
            except ImportError as e:
                error_msg = f"Failed to import main_application: {e}"
                gui_attempts.append(("Legacy main_application", error_msg))
                logger.warning(error_msg)
            except Exception as e:
                error_msg = f"Error running main_application: {e}"
                gui_attempts.append(("Legacy main_application", error_msg))
                logger.warning(error_msg)
                logger.debug(traceback.format_exc())

            # Attempt 4: Simple UI
            try:
                from dualgpuopt.ui.simple import run_simple_ui
                logger.info("Using simple UI fallback")
                gui_attempts.append(("Simple UI", None))
                run_simple_ui()
                return
            except ImportError as e:
                error_msg = f"Failed to import simple UI: {e}"
                gui_attempts.append(("Simple UI", error_msg))
                logger.warning(error_msg)
            except Exception as e:
                error_msg = f"Error running simple UI: {e}"
                gui_attempts.append(("Simple UI", error_msg))
                logger.warning(error_msg)
                logger.debug(traceback.format_exc())

            # Last resort: Try importing direct app again but with different approach
            try:
                from run_direct_app import main as direct_app_main
                logger.info("Running direct app function as last resort")
                gui_attempts.append(("Direct app function", None))
                direct_app_main()
                return
            except ImportError as e:
                error_msg = f"Failed to import direct app function: {e}"
                gui_attempts.append(("Direct app function", error_msg))
                logger.warning(error_msg)
            except Exception as e:
                error_msg = f"Error running direct app function: {e}"
                gui_attempts.append(("Direct app function", error_msg))
                logger.warning(error_msg)
                logger.debug(traceback.format_exc())

            # If we get here, all GUI options failed
            logger.error("All GUI initialization attempts failed:")
            for method, error in gui_attempts:
                if error:
                    logger.error(f"  - {method}: {error}")
                else:
                    logger.error(f"  - {method}: Unknown error")

            # Provide a helpful error message with suggestions
            logger.error("\nTroubleshooting suggestions:")
            logger.error("1. Run with --install-deps to install missing dependencies")
            logger.error("2. Run with --check-deps to see what dependencies are missing")
            logger.error("3. Download and run the direct app from the latest release")
            logger.error("4. Check the logs for detailed error information")
            logger.error("5. Try running with --mock flag for testing without GPUs")

            sys.exit(1)

    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()