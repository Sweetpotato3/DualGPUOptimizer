#!/usr/bin/env python3
"""
Simple script to fix the psutil issue with PyInstaller
"""
import subprocess
import sys
import os

# Uninstall and reinstall psutil
print("Fixing psutil installation for PyInstaller...")
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "psutil"], check=True)
subprocess.run(
               [sys.executable,
               "-m",
               "pip",
               "install",
               "--no-cache-dir",
               "psutil"],
               check=True)
)
# Create a simple test script
test_file = "test_psutil.py"
with open(test_file, "w") as f:
    f.write("import psutil; print('PSUTIL_WORKING')")

# Run to ensure it works
try:
    print("Testing psutil import...")
    subprocess.run([sys.executable, test_file], check=True)
    print("✅ psutil is working correctly")
except subprocess.CalledProcessError:
    print("❌ psutil import test failed")
    sys.exit(1)
finally:
    if os.path.exists(test_file):
        os.remove(test_file)

print("\nNow try running the build again with:")
print("python build.py")