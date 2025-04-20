"""
Standalone launcher for DualGPUOptimizer.
This script will check for dependencies and run the application.
"""
import os
import sys
import pathlib
import subprocess

def main():
    print("DualGPUOptimizer Launcher")
    print("=========================")

    # Set environment variable for mock GPU mode
    os.environ["DGPUOPT_MOCK_GPUS"] = "1"
    print("Mock GPU mode enabled")

    # Check for required dependencies
    try:
        import rich
        print("✓ Rich library found")
    except ImportError:
        print("✗ Rich library not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
            print("✓ Rich library installed")
        except Exception as e:
            print(f"✗ Failed to install Rich: {e}")
            return 1

    # Try to import the core module
    try:
        import dualgpuopt
        print("✓ DualGPUOptimizer core module found")
    except ImportError:
        print("✗ DualGPUOptimizer module not found.")

        # Try installing the local package
        current_dir = pathlib.Path(__file__).parent
        if (current_dir / "dual_gpu_optimizer").exists():
            print(f"Found dual_gpu_optimizer directory. Installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "./dual_gpu_optimizer"])
                print("✓ DualGPUOptimizer installed")
                # Try importing again
                try:
                    import dualgpuopt
                except ImportError:
                    print("✗ Still cannot import DualGPUOptimizer even after installation.")
                    return 1
            except Exception as e:
                print(f"✗ Failed to install DualGPUOptimizer: {e}")
                return 1
        else:
            print("✗ Cannot find dual_gpu_optimizer directory for installation.")
            return 1

    # Launch the application
    print("\nStarting DualGPUOptimizer with mock GPU mode...")
    try:
        # Import and run the main module
        from dualgpuopt.__main__ import main
        main()
    except Exception as e:
        print(f"Error running application: {e}")

        # Create log directory
        log_dir = pathlib.Path.home() / ".dualgpuopt" / "logs"
        os.makedirs(log_dir, exist_ok=True)

        # Write error to log
        with open(log_dir / "launcher.log", "w") as f:
            f.write(f"Error: {e}\n")
            import traceback
            f.write(traceback.format_exc())

        print(f"Error details written to: {log_dir / 'launcher.log'}")
        input("Press Enter to exit...")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())