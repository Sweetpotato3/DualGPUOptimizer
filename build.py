#!/usr/bin/env python3
"""
Build script for DualGPUOptimizer using PyInstaller.
"""
import os
import subprocess
import sys
from pathlib import Path

def main():
    """
    Build the application with PyInstaller using our custom spec.
    """
    print("Building DualGPUOptimizer application...")
    
    # Create hooks directory if it doesn't exist
    hooks_dir = Path("hooks")
    hooks_dir.mkdir(exist_ok=True)
    
    # Run PyInstaller with our spec file
    cmd = [
        "pyinstaller",
        "DualGPUOptimizer.spec",
        "--noconfirm",
        "--clean"
    ]
    
    result = subprocess.run(cmd, check=False)
    
    if result.returncode != 0:
        print("❌ Build failed!")
        sys.exit(1)
    
    print("✅ Build completed successfully!")
    print(f"Application is available at: {os.path.abspath('dist/DualGPUOptimizer')}")

if __name__ == "__main__":
    main() 