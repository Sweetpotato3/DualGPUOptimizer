#!/usr/bin/env python3
"""
Build script for creating standalone executable of DualGPUOptimizer
Uses PyInstaller to package the application
"""
import os
import sys
import subprocess
import platform
import shutil
import argparse
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed, install if not"""
    try:
        print("PyInstaller is already installed")
        return True
    except ImportError:
        print("PyInstaller is not installed. Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("Failed to install PyInstaller")
            return False

def get_icon_path():
    """Get the path to the application icon"""
    # Check different possible locations
    icon_paths = [
        "dualgpuopt/resources/icon.ico",
        "dualgpuopt/resources/icon.png",
        "dualgpuopt/assets/icon.ico",
        "dualgpuopt/assets/icon.png"
    ]

    for path in icon_paths:
        if os.path.exists(path):
            # Convert PNG to ICO if on Windows and only PNG available
            if platform.system() == "Windows" and path.endswith(".png"):
                try:
                    from PIL import Image
                    ico_path = path.replace(".png", ".ico")
                    Image.open(path).save(ico_path)
                    return ico_path
                except ImportError:
                    print("Pillow not installed, using PNG icon")
                    return path
            return path

    # No icon found
    print("No application icon found")
    return None

def copy_runtime_dependencies():
    """Copy runtime dependencies to include with the executable"""
    runtime_dir = Path("runtime_dependencies")
    runtime_dir.mkdir(exist_ok=True)

    # Copy any additional runtime files here
    # For example, default config, themes, etc.
    print("Copying runtime dependencies...")
    for path in ["LICENSE", "README.md"]:
        if os.path.exists(path):
            shutil.copy(path, runtime_dir)

    # Create an empty config directory
    config_dir = runtime_dir / "config"
    config_dir.mkdir(exist_ok=True)

    return runtime_dir

def build_executable(args):
    """Build the executable using PyInstaller"""
    # Verify PyInstaller is installed
    if not check_pyinstaller():
        print("Cannot proceed without PyInstaller")
        return False

    # Determine icon path
    icon_path = get_icon_path()
    icon_option = [f"--icon={icon_path}"] if icon_path else []

    # Create runtime dependencies
    runtime_dir = copy_runtime_dependencies()

    # Determine entry point
    if args.direct:
        entry_point = "run_direct_app.py"
        output_name = "DualGPUOptimizer-Direct"
    else:
        entry_point = "dualgpuopt/__main__.py"
        output_name = "DualGPUOptimizer"

    # Build additional options
    additional_options = []

    # Add hidden imports
    hidden_imports = [
        "--hidden-import=tkinter",
        "--hidden-import=dualgpuopt.gpu",
        "--hidden-import=dualgpuopt.ui",
        "--hidden-import=dualgpuopt.error_handler"
    ]
    additional_options.extend(hidden_imports)

    # Add data files
    data_files = [
        f"--add-data={runtime_dir};runtime_dependencies"
    ]
    additional_options.extend(data_files)

    # Add exclusions to reduce size
    excludes = [
        "--exclude-module=matplotlib",
        "--exclude-module=PySide2",
        "--exclude-module=PySide6",
        "--exclude-module=PyQt5",
        "--exclude-module=PyQt6",
        "--exclude-module=IPython"
    ]
    additional_options.extend(excludes)

    # One-file or one-dir mode
    if args.onefile:
        additional_options.append("--onefile")
    else:
        additional_options.append("--onedir")

    # Add name
    additional_options.append(f"--name={output_name}")

    # Add console window toggle
    if args.console:
        additional_options.append("--console")
    else:
        additional_options.append("--noconsole")

    # Build the command
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        *icon_option,
        *additional_options,
        entry_point
    ]

    # Print command for debugging
    print("Running command:", " ".join(command))

    # Run PyInstaller
    try:
        subprocess.run(command, check=True)
        print(f"Build successful! Executable created in dist/{output_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False

def clean_build_files():
    """Clean up build artifacts"""
    paths_to_remove = ["build", "*.spec"]

    for path in paths_to_remove:
        if "*" in path:
            for file_path in Path(".").glob(path):
                if file_path.is_file():
                    file_path.unlink()
                    print(f"Removed {file_path}")
        else:
            path_obj = Path(path)
            if path_obj.exists():
                if path_obj.is_dir():
                    shutil.rmtree(path_obj)
                else:
                    path_obj.unlink()
                print(f"Removed {path_obj}")

    # Don't remove the dist directory as it contains the built executable
    print("Clean up completed")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Build DualGPUOptimizer executable")

    parser.add_argument("--direct", action="store_true",
                        help="Build the direct app version (run_direct_app.py)")
    parser.add_argument("--onefile", action="store_true",
                        help="Build a single executable file (default is directory)")
    parser.add_argument("--console", action="store_true",
                        help="Include console window for debugging (default is hidden)")
    parser.add_argument("--clean", action="store_true",
                        help="Clean build artifacts after successful build")

    args = parser.parse_args()

    print("Building DualGPUOptimizer executable...")

    success = build_executable(args)

    if success and args.clean:
        clean_build_files()

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())