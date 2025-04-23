#!/usr/bin/env python3
"""
Entry point launcher for DualGPUOptimizer
"""
import multiprocessing
import os
import platform
import subprocess
import sys

# Set environment variables for PyTorch and CUDA
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"  # Use first two GPUs
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512"  # Helps with memory fragmentation
os.environ[
    "PYTORCH_ENABLE_OBSOLETE_CUDA_COMPAT"
] = "1"  # Enable compatibility with newer CUDA architectures
os.environ["DGPUOPT_DEBUG"] = "1"  # Enable debug mode for more verbose output

# Ensure we can find the application modules
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)


def check_and_install_torch():
    """Check if PyTorch is installed, if not install it"""
    try:
        import torch

        print(f"PyTorch {torch.__version__} is already installed")

        # Check if GPU support is available
        if not torch.cuda.is_available():
            raise RuntimeError("GPU build of PyTorch not found – reinstall with cu121 wheels")

        return True
    except ImportError:
        print("PyTorch is not installed. Attempting to install...")
        try:
            # Get Python version to determine correct CUDA version
            py_version = platform.python_version_tuple()

            # Python 3.12+ needs CUDA 12.1 wheels, earlier versions can use 12.2
            cuda_version = (
                "cu121" if int(py_version[0]) == 3 and int(py_version[1]) >= 12 else "cu122"
            )
            torch_version = "2.5.1" if cuda_version == "cu121" else "2.3.1"
            vision_version = "0.20.1" if cuda_version == "cu121" else "0.18.1"
            audio_version = "2.5.1" if cuda_version == "cu121" else "2.3.1"

            print(
                f"Installing PyTorch {torch_version} with {cuda_version} for Python {py_version[0]}.{py_version[1]}"
            )

            # Use PowerShell-friendly command syntax (backtick for line continuation if needed)
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    f"torch=={torch_version}",
                    f"torchvision=={vision_version}",
                    f"torchaudio=={audio_version}",
                    "--index-url",
                    f"https://download.pytorch.org/whl/{cuda_version}",
                ]
            )
            print("PyTorch installation completed. Please restart the application.")
            return False
        except subprocess.CalledProcessError as e:
            print(f"Failed to install PyTorch: {e}")
            return False


def main():
    """Main entry point function that can be imported and called from elsewhere"""
    # Add multiprocessing support
    multiprocessing.freeze_support()

    # Print working directory for diagnostic purposes
    print(f"Current working directory: {os.getcwd()}")

    # Check and install PyTorch if needed
    torch_installed = check_and_install_torch()

    try:
        # Try to import torch to check if it's available
        if torch_installed:
            try:
                import torch

                print(f"PyTorch version: {torch.__version__}")
                print(f"CUDA available: {torch.cuda.is_available()}")
                if torch.cuda.is_available():
                    print(f"CUDA version: {torch.version.cuda}")
                    print(f"GPU devices: {torch.cuda.device_count()}")
                    for i in range(torch.cuda.device_count()):
                        print(f"Device {i}: {torch.cuda.get_device_name(i)}")
                else:
                    print("WARNING: CUDA not available. DualGPUOptimizer requires GPU support!")
                    print("Please reinstall PyTorch with CUDA support using:")
                    print(
                        "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
                    )
            except Exception as e:
                print(f"Warning when initializing PyTorch: {e}")
                print("Continuing with application startup...")

        # Import the main app
        try:
            from dualgpuopt.gui import main_app

            print("Starting DualGPUOptimizer...")
            main_app.run()
        except ModuleNotFoundError:
            print("Could not import dualgpuopt.gui.main_app")
            print("Checking available modules in dualgpuopt/gui:")
            try:
                import dualgpuopt.gui

                print(f"Available modules in dualgpuopt.gui: {dir(dualgpuopt.gui)}")
            except ImportError:
                print("Could not import dualgpuopt.gui package")
                print("Checking directory structure:")
                if os.path.exists("dualgpuopt"):
                    print("dualgpuopt directory exists, contents:")
                    print(os.listdir("dualgpuopt"))
                    if os.path.exists("dualgpuopt/gui"):
                        print("dualgpuopt/gui directory exists, contents:")
                        print(os.listdir("dualgpuopt/gui"))
                else:
                    print("dualgpuopt directory not found")
    except Exception as e:
        # Print errors to console for debugging
        print(f"Error launching application: {e}")
        import traceback

        traceback.print_exc()
        input("Press Enter to exit...")


# Import and run the application
if __name__ == "__main__":
    main()
