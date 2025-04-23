#!/usr/bin/env python3
"""
Rebuild script for DualGPUOptimizer.
This script rebuilds the application with PyInstaller with all necessary dependencies.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile


def copy_constants_file():
    """Make sure constants.py is correctly installed in the package."""
    # Get file paths
    current_dir = pathlib.Path(__file__).parent.resolve()
    constants_src = current_dir / "gui_constants.py"
    constants_dst = current_dir / "dual_gpu_optimizer" / "dualgpuopt" / "gui" / "constants.py"

    # Make sure constants.py exists
    if not constants_src.exists():
        print(f"Error: {constants_src} not found")
        return False

    # Make sure destination directory exists
    constants_dst.parent.mkdir(parents=True, exist_ok=True)

    # Copy the file
    try:
        shutil.copy2(constants_src, constants_dst)
        print(f"Copied constants.py to {constants_dst}")
        return True
    except Exception as e:
        print(f"Error copying constants.py: {e}")
        return False


def copy_module_files():
    """Create a directory structure for PyInstaller with flattened imports."""
    temp_dir = pathlib.Path(tempfile.mkdtemp())

    try:
        # Get paths
        current_dir = pathlib.Path(__file__).parent.resolve()
        package_dir = current_dir / "dual_gpu_optimizer" / "dualgpuopt"

        # Create destination directory
        temp_package_dir = temp_dir / "dualgpuopt"
        temp_package_dir.mkdir(parents=True, exist_ok=True)

        # Copy all files from package directory to temp directory
        for item in package_dir.glob("**/*"):
            if item.is_file():
                # Calculate relative path
                rel_path = item.relative_to(package_dir)
                # Create destination path
                dst_path = temp_package_dir / rel_path
                # Create parent directories if needed
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                # Copy the file
                shutil.copy2(item, dst_path)

        # Create a simplified __main__.py that imports only what's needed
        main_py = temp_package_dir / "__main__.py"
        with open(main_py, "w") as f:
            f.write(
                """#!/usr/bin/env python3
import os
import sys
import logging

# Set up mock GPU mode
os.environ["DGPUOPT_MOCK_GPUS"] = "1"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("dualgpuopt.startup")

try:
    # Try to import GUI application
    from dualgpuopt.gui.app import DualGpuApp, run_app

    logger.info("Starting application...")
    run_app()
except Exception as e:
    logger.error(f"Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
            )

        print(f"Module files copied to {temp_dir}")
        return temp_dir

    except Exception as e:
        print(f"Error copying module files: {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None


def build_with_pyinstaller(temp_dir):
    """Build the application with PyInstaller."""
    # Get paths
    current_dir = pathlib.Path(__file__).parent.resolve()

    # Path to PyInstaller script
    pyinstaller_script = temp_dir / "dualgpuopt" / "__main__.py"

    # Create PyInstaller command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--clean",
        "--name",
        "DualGPUOptimizer",
        "--add-data",
        f"{temp_dir}:dualgpuopt",
        "--hidden-import",
        "dualgpuopt",
        "--hidden-import",
        "dualgpuopt.gui",
        "--hidden-import",
        "dualgpuopt.gui.constants",
        str(pyinstaller_script),
    ]

    print(f"Running PyInstaller command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True, cwd=current_dir)
        print("PyInstaller build completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running PyInstaller: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during build: {e}")
        return False


def main():
    """Main entry point."""
    # Copy constants file
    if not copy_constants_file():
        print("Failed to copy constants file")
        return 1

    # Copy module files to temp directory
    temp_dir = copy_module_files()
    if not temp_dir:
        print("Failed to copy module files")
        return 1

    try:
        # Build with PyInstaller
        if not build_with_pyinstaller(temp_dir):
            print("PyInstaller build failed")
            return 1

        print("\nBuild completed successfully!")
        print("You can find the executable in the 'dist' directory.")
        return 0

    finally:
        # Clean up temp directory
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
