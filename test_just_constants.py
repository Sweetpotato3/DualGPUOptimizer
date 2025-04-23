#!/usr/bin/env python3
"""
Test script that imports only the constants module directly
"""
import importlib.util
from pathlib import Path

# Direct import without going through __init__.py
constants_path = Path("dualgpuopt/gui/constants.py")
if constants_path.exists():
    print(f"Found constants.py at {constants_path.absolute()}")

    try:
        spec = importlib.util.spec_from_file_location(
            "constants",
            str(constants_path),
        )
        constants = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(constants)

        print("Constants module loaded successfully!")
        print(f"APP_NAME: {constants.APP_NAME}")
        print(f"THEME: {constants.THEME}")
        if hasattr(constants, "GPU_COLORS"):
            print(f"GPU_COLORS: {constants.GPU_COLORS}")
    except Exception as e:
        print(f"Error loading constants directly: {e}")
else:
    print(f"Constants file not found at {constants_path.absolute()}")
