#!/usr/bin/env python3
"""
Main entry point for the Qt version of DualGPUOptimizer.
"""

import sys
import os
import logging
from datetime import datetime

def setup_qt_directories():
    """Ensure dualgpuopt and its qt submodule are in the Python path."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Create required directories
    os.makedirs('logs', exist_ok=True)

def check_dependencies():
    """Check if required dependencies are installed."""
    missing_deps = []
    
    try:
        import PySide6
        print("✓ PySide6 is installed")
    except ImportError:
        missing_deps.append("PySide6")
        print("✗ PySide6 is not installed")
    
    if missing_deps:
        print("\nMissing dependencies:")
        print("  " + "\n  ".join(missing_deps))
        print("\nPlease install the missing dependencies:")
        print("  pip install " + " ".join(missing_deps))
        return False
    
    return True

def main():
    """Main entry point."""
    # Set up directories
    setup_qt_directories()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Run the Qt application
    try:
        from dualgpuopt.qt.main import main
        sys.exit(main())
    except ImportError as e:
        print(f"Error importing Qt application modules: {e}")
        print("Make sure the directory structure is correct.")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 