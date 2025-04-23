#!/usr/bin/env python3
"""
Runner script for the integrated DualGPUOptimizer application.
"""
import argparse
import os
import sys

# Add the integrated_app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "integrated_app")))


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run the integrated DualGPUOptimizer application")
    parser.add_argument("--mock", action="store_true", help="Run with mock GPU data")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set up command line arguments to pass to the app
    sys_args = []
    if args.mock:
        sys_args.append("--mock")
    if args.verbose:
        sys_args.append("--verbose")

    # Replace sys.argv with our processed arguments
    sys.argv = [sys.argv[0]] + sys_args

    # Import and run the application
    try:
        from dualgpuopt.__main__ import main as app_main

        return app_main()
    except ImportError as e:
        print(f"Error importing application: {e}")
        print("Please ensure all dependencies are installed.")
        return 1
    except Exception as e:
        print(f"Error running application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
