#!/usr/bin/env python3
"""
Fix package installation and module import issues.
"""
import os
import sys
import subprocess
import pathlib

def main():
    # Get the current directory
    current_dir = pathlib.Path(__file__).parent.resolve()
    package_dir = current_dir / "dual_gpu_optimizer"
    
    print(f"Current directory: {current_dir}")
    print(f"Package directory: {package_dir}")
    
    # Check if the package directory exists
    if not package_dir.exists():
        print(f"Error: Package directory {package_dir} does not exist")
        return 1
    
    # Install the package in development mode
    print("Installing package in development mode...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", str(package_dir)], 
            cwd=current_dir,
            check=True
        )
        print("Package installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing package: {e}")
        return 1
    
    # Check if the constants.py file exists
    constants_path = package_dir / "dualgpuopt" / "gui" / "constants.py"
    print(f"Checking for constants.py: {constants_path}")
    if not constants_path.exists():
        print(f"Error: constants.py not found at {constants_path}")
        return 1
    
    print(f"constants.py exists at {constants_path}")
    
    # Try running the application with mock mode
    print("Running application in mock mode...")
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(current_dir)
        subprocess.run(
            [sys.executable, "-m", "dual_gpu_optimizer.dualgpuopt", "--mock"],
            cwd=current_dir,
            env=env,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running application: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 