#!/usr/bin/env python3
"""
Dependency installer for DualGPUOptimizer

This script provides a simple way to install all dependencies required by DualGPUOptimizer.
It handles both required and optional dependencies with proper error handling.
"""
import sys
import subprocess
import logging
import os
from pathlib import Path
import importlib.util
import argparse
from typing import Dict, List, Union, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger("DualGPUOpt.Install")

def is_venv() -> bool:
    """
    Check if the script is running in a virtual environment
    
    Returns:
        True if running in a virtual environment, False otherwise
    """
    return hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

def get_python_executable() -> str:
    """
    Get the current Python executable path
    
    Returns:
        Path to the Python executable
    """
    return sys.executable

def run_command(cmd: List[str], cwd: Optional[str] = None) -> bool:
    """
    Run a shell command
    
    Args:
        cmd: Command to run as a list of arguments
        cwd: Working directory to run the command in
        
    Returns:
        True if the command was successful, False otherwise
    """
    try:
        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Log output if there is any
        if result.stdout:
            for line in result.stdout.splitlines():
                logger.debug(line)
                
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return False

def check_tkinter() -> bool:
    """
    Check if tkinter is installed
    
    Returns:
        True if tkinter is installed, False otherwise
    """
    try:
        import tkinter
        logger.info("tkinter is installed")
        return True
    except ImportError:
        logger.error("tkinter is not installed")
        return False

def install_pip_dependencies(dependencies: List[str], upgrade: bool = False) -> bool:
    """
    Install Python dependencies using pip
    
    Args:
        dependencies: List of dependencies to install
        upgrade: Whether to upgrade existing packages
        
    Returns:
        True if installation was successful, False otherwise
    """
    if not dependencies:
        logger.info("No dependencies to install")
        return True
    
    pip_cmd = [get_python_executable(), "-m", "pip", "install"]
    
    if upgrade:
        pip_cmd.append("--upgrade")
    
    pip_cmd.extend(dependencies)
    
    result = run_command(pip_cmd)
    if result:
        logger.info("Dependencies installed successfully")
    else:
        logger.error("Failed to install dependencies")
    
    return result

def ensure_pip_and_setuptools() -> bool:
    """
    Ensure pip and setuptools are up to date
    
    Returns:
        True if pip and setuptools are installed and up to date, False otherwise
    """
    return install_pip_dependencies(["pip", "setuptools", "wheel"], upgrade=True)

def handle_tkinter_installation() -> bool:
    """
    Provide instructions for installing tkinter
    
    Returns:
        True if tkinter is installed, False otherwise
    """
    if check_tkinter():
        return True
    
    logger.error("tkinter is required but not installed.")
    logger.error("Please install tkinter using your operating system's package manager:")
    
    if sys.platform == 'win32':
        logger.error("Windows: Reinstall Python and ensure 'tcl/tk and IDLE' is checked")
    elif sys.platform == 'darwin':
        logger.error("macOS: Run 'brew install python-tk' or reinstall Python")
    else:
        logger.error("Linux (Ubuntu/Debian): Run 'sudo apt-get install python3-tk'")
        logger.error("Linux (Fedora): Run 'sudo dnf install python3-tkinter'")
        logger.error("Linux (Arch): Run 'sudo pacman -S tk'")
    
    return check_tkinter()

def get_dependency_manager():
    """
    Try to import the dependency manager module
    
    Returns:
        Dependency manager module if available, None otherwise
    """
    try:
        # Try to add the current directory to sys.path
        current_dir = str(Path.cwd())
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Try to import the dependency manager
        import dualgpuopt.dependency_manager as dm
        logger.info("Dependency manager imported successfully")
        return dm
    except ImportError as e:
        logger.warning(f"Could not import dependency manager: {e}")
        
        # Try to directly import from a relative path
        try:
            # Try to import the module from the dualgpuopt directory
            spec = importlib.util.spec_from_file_location(
                "dependency_manager",
                str(Path("dualgpuopt") / "dependency_manager.py")
            )
            dm = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(dm)
            logger.info("Dependency manager imported from file path")
            return dm
        except Exception as e2:
            logger.error(f"Could not import dependency manager from file: {e2}")
            return None

def create_virtual_environment(venv_path: Union[str, Path]) -> bool:
    """
    Create a virtual environment
    
    Args:
        venv_path: Path to create the virtual environment
        
    Returns:
        True if the virtual environment was created, False otherwise
    """
    venv_path = Path(venv_path)
    
    if venv_path.exists():
        logger.info(f"Virtual environment already exists at {venv_path}")
        return True
    
    logger.info(f"Creating virtual environment at {venv_path}")
    
    try:
        import venv
        venv.create(venv_path, with_pip=True)
        logger.info(f"Virtual environment created at {venv_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create virtual environment: {e}")
        return False

