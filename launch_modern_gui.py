#!/usr/bin/env python3
"""
Launch script for the Modern DualGPUOptimizer UI.

This script checks for the icon file, copies it if needed, 
and then launches the modern UI with real GPU detection.
"""
import os
import sys
import shutil
from pathlib import Path
import subprocess

def ensure_icon_exists():
    """Ensure the icon file exists in the assets directory."""
    assets_dir = Path("dualgpuopt/assets")
    assets_dir.mkdir(exist_ok=True)
    
    target_ico = assets_dir / "windowsicongpu.ico"
    
    # Check if icon already exists
    if target_ico.exists():
        print(f"Icon file already exists at {target_ico}")
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

def main():
    """Main entry point for the launcher."""
    print("Preparing to launch DualGPUOptimizer Modern UI...")
    
    # Ensure icon exists
    ensure_icon_exists()
    
    # Clear any mock GPU environment variable if set
    if "DGPUOPT_MOCK_GPUS" in os.environ:
        print("Removing mock GPU mode to use real hardware")
        del os.environ["DGPUOPT_MOCK_GPUS"]
    
    # Launch the modern UI with real GPU detection
    print("Launching DualGPUOptimizer Modern UI with real GPU detection...")
    try:
        subprocess.run([sys.executable, "run_modern_ui.py"])
    except Exception as e:
        print(f"Error launching application: {e}")
        input("Press Enter to exit...")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 