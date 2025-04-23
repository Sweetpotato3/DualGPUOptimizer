"""
Runtime hook to ensure dualgpuopt.gui.constants can be loaded
This helps with PyInstaller bundling by adding fallback imports
"""
import importlib.util
import sys
from pathlib import Path

# If running from a frozen bundle, ensure constants.py can be found
if getattr(sys, "frozen", False):
    meipass = Path(sys._MEIPASS)

    # Create dualgpuopt.gui if needed
    if "dualgpuopt" not in sys.modules:
        dualgpuopt = type("dualgpuopt", (), {})
        sys.modules["dualgpuopt"] = dualgpuopt

        if not hasattr(dualgpuopt, "gui"):
            dualgpuopt.gui = type("gui", (), {})
            sys.modules["dualgpuopt.gui"] = dualgpuopt.gui

    # Try to load constants.py directly if needed
    if "dualgpuopt.gui.constants" not in sys.modules:
        constants_path = meipass / "dualgpuopt" / "gui" / "constants.py"

        if constants_path.exists():
            try:
                spec = importlib.util.spec_from_file_location(
                    "dualgpuopt.gui.constants",
                    constants_path,
                )
                constants = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(constants)
                sys.modules["dualgpuopt.gui.constants"] = constants

                # Add to dualgpuopt.gui
                if "dualgpuopt.gui" in sys.modules:
                    sys.modules["dualgpuopt.gui"].constants = constants
            except Exception as e:
                print(f"Error loading constants.py: {e}")
                # Continue app startup - don't crash
