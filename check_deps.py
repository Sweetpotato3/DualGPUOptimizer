#!/usr/bin/env python3
"""
Dependency checker for DualGPUOptimizer
"""
import importlib
import sys
import subprocess
import os

def check_dependency(module_name, install_command=None):
    """Check if a module is installed and can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name} is installed")
        sys.stdout.flush()
        return True
    except ImportError:
        print(f"❌ {module_name} is not installed")
        sys.stdout.flush()
        if install_command:
            print(f"   Installing {module_name}...")
            sys.stdout.flush()
            try:
                subprocess.check_call(install_command, shell=True)
                print(f"✅ {module_name} installed successfully")
                sys.stdout.flush()
                return True
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {module_name}")
                sys.stdout.flush()
                return False
        return False

def fix_pyinstaller_psutil_issue():
    """Fix the PyInstaller psutil issue by ensuring it's properly installed"""
    print("Checking psutil installation...")
    sys.stdout.flush()
    
    # First check if psutil is installed
    if not check_dependency("psutil", "pip install psutil"):
        return False
    
    # Now check if PyInstaller can find it
    try:
        print("Testing if PyInstaller can find psutil...")
        sys.stdout.flush()
        
        # Create a minimal script that imports psutil
        test_script = "import psutil; print('PSUTIL_WORKING')"
        test_file = "test_psutil.py"
        
        with open(test_file, "w") as f:
            f.write(test_script)
        
        # Try to run it with PyInstaller
        print("Running test build with PyInstaller...")
        sys.stdout.flush()
        
        result = subprocess.run(
            ["pyinstaller", "--specpath", "build", "--workpath", "build", 
             "--distpath", "build", "--onefile", test_file],
            capture_output=True, 
            text=True
        )
        
        if "Hidden import 'psutil' not found" in result.stderr:
            print("⚠️ PyInstaller can't find psutil, fixing...")
            sys.stdout.flush()
            
            # Try reinstalling psutil with pip directly, not through a requirements file
            print("Uninstalling psutil...")
            sys.stdout.flush()
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "psutil"])
            
            print("Reinstalling psutil...")
            sys.stdout.flush()
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", "psutil"])
            
            print("✅ Fixed psutil installation")
            sys.stdout.flush()
            return True
        else:
            print("✅ PyInstaller can find psutil")
            sys.stdout.flush()
            return True
    except Exception as e:
        print(f"❌ Error while testing PyInstaller psutil: {e}")
        sys.stdout.flush()
        return False
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    print("DualGPUOptimizer Dependency Checker")
    print("==================================")
    sys.stdout.flush()
    
    # Check critical dependencies
    check_dependency("pynvml", "pip install nvidia-ml-py3")
    check_dependency("rich", "pip install rich")
    
    # Fix the psutil issue
    if fix_pyinstaller_psutil_issue():
        print("\n✅ All dependencies checked and fixed")
        print("You can now run the build script: python build.py")
    else:
        print("\n❌ Failed to fix all dependencies")
        print("Please manually install the missing dependencies and try again")
        sys.exit(1) 