#!/usr/bin/env python3
"""
Standalone launcher for modern UI
"""
import sys
from pathlib import Path

# Get the absolute path to this script
script_dir = Path(__file__).resolve().parent

# Add the parent directory to sys.path
parent_dir = str(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Make sure we can import from dualgpuopt

# Try to import ttkbootstrap
try:
    import ttkbootstrap

    print("ttkbootstrap is available")
except ImportError:
    print("ttkbootstrap is not available - UI will use standard ttk theme")

# Try to import our custom widgets
try:
    from dualgpuopt.ui.neon import GradientBar, NeonButton, init_theme

    print("Custom UI components found")
except ImportError as e:
    print(f"Error importing custom UI components: {e}")
    sys.exit(1)

# Import the GUI class directly, not through importing the function
try:
    # Import the GUI module
    from dualgpuopt.gui import DualGUI

    print("Starting modern UI...")

    # Create and run the UI
    app = DualGUI()
    app.mainloop()
except Exception as e:
    print(f"Error starting UI: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
