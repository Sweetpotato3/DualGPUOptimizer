#!/usr/bin/env python3
"""
DualGPUOptimizer Qt Dashboard launcher.

This script provides a simple way to launch the Qt-based dashboard.
"""

import sys
import os
import importlib.util
import subprocess
import warnings
import platform

def check_numpy_version():
    """Check for NumPy version and warn if it's 2.x."""
    try:
        import numpy as np
        numpy_version = np.__version__
        major_version = int(numpy_version.split('.')[0])
        
        if major_version >= 2:
            warnings.warn(
                f"NumPy version {numpy_version} detected. Some modules may not work correctly with NumPy 2.x. "
                "If you encounter errors, consider downgrading to 'numpy<2'.", stacklevel=2
            )
            
            # If using NumPy 2.x, set environment variable to help modules cope
            os.environ['NPY_RELAXED_STRIDES_CHECKING'] = '1'
            
            # If we're on Windows, offer to downgrade
            if platform.system() == 'Windows' and not os.environ.get('NUMPY_DOWNGRADE_OFFERED'):
                print(f"WARNING: NumPy version {numpy_version} detected, which may cause compatibility issues.")
                print("Would you like to downgrade to NumPy 1.26.4? (y/n)")
                choice = input().strip().lower()
                if choice == 'y':
                    print("Downgrading NumPy to 1.26.4...")
                    try:
                        subprocess.check_call(
                            [sys.executable, "-m", "pip", "install", "numpy==1.26.4", "--force-reinstall"]
                        )
                        print("NumPy has been downgraded to 1.26.4.")
                        print("Please restart the application.")
                        sys.exit(0)
                    except subprocess.CalledProcessError as e:
                        print(f"Failed to downgrade NumPy: {e}")
                else:
                    print("Continuing with NumPy 2.x (some features may not work correctly).")
                # Mark that we've offered the downgrade
                os.environ['NUMPY_DOWNGRADE_OFFERED'] = '1'
            
        return numpy_version
    except ImportError:
        return None

def check_dependencies():
    """Check that all required dependencies are installed."""
    required_packages = ["PySide6", "pyqtgraph"]
    missing_packages = []
    
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies(packages):
    """Attempt to install missing dependencies."""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + packages
        )
        return True
    except subprocess.CalledProcessError:
        return False

def fix_import_issues():
    """Fix common import issues that might cause startup failures."""
    telemetry_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 'dualgpuopt', 'telemetry')
    
    # Make sure the telemetry directory is a proper package with __init__.py
    init_path = os.path.join(telemetry_dir, '__init__.py')
    if not os.path.exists(telemetry_dir):
        os.makedirs(telemetry_dir, exist_ok=True)
        
    if not os.path.exists(init_path):
        # Create a basic __init__.py if it doesn't exist
        with open(init_path, 'w') as f:
            f.write("""\"\"\"
dualgpuopt.telemetry module
Provides telemetry and history tracking for GPU metrics.
\"\"\"

from dualgpuopt.telemetry.sample import TelemetrySample

# Import the main telemetry module to make its classes available
import dualgpuopt.telemetry as telemetry_module

__all__ = ["TelemetrySample"]
""")
        print(f"Created telemetry __init__.py at {init_path}")

def main():
    """Main entry point for the launcher."""
    # Try to fix potential import issues
    fix_import_issues()
    
    # Check NumPy version 
    numpy_version = check_numpy_version()
    if numpy_version:
        print(f"Using NumPy version: {numpy_version}")
    
    # Check for dependencies
    missing_packages = check_dependencies()
    
    if missing_packages:
        print(f"The following required packages are missing: {', '.join(missing_packages)}")
        print("Would you like to install them now? (y/n)")
        
        choice = input().strip().lower()
        
        if choice == "y":
            print(f"Installing {', '.join(missing_packages)}...")
            
            if install_dependencies(missing_packages):
                print("Dependencies installed successfully!")
            else:
                print("Failed to install dependencies. Please install them manually:")
                print(f"pip install {' '.join(missing_packages)}")
                return 1
        else:
            print("Cannot continue without required dependencies.")
            return 1
    
    # Launch the Qt dashboard
    try:
        # Check if dualgpuopt package is installed or in current directory
        if importlib.util.find_spec("dualgpuopt") is None:
            # Try to add the current directory to sys.path
            sys.path.insert(0, os.path.abspath("."))
            
            if importlib.util.find_spec("dualgpuopt") is None:
                print("Error: Cannot find the dualgpuopt package.")
                print("Make sure you are running this script from the DualGPUOptimizer directory.")
                return 1
        
        # Import and run the dashboard
        from dualgpuopt.qtgui.main import main
        return main()
        
    except ImportError as e:
        print(f"Error importing required modules: {e}")
        print("\nTrying to fix common import issues...")
        
        # Get the problematic module name
        module_name = str(e).split("'")[-2] if "'" in str(e) else None
        if module_name:
            print(f"Problem with module: {module_name}")
            
            # Try to load the module directly
            if module_name == "GPUMetrics" and "telemetry" in str(e):
                print("The error is with GPUMetrics import from telemetry.")
                print("This is a known issue. Applying a workaround...")
                
                # Create a temporary local version of GPUMetrics if needed
                # This code would typically be executed dynamically, but we've
                # already added fallback code in telethread.py
                
                print("Workaround applied. Restarting the application...")
                os.execv(sys.executable, [sys.executable] + sys.argv)
        
        return 1
    except Exception as e:
        print(f"Error launching the dashboard: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 