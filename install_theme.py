#!/usr/bin/env python
"""
Theme Installation Script for DualGPUOptimizer
This script installs the pinned theme dependencies for DualGPUOptimizer.
"""

import subprocess
import sys
import importlib.util

def check_python_version():
    major, minor, _ = sys.version_info[:3]
    if major != 3 or minor < 9 or minor >= 12:
        print(f"WARNING: Current Python version ({sys.version.split()[0]}) may not be compatible.")
        print("Recommended: Python 3.9-3.11")
        if input("Continue anyway? (y/n): ").lower() != 'y':
            sys.exit(1)
    else:
        print(f"Python version: {sys.version.split()[0]} ✓")

def install_dependencies():
    packages = [
        "PySide6==6.5.3",
        "PyQtDarkTheme==2.1.0"
    ]
    
    print("Installing theme dependencies...")
    for package in packages:
        print(f"Installing {package}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Successfully installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    return True

def test_theme_import():
    print("Testing theme import...")
    try:
        # Use importlib to check if module is available without actually importing it
        if importlib.util.find_spec("qdarktheme") is not None:
            print("✓ Successfully found qdarktheme module")
            return True
        else:
            print("❌ Could not find qdarktheme module")
            return False
    except ImportError:
        print("❌ Failed to import qdarktheme module")
        return False

def main():
    print("=== DualGPUOptimizer Theme Setup ===")
    
    check_python_version()
    
    if install_dependencies() and test_theme_import():
        print("\n✅ Theme setup completed successfully!")
        print("You can now run the application with the dark theme.")
    else:
        print("\n❌ Theme setup encountered issues.")
        print("The application will still run but may not have the dark theme applied.")
        
    print("\nTo manually install the theme dependencies:")
    print("  pip install PySide6==6.5.3 PyQtDarkTheme==2.1.0")
    
    print("\nNext:  activate your venv  ➜  python -m dualgpuopt.qt.app_window")

if __name__ == "__main__":
    main() 