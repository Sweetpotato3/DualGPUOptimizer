#!/usr/bin/env python3
"""
Direct launcher script for DualGPUOptimizer.
Bypasses the circular imports by directly importing the GUI components.
"""
import os
import sys
import pathlib
import logging
import importlib.util

def import_module_from_file(file_path, module_name):
    """Import a module directly from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        return None
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def setup_environment():
    """Set up the environment for running the application."""
    # Get the current directory
    current_dir = pathlib.Path(__file__).parent.resolve()
    package_dir = current_dir / "dual_gpu_optimizer"
    dualgpuopt_dir = package_dir / "dualgpuopt"
    
    # Add to sys.path
    sys.path.insert(0, str(current_dir))
    sys.path.insert(0, str(package_dir))
    sys.path.insert(0, str(dualgpuopt_dir))
    
    # Set environment variable for mock GPU mode
    os.environ["DGPUOPT_MOCK_GPUS"] = "1"
    
    # Directly import the constants module
    constants_path = dualgpuopt_dir / "gui" / "constants.py"
    constants = import_module_from_file(constants_path, "constants")
    if constants:
        print("Successfully imported constants module")
        sys.modules["dualgpuopt.gui.constants"] = constants
    else:
        print("Failed to import constants module")
        return False
    
    return True

def run_direct_gui():
    """Run the GUI application directly."""
    try:
        # Import the GUI app directly
        current_dir = pathlib.Path(__file__).parent.resolve()
        dualgpuopt_dir = current_dir / "dual_gpu_optimizer" / "dualgpuopt"
        app_path = dualgpuopt_dir / "gui" / "app.py"
        
        app_module = import_module_from_file(app_path, "app")
        if not app_module:
            print("Failed to import app module")
            return False
        
        # Create app instance and run
        app = app_module.DualGpuApp(mock_mode=True)
        app.run()
        return True
    except Exception as e:
        print(f"Error running direct GUI: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point."""
    # Set up basic logging first
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set up the environment
    if not setup_environment():
        print("Failed to set up environment")
        return 1
    
    # Run the application
    if run_direct_gui():
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main()) 