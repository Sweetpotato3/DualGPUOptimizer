#!/usr/bin/env python3
"""
Build script for DualGPUOptimizer Modern UI.

This script builds a Windows executable with proper taskbar icon.
"""
import os
import sys
import subprocess
from pathlib import Path

def ensure_icon_exists():
    """Ensure the icon file exists in the assets directory."""
    assets_dir = Path("dualgpuopt/assets")
    assets_dir.mkdir(exist_ok=True)

    target_ico = assets_dir / "windowsicongpu.ico"

    # Check if icon already exists
    if target_ico.exists():
        print(f"Icon file found at {target_ico}")
        return True

    # Check potential source locations
    potential_sources = [
        Path("windowsicongpu.ico"),  # Root directory
        Path("integrated_app/dualgpuopt/assets/windowsicongpu.ico"),
        Path("dual_gpu_optimizer/dualgpuopt/assets/windowsicongpu.ico"),
    ]

    for source in potential_sources:
        if source.exists():
            print(f"Found icon at {source}, copying to {target_ico}")
            import shutil
            shutil.copy2(source, target_ico)
            return True

    # If no icon found, try to generate one
    print("No icon found, attempting to generate one...")
    try:
        if Path("generate_icon.py").exists():
            subprocess.run([sys.executable, "generate_icon.py"], check=True)
            if target_ico.exists():
                print("Successfully generated icon file.")
                return True
        else:
            print("Warning: generate_icon.py not found.")
    except Exception as e:
        print(f"Error generating icon: {e}")

    print("Warning: Unable to find or generate icon file.")
    return False

def install_pyinstaller():
    """Ensure PyInstaller is installed."""
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("PyInstaller installed successfully.")

def build_executable():
    """Build the executable using PyInstaller."""
    print("Building executable...")

    # Determine which spec file to use
    onefile = input("Build as a single executable file? (y/n, default=y): ").strip().lower() != 'n'

    spec_file = "DualGPUOptimizer_onefile.spec" if onefile else "DualGPUOptimizer_modern.spec"

    try:
        # Run PyInstaller
        subprocess.run([
            sys.executable,
            "-m",
            "PyInstaller",
            spec_file,
            "--clean"
        ], check=True)

        print(f"\n🎉 Build complete → {os.path.abspath('dist/DualGPUOptimizer.exe')}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {e}")
        return False

def main():
    """Main entry point."""
    print("="*60)
    print("DualGPUOptimizer Modern UI Build Script")
    print("="*60)

    # Ensure icon exists
    ensure_icon_exists()

    # Install PyInstaller if needed
    install_pyinstaller()

    # Build the executable
    success = build_executable()

    if success:
        print("\nBuild successful! You can find the executable in the 'dist' folder.")
        print("The taskbar icon should now display correctly when running the executable.")
    else:
        print("\nBuild failed. Please check the error messages above.")

    input("\nPress Enter to exit...")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())