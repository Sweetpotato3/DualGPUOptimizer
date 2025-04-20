#!/usr/bin/env python3
"""
Test script to check if the constants module can be imported
"""

try:
    from dualgpuopt.gui.constants import *
    print("Constants loaded successfully!")
    print(f"APP_NAME: {APP_NAME}")
    print(f"THEME: {THEME}")
    print(f"GPU_COLORS: {GPU_COLORS}")
except Exception as e:
    print(f"Error importing constants: {e}") 