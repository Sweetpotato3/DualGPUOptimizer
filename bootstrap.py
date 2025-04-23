import os
import sys

# Make sure we're running from the correct directory
if getattr(sys, "frozen", False):
    # We're running in a PyInstaller bundle
    bundle_dir = os.path.dirname(sys.executable)
    # Change to the directory containing the executable
    os.chdir(bundle_dir)
    print(f"Working directory set to: {bundle_dir}")

# Import the actual entry point
from run_optimizer import main

main()
