#!/usr/bin/env python
"""
Build script for DualGPUOptimizer
Creates an executable package using PyInstaller
"""

import sys
import shutil
import subprocess
from pathlib import Path

def run_command(cmd):
    """Run a command and print output"""
    print(f"Running: {cmd}")
    process = subprocess.run(cmd, shell=True, check=False)
    return process.returncode == 0

def create_bootstrap_file():
    """Create a bootstrap file to ensure the app starts in the correct directory"""
    bootstrap_content = """
import os
import sys

# Make sure we're running from the correct directory
if getattr(sys, 'frozen', False):
    # We're running in a PyInstaller bundle
    bundle_dir = os.path.dirname(sys.executable)
    # Change to the directory containing the executable
    os.chdir(bundle_dir)
    print(f"Working directory set to: {bundle_dir}")

# Import the actual entry point
from run_optimizer import main
main()
"""

    with open("bootstrap.py", "w") as f:
        f.write(bootstrap_content)

    print("Created bootstrap.py file")
    return True

def install_dependencies():
    """Install required dependencies for the build"""
    dependencies = [
        "pyinstaller",
        "pillow",
        "ttkthemes",
        "pynvml"
    ]

    for dep in dependencies:
        print(f"Ensuring {dep} is installed...")
        run_command(f"pip install {dep}")

    return True

def build_executable():
    """Build the executable package"""
    # First fix ttkbootstrap escape sequences
    if Path("fix_ttkbootstrap.py").exists():
        print("Fixing ttkbootstrap escape sequences...")
        run_command("python fix_ttkbootstrap.py")

    # Install dependencies
    install_dependencies()

    # Generate icons if needed
    if not (Path("dualgpuopt/resources/icon.ico").exists() and Path("dualgpuopt/resources/icon.png").exists()):
        print("Generating application icons...")
        if Path("create_icon.py").exists():
            run_command("python create_icon.py")
        else:
            print("Warning: create_icon.py not found, icons will not be generated")

    # Create bootstrap file
    create_bootstrap_file()

    # Clean up previous build artifacts
    build_dir = Path("build")
    dist_dir = Path("dist")

    if build_dir.exists():
        print(f"Cleaning {build_dir}...")
        shutil.rmtree(build_dir, ignore_errors=True)

    if dist_dir.exists():
        print(f"Cleaning {dist_dir}...")
        shutil.rmtree(dist_dir, ignore_errors=True)

    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Add empty log file
    log_file = logs_dir / "dualgpuopt.log"
    log_file.touch()

    # Create data directory mappings
    data_dirs = [
        ("dualgpuopt/resources", "dualgpuopt/resources"),
        ("dualgpuopt/config", "dualgpuopt/config"),
        ("logs", "logs"),
    ]

    # Create assets directory if it doesn't exist
    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)

    # Copy icons to assets directory
    for icon_file in ["icon.png", "icon.ico"]:
        src_path = Path("dualgpuopt/resources") / icon_file
        if src_path.exists():
            dst_path = assets_dir / icon_file
            try:
                shutil.copy(src_path, dst_path)
                print(f"Copied {src_path} to {dst_path}")
            except Exception as e:
                print(f"Error copying {src_path} to {dst_path}: {e}")

    # Add assets directory to data dirs
    data_dirs.append(("assets", "assets"))

    data_args = []
    for src, dst in data_dirs:
        if Path(src).exists():
            data_args.append(f"--add-data={src};{dst}")

    # Get icon path
    icon_path = "dualgpuopt/resources/icon.ico"
    if not Path(icon_path).exists():
        icon_path = "assets/icon.ico"

    icon_arg = f"--icon={icon_path}" if Path(icon_path).exists() else ""

    # Build command - now using bootstrap.py as the main script
    cmd = [
        "pyinstaller",
        "bootstrap.py",
        "--name=DualGPUOptimizer",
        "--windowed",
        "--clean",
        *data_args
    ]

    if icon_arg:
        cmd.append(icon_arg)

    # Run PyInstaller
    print("\nBuilding executable...")
    success = run_command(" ".join(cmd))

    if success:
        exe_path = dist_dir / "DualGPUOptimizer" / "DualGPUOptimizer.exe"
        if exe_path.exists():
            print(f"\n✅ Build successful! Executable is at: {exe_path}")

            # Copy the icon directly next to the executable for Windows Explorer
            try:
                icon_src = Path(icon_path) if Path(icon_path).exists() else None
                if icon_src:
                    icon_dst = exe_path.parent / "icon.ico"
                    shutil.copy(icon_src, icon_dst)
                    print(f"Copied icon to {icon_dst}")
            except Exception as e:
                print(f"Error copying icon: {e}")

            return True
        else:
            print(f"\n❌ Build failed: Executable not found at {exe_path}")
            return False
    else:
        print("\n❌ Build failed: PyInstaller returned an error")
        return False

if __name__ == "__main__":
    print("=== DualGPUOptimizer Build Script ===\n")
    if build_executable():
        print("\nDone! The executable can be found in the dist/DualGPUOptimizer directory.")
        print("To ensure the icon displays correctly in Windows Explorer:")
        print("1. Try renaming the executable and changing it back")
        print("2. If that doesn't work, clear the Windows icon cache by running 'ie4uinit.exe -show'")
    else:
        print("\nBuild failed. Please check the errors above.")
        sys.exit(1)