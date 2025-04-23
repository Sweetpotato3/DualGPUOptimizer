#!/usr/bin/env python3
"""
Minimalist launcher for the modern UI
Directly runs our GUI class
"""
import sys
from pathlib import Path

# Add this to the Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Import our modules directly without going through package imports

    # Directly load the GUI module and extract the class
    import importlib.util
    from pathlib import Path

    # Path to gui.py
    gui_path = Path(__file__).parent / "dualgpuopt" / "gui.py"

    # Load the module
    spec = importlib.util.spec_from_file_location("gui", gui_path)
    gui = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gui)

    # Now run the app
    print("Starting modern UI...")
    app = gui.DualGUI()
    app.mainloop()

except Exception as e:
    print(f"Error starting modern UI: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
