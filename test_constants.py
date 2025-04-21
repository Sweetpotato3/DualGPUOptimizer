#!/usr/bin/env python3
"""
Test script to check if the constants module can be imported
"""

import sys
import os

# Print Python path for debugging
print("Python Path:")
for p in sys.path:
    print(f"  - {p}")

print("\nChecking for module files:")
if os.path.exists("dualgpuopt/gui/constants.py"):
    print("Found constants.py")
else:
    print("constants.py not found")

# Try importing directly from the file
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "constants", "dualgpuopt/gui/constants.py"
    )
    constants = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(constants)
    print("\nDirect import successful!")
    print(f"APP_NAME: {constants.APP_NAME}")
    print(f"THEME: {constants.THEME}")
    print(f"GPU_COLORS: {constants.GPU_COLORS}")
except Exception as e:
    print(f"\nError with direct import: {e}")

# Try normal import
try:
    from dualgpuopt.gui import constants
    print("\nModule import successful!")
    print(f"APP_NAME: {constants.APP_NAME}")
    print(f"THEME: {constants.THEME}")
    print(f"GPU_COLORS: {constants.GPU_COLORS}")
except Exception as e:
    print(f"\nError with module import: {e}")