def parse_args():
    """
    Parse command line arguments
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Install dependencies for DualGPUOptimizer"
    )
    
    parser.add_argument(
        "--core-only",
        action="store_true",
        help="Only install core dependencies"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Install all dependencies, including optional ones"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reinstallation of dependencies"
    )
    
    parser.add_argument(
        "--venv",
        type=str,
        help="Create or use a virtual environment at the specified path"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def main():
    """
    Main function
    """
    args = parse_args()
    
    # Set verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Check if we're in a virtual environment
    if not is_venv() and not args.venv:
        logger.warning("Not running in a virtual environment.")
        logger.warning("It's recommended to use a virtual environment to avoid dependency conflicts.")
        logger.warning("Use --venv to create a virtual environment.")
        
        if not confirm("Continue without virtual environment?"):
            logger.info("Installation cancelled.")
            return
    
    # Create or activate virtual environment if requested
    if args.venv:
        venv_path = Path(args.venv)
        
        # Create virtual environment if it doesn't exist
        if not venv_path.exists():
            if not create_virtual_environment(venv_path):
                logger.error("Failed to create virtual environment.")
                return
            
            logger.info(f"Virtual environment created at {venv_path}")
            logger.info(f"Please activate it and run this script again within the virtual environment:")
            
            if sys.platform == 'win32':
                logger.info(f"{venv_path}\\Scripts\\activate")
            else:
                logger.info(f"source {venv_path}/bin/activate")
            
            return
        else:
            logger.info(f"Using existing virtual environment at {venv_path}")
            
            # If we're not in the specified virtual environment, suggest activation
            if venv_path != Path(sys.prefix):
                logger.warning(f"Not running in the specified virtual environment.")
                logger.warning(f"Please activate it and run this script again:")
                
                if sys.platform == 'win32':
                    logger.warning(f"{venv_path}\\Scripts\\activate")
                else:
                    logger.warning(f"source {venv_path}/bin/activate")
                
                return
    
    # Ensure pip and setuptools are up to date
    logger.info("Checking pip and setuptools...")
    if not ensure_pip_and_setuptools():
        logger.error("Failed to update pip and setuptools.")
        return
    
    # Check for tkinter
    logger.info("Checking for tkinter...")
    if not handle_tkinter_installation():
        logger.error("tkinter is required but not installed.")
        logger.error("Please install tkinter and try again.")
        return
    
    # Try to get the dependency manager
    dm = get_dependency_manager()
    
    if dm:
        logger.info("Using dependency manager for installation")
        
        # Initialize dependency status
        dm.initialize_dependency_status()
        
        # Get missing dependencies
        missing = dm.get_missing_dependencies()
        
        if not missing:
            logger.info("All dependencies are already installed!")
            return
        
        # Filter dependencies based on flags
        if args.core_only and not args.all:
            # Only keep required and core dependencies
            missing = {k: v for k, v in missing.items() if k in ["required", "core"]}
        
        # Install dependencies
        success = dm.install_dependencies(missing, interactive=not args.force)
        
        if success:
            logger.info("All dependencies installed successfully!")
        else:
            logger.error("Failed to install some dependencies.")
            logger.info("Please check the error messages and try again.")
    else:
        logger.warning("Dependency manager not available. Using basic installation.")
        
        # Define core dependencies
        core_deps = [
            "pynvml>=11.0.0",
            "psutil>=5.9.0",
            "numpy>=1.24.0",
        ]
        
        # Define optional dependencies
        optional_deps = []
        
        if not args.core_only or args.all:
            optional_deps.extend([
                "ttkbootstrap>=1.0.0",
                "ttkthemes>=3.2.0",
                "ttkwidgets>=0.13.0",
                "requests>=2.25.0",
                "sseclient-py>=1.7.2",
            ])
        
        if args.all:
            optional_deps.extend([
                "torch==2.5.1",
                "torchvision==0.20.1",
                "torchaudio==2.5.1",
            ])
        
        # Install dependencies
        logger.info("Installing core dependencies...")
        if not install_pip_dependencies(core_deps, upgrade=args.force):
            logger.error("Failed to install core dependencies.")
            return
        
        if optional_deps:
            logger.info("Installing optional dependencies...")
            if not install_pip_dependencies(optional_deps, upgrade=args.force):
                logger.warning("Failed to install some optional dependencies.")
        
        logger.info("Dependencies installed successfully!")

def confirm(prompt: str) -> bool:
    """
    Ask for user confirmation
    
    Args:
        prompt: Prompt to display
        
    Returns:
        True if user confirms, False otherwise
    """
    while True:
        response = input(f"{prompt} [y/N] ").strip().lower()
        if not response or response == 'n':
            return False
        elif response == 'y':
            return True
        else:
            print("Please enter 'y' or 'n'")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Installation cancelled by user.")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1) 