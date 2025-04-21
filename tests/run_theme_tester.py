"""
Script to run the theme tester tool
"""
import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Import necessary modules
try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    print("Error: Tkinter is not available. Please install Python with Tkinter support.")
    sys.exit(1)

# Import theme tester
try:
    from dualgpuopt.gui.theme_tester import run_theme_tester
    print("Starting theme tester application...")
    run_theme_tester()
except ImportError as e:
    print(f"Error importing theme tester: {e}")
    print("\nChecking available modules:")

    # Check for the presence of critical modules
    modules_to_check = [
        "dualgpuopt.gui.theme",
        "dualgpuopt.gui.theme_selector",
        "dualgpuopt.gui.theme_observer",
        "dualgpuopt.gui.themed_widgets",
        "dualgpuopt.services.event_service",
        "dualgpuopt.services.config_service"
    ]

    for module in modules_to_check:
        try:
            __import__(module)
            print(f"  ✓ {module}: Available")
        except ImportError as err:
            print(f"  ✗ {module}: Not available ({err})")

    print("\nCheck directory structure:")
    for directory in ["dualgpuopt", "dualgpuopt/gui", "dualgpuopt/services"]:
        if os.path.exists(directory):
            print(f"  ✓ {directory}: Exists")
            files = os.listdir(directory)
            print(f"    Contents: {', '.join(files)}")
        else:
            print(f"  ✗ {directory}: Does not exist")

    sys.exit(1)