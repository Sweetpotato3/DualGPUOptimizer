#!/usr/bin/env python3
"""
Test script to verify DualGPUOptimizer bundle integrity.
Run this after building to check for common issues.
"""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path


def check_output(command):
    """Run a command and return its output."""
    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
        check=False,
    )
    return process.returncode, process.stdout, process.stderr


def test_constants_packaged():
    """Test if the constants module can be imported."""
    print("Testing constants module...")
    try:
        spec = importlib.util.find_spec("dualgpuopt.gui.constants")
        if spec is None:
            print("❌ dualgpuopt.gui.constants module not found")
            return False
        print("✅ dualgpuopt.gui.constants module found")
        return True
    except ImportError as exc:
        print(f"❌ Error importing constants: {exc}")
        return False


def test_torch_available():
    """Test if torch is available and properly imported."""
    print("Testing torch availability...")
    try:
        import torch

        print(f"✅ Torch {torch.__version__} found")

        if torch.cuda.is_available():
            print(f"✅ CUDA is available: {torch.version.cuda}")
            print(f"✅ Found {torch.cuda.device_count()} CUDA device(s)")
        else:
            print("⚠️ CUDA is not available")
        return True
    except ImportError:
        print("⚠️ Torch not available (optional dependency)")
        return True  # Not a critical failure as it's optional
    except Exception as exc:
        print(f"❌ Error with torch: {exc}")
        return False


def test_assets_present():
    """Test if assets directory is properly included."""
    print("Testing assets directory...")
    try:
        from dualgpuopt.gui.constants import ASSET_DIR

        if not ASSET_DIR.exists():
            print(f"❌ Assets directory not found: {ASSET_DIR}")
            return False

        # Check for important assets
        icon_file = ASSET_DIR / "app_icon.ico"
        if not icon_file.exists():
            print(f"❌ App icon not found: {icon_file}")
            return False

        print(f"✅ Assets directory found: {ASSET_DIR}")
        print(f"✅ App icon found: {icon_file}")
        return True
    except Exception as exc:
        print(f"❌ Error checking assets: {exc}")
        return False


def test_app_runs_in_mock_mode():
    """Test if the app runs in mock mode (quick smoke test)."""
    print("Testing app in mock mode...")
    app_path = Path("dist") / "DualGPUOptimizer" / "DualGPUOptimizer.exe"

    if not app_path.exists():
        print(f"❌ Application executable not found: {app_path}")
        return False

    print(f"✅ Application executable found: {app_path}")
    print("Running in mock mode (will start GUI, close it after testing)...")

    # Spawn process but don't wait (GUI will show)
    if sys.platform == "win32":
        os.startfile(str(app_path) + " --mock")
    else:
        subprocess.Popen([str(app_path), "--mock"])

    print("✅ Application launched in mock mode")
    return True


def main():
    """Run all tests."""
    print("=== DualGPUOptimizer Bundle Verification ===")

    tests = [
        test_constants_packaged,
        test_torch_available,
        test_assets_present,
        test_app_runs_in_mock_mode,
    ]

    results = []
    for test in tests:
        results.append(test())
        print()  # Add spacing

    print("=== Test Summary ===")
    if all(results):
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
