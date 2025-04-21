#!/usr/bin/env python3
"""
Direct build script for DualGPUOptimizer Modern UI.

This script builds a Windows executable without requiring spec files.
"""
import os
import sys
import subprocess
from pathlib import Path
import shutil

def ensure_icon_exists():
    """Ensure the icon file exists and return its path."""
    assets_dir = Path("dualgpuopt/assets")
    assets_dir.mkdir(exist_ok=True)

    target_ico = assets_dir / "windowsicongpu.ico"

    # Check if icon already exists
    if target_ico.exists():
        print(f"Icon file found at {target_ico}")
        return target_ico

    # Check potential source locations
    potential_sources = [
        Path("windowsicongpu.ico"),  # Root directory
        Path("integrated_app/dualgpuopt/assets/windowsicongpu.ico"),
        Path("dual_gpu_optimizer/dualgpuopt/assets/windowsicongpu.ico"),
    ]

    for source in potential_sources:
        if source.exists():
            print(f"Found icon at {source}, copying to {target_ico}")
            shutil.copy2(source, target_ico)
            return target_ico

    # If no icon found, try to generate one
    print("No icon found, attempting to generate one...")
    try:
        if Path("generate_icon.py").exists():
            subprocess.run([sys.executable, "generate_icon.py"], check=True)
            if target_ico.exists():
                print("Successfully generated icon file.")
                return target_ico
    except Exception as e:
        print(f"Error generating icon: {e}")

    print("Warning: Unable to find or generate icon file.")
    return None

def install_pyinstaller():
    """Ensure PyInstaller is installed."""
    try:
        print("PyInstaller is already installed.")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("PyInstaller installed successfully.")

def build_executable(icon_path):
    """Build the executable directly using PyInstaller command line."""
    print("Building executable...")

    # Determine build type
    onefile = input("Build as a single executable file? (y/n, default=y): ").strip().lower() != 'n'

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--name=DualGPUOptimizer",
        "--windowed",  # No console window
    ]

    # Add icon if available
    if icon_path:
        cmd.append(f"--icon={icon_path}")

    # Add onefile option if selected
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    # Add data files
    cmd.append("--add-data=dualgpuopt/assets/*;dualgpuopt/assets/")

    # Add hidden imports
    cmd.append("--hidden-import=ttkbootstrap")
    cmd.append("--hidden-import=PIL")
    cmd.append("--hidden-import=dualgpuopt.ui.widgets")
    cmd.append("--hidden-import=dualgpuopt.gui.modern_ui")

    # Add the script to build
    cmd.append("run_modern_ui.py")

    try:
        print(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

        exe_path = os.path.abspath("dist/DualGPUOptimizer.exe")
        if onefile:
            print(f"\n🎉 Build complete → {exe_path}")
        else:
            print(f"\n🎉 Build complete → {os.path.abspath('dist/DualGPUOptimizer/DualGPUOptimizer.exe')}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {e}")
        return False

def main():
    """Main entry point."""
    print("="*60)
    print("DualGPUOptimizer Modern UI Direct Build Script")
    print("="*60)

    # Ensure icon exists
    icon_path = ensure_icon_exists()

    # Install PyInstaller if needed
    install_pyinstaller()

    # Build the executable
    success = build_executable(icon_path)

    if success:
        print("\nBuild successful! You can find the executable in the 'dist' folder.")
        print("The taskbar icon should now display correctly when running the executable.")

        # Ask if user wants to run the executable
        if input("\nRun the executable now? (y/n): ").strip().lower() == 'y':
            if os.path.exists("dist/DualGPUOptimizer.exe"):
                subprocess.Popen(["dist/DualGPUOptimizer.exe"])
            elif os.path.exists("dist/DualGPUOptimizer/DualGPUOptimizer.exe"):
                subprocess.Popen(["dist/DualGPUOptimizer/DualGPUOptimizer.exe"])
    else:
        print("\nBuild failed. Please check the error messages above.")

    input("\nPress Enter to exit...")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())