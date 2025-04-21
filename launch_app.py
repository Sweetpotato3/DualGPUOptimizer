#!/usr/bin/env python3
"""
Launcher script for DualGPUOptimizer.
Sets up the Python path and runs the application with mock GPU mode.
"""
import os
import sys
import pathlib
import logging

def setup_environment():
    """Set up the environment for running the application."""
    # Get the current directory
    current_dir = pathlib.Path(__file__).parent.resolve()
    package_dir = current_dir / "dual_gpu_optimizer"

    # Add to sys.path
    sys.path.insert(0, str(current_dir))
    sys.path.insert(0, str(package_dir))

    # Set environment variable for mock GPU mode
    os.environ["DGPUOPT_MOCK_GPUS"] = "1"

    return True

def run_application():
    """Run the application."""
    try:
        # Import the main module
        from dual_gpu_optimizer.dualgpuopt import __main__ as app_main

        # Call the main function
        return app_main.main()
    except ImportError as e:
        print(f"Error importing application modules: {e}")

        # Try an alternative method
        try:
            # Set up direct access to the modules
            dualgpuopt_path = pathlib.Path(__file__).parent / "dual_gpu_optimizer" / "dualgpuopt"
            sys.path.insert(0, str(dualgpuopt_path))

            # Try importing GUI components directly
            from dualgpuopt.gui import run_app

            # Run the app
            print("Running application directly...")
            run_app()
            return 0
        except ImportError as e2:
            print(f"Failed to run application directly: {e2}")
            return 1

def main():
    """Main entry point."""
    # Set up basic logging first
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set up the environment
    if not setup_environment():
        print("Failed to set up environment")
        return 1

    # Run the application
    try:
        return run_application()
    except Exception as e:
        print(f"Error running application: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())