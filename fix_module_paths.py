#!/usr/bin/env python3
"""
Fix module path issues for the DualGPUOptimizer application.
"""
import sys
import os
import pathlib
import importlib
import importlib.util

def check_module(module_name):
    """Check if a module can be imported."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError as e:
        print(f"Cannot import {module_name}: {e}")
        return False

def fix_module_paths():
    """Add necessary paths to sys.path to fix import issues."""
    # Get the current directory
    current_dir = pathlib.Path(__file__).parent.resolve()
    package_dir = current_dir / "dual_gpu_optimizer"

    print(f"Current directory: {current_dir}")
    print(f"Package directory: {package_dir}")

    # Add the package directory to sys.path
    sys.path.insert(0, str(current_dir))

    # Check if constants.py exists
    constants_path = package_dir / "dualgpuopt" / "gui" / "constants.py"
    print(f"Constants path: {constants_path}")
    if not constants_path.exists():
        print(f"Error: constants.py not found at {constants_path}")
        return False

    # Check if we can import the module now
    result = check_module("dual_gpu_optimizer.dualgpuopt.gui.constants")
    if not result:
        print("Cannot import constants module even after adding to sys.path")

        # Let's try adding the specific directory
        gui_dir = package_dir / "dualgpuopt" / "gui"
        sys.path.insert(0, str(gui_dir.parent))
        print(f"Added {gui_dir.parent} to sys.path")

        # Try creating a constants.py file directly in the package
        try:
            with open(constants_path, "r") as src_file:
                constants_content = src_file.read()

            # Create __init__.py files if not present
            init_paths = [
                package_dir / "dualgpuopt" / "__init__.py",
                package_dir / "dualgpuopt" / "gui" / "__init__.py"
            ]

            for init_path in init_paths:
                if not init_path.exists():
                    with open(init_path, "w") as init_file:
                        init_file.write('"""Module initialization."""\n')
                    print(f"Created {init_path}")

            # Try importing again
            result = check_module("dual_gpu_optimizer.dualgpuopt.gui.constants")
            if not result:
                # One last attempt with a more direct approach
                sys.path.insert(0, str(gui_dir))
                print(f"Added {gui_dir} to sys.path")
                result = check_module("constants")
        except Exception as e:
            print(f"Error trying to fix module paths: {e}")
            return False

    return result

def main():
    """Main entry point."""
    # Try to fix module paths
    if fix_module_paths():
        print("Module paths fixed successfully")
        return 0
    else:
        print("Failed to fix module paths")
        return 1

if __name__ == "__main__":
    sys.exit(main())