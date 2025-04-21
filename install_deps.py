#!/usr/bin/env python3
"""
DualGPUOptimizer Dependency Installer

This script provides a simple way to install the dependencies required by DualGPUOptimizer.
It can install core dependencies only or all dependencies.
"""
import sys
import argparse
import subprocess
import importlib.util
from typing import Dict, List, Set
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("DualGPUOpt.Installer")

# Define dependency categories
REQUIRED_DEPENDENCIES = {
    "tkinter": {"package": "tk", "description": "Base UI framework", "test_import": "tkinter"},
}

CORE_DEPENDENCIES = {
    "pynvml": {"package": "pynvml>=11.0.0", "description": "NVIDIA GPU monitoring"},
    "psutil": {"package": "psutil>=5.9.0", "description": "System resource monitoring"},
    "numpy": {"package": "numpy>=1.24.0", "description": "Optimization algorithms"},
}

UI_DEPENDENCIES = {
    "ttkbootstrap": {"package": "ttkbootstrap>=1.0.0", "description": "Enhanced UI appearance"},
    "ttkthemes": {"package": "ttkthemes>=3.2.0", "description": "Additional UI themes"},
    "ttkwidgets": {"package": "ttkwidgets>=0.13.0", "description": "Additional UI widgets"},
}

CHAT_DEPENDENCIES = {
    "requests": {"package": "requests>=2.25.0", "description": "API communication"},
    "sseclient": {"package": "sseclient-py>=1.7.2", "description": "Streaming events"},
}

ML_DEPENDENCIES = {
    "torch": {"package": "torch==2.5.1", "description": "PyTorch for advanced features"},
    "torchvision": {"package": "torchvision==0.20.1", "description": "PyTorch vision utils"},
    "torchaudio": {"package": "torchaudio==2.5.1", "description": "PyTorch audio utils"},
}

# All dependencies
ALL_DEPENDENCIES = {
    **REQUIRED_DEPENDENCIES,
    **CORE_DEPENDENCIES,
    **UI_DEPENDENCIES,
    **CHAT_DEPENDENCIES,
    **ML_DEPENDENCIES
}

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def check_dependency(name: str) -> bool:
    """Check if a dependency is available

    Args:
        name: Name of the dependency to check

    Returns:
        True if available, False otherwise
    """
    if name == "tkinter":
        try:
            return True
        except ImportError:
            return False
    else:
        return importlib.util.find_spec(name) is not None

def get_missing_dependencies() -> Dict[str, List[str]]:
    """Check all dependencies and return missing ones by category

    Returns:
        Dictionary with categories as keys and lists of missing dependencies as values
    """
    missing = {}

    # Check required dependencies
    required_missing = [name for name in REQUIRED_DEPENDENCIES if not check_dependency(name)]
    if required_missing:
        missing["required"] = required_missing

    # Check core dependencies
    core_missing = [name for name in CORE_DEPENDENCIES if not check_dependency(name)]
    if core_missing:
        missing["core"] = core_missing

    # Check UI dependencies
    ui_missing = [name for name in UI_DEPENDENCIES if not check_dependency(name)]
    if ui_missing:
        missing["ui"] = ui_missing

    # Check chat dependencies
    chat_missing = [name for name in CHAT_DEPENDENCIES if not check_dependency(name)]
    if chat_missing:
        missing["chat"] = chat_missing

    # Check ML dependencies
    ml_missing = [name for name in ML_DEPENDENCIES if not check_dependency(name)]
    if ml_missing:
        missing["ml"] = ml_missing

    return missing

def get_installation_commands(missing_deps: Dict[str, List[str]], install_categories: Set[str]) -> List[str]:
    """Get pip installation commands for missing dependencies

    Args:
        missing_deps: Dictionary with categories as keys and lists of missing dependencies as values
        install_categories: Set of categories to install

    Returns:
        List of pip install commands
    """
    commands = []

    # Build installation commands by category
    if "required" in missing_deps and "required" in install_categories:
        required_packages = " ".join(
            REQUIRED_DEPENDENCIES[name]["package"] for name in missing_deps["required"]
            if name != "tkinter"  # tkinter requires special handling
        )
        if required_packages:
            commands.append(f"pip install {required_packages}")

    if "core" in missing_deps and "core" in install_categories:
        core_packages = " ".join(CORE_DEPENDENCIES[name]["package"] for name in missing_deps["core"])
        if core_packages:
            commands.append(f"pip install {core_packages}")

    if "ui" in missing_deps and "ui" in install_categories:
        ui_packages = " ".join(UI_DEPENDENCIES[name]["package"] for name in missing_deps["ui"])
        if ui_packages:
            commands.append(f"pip install {ui_packages}")

    if "chat" in missing_deps and "chat" in install_categories:
        chat_packages = " ".join(CHAT_DEPENDENCIES[name]["package"] for name in missing_deps["chat"])
        if chat_packages:
            commands.append(f"pip install {chat_packages}")

    if "ml" in missing_deps and "ml" in install_categories:
        ml_packages = " ".join(ML_DEPENDENCIES[name]["package"] for name in missing_deps["ml"])
        if ml_packages:
            commands.append(f"pip install {ml_packages}")

    return commands

def print_dependency_status() -> None:
    """Print status of all dependencies"""
    print("\nDualGPUOptimizer Dependency Check")
    print("===============================\n")

    # Check Python version
    py_version = sys.version.split()[0]
    print(f"Python version: {py_version}")
    if float(py_version.split('.')[0] + '.' + py_version.split('.')[1]) < 3.8:
        print("  ❌ Python 3.8+ is recommended. Some features may not work correctly.")
    else:
        print("  ✅ Python version is compatible.")

    print("\nRequired Dependencies:")
    for name, info in REQUIRED_DEPENDENCIES.items():
        if check_dependency(name):
            print(f"  ✅ {name}: {info['description']}")
        else:
            print(f"  ❌ {name}: {info['description']} - REQUIRED, application will not run")

    print("\nCore Dependencies:")
    for name, info in CORE_DEPENDENCIES.items():
        if check_dependency(name):
            print(f"  ✅ {name}: {info['description']}")
        else:
            print(f"  ❌ {name}: {info['description']} - FALLBACK available but features limited")

    print("\nUI Dependencies:")
    for name, info in UI_DEPENDENCIES.items():
        if check_dependency(name):
            print(f"  ✅ {name}: {info['description']}")
        else:
            print(f"  ❌ {name}: {info['description']} - FALLBACK available with basic UI")

    print("\nChat Dependencies:")
    for name, info in CHAT_DEPENDENCIES.items():
        if check_dependency(name):
            print(f"  ✅ {name}: {info['description']}")
        else:
            print(f"  ❌ {name}: {info['description']} - FALLBACK available with limited chat")

    print("\nMachine Learning Dependencies:")
    for name, info in ML_DEPENDENCIES.items():
        if check_dependency(name):
            print(f"  ✅ {name}: {info['description']}")
        else:
            print(f"  ❌ {name}: {info['description']} - OPTIONAL for advanced features")

    # Get missing dependencies
    missing = get_missing_dependencies()
    if missing:
        print("\nMissing Dependencies:")
        for category, deps in missing.items():
            print(f"  {category.capitalize()}: {', '.join(deps)}")
    else:
        print("\nAll dependencies are installed! ✅")

def install_dependencies(args: argparse.Namespace) -> int:
    """Install missing dependencies based on command-line arguments

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Check for missing dependencies
    missing = get_missing_dependencies()
    if not missing:
        logger.info("All dependencies are already installed!")
        return 0

    # Determine which categories to install
    install_categories = set()
    if args.core_only:
        install_categories.update(["required", "core"])
    elif args.ui_only:
        install_categories.update(["required", "ui"])
    elif args.chat_only:
        install_categories.update(["required", "chat"])
    elif args.ml_only:
        install_categories.update(["required", "ml"])
    else:
        # Install all by default
        install_categories.update(["required", "core", "ui", "chat", "ml"])

    # Get installation commands
    commands = get_installation_commands(missing, install_categories)
    if not commands:
        logger.info("No installable dependencies found in selected categories")
        return 0

    # Check for tkinter separately
    if "required" in missing and "tkinter" in missing["required"]:
        logger.warning("tkinter is required and must be installed through your system package manager")
        if sys.platform == "win32":
            logger.info("For Windows, reinstall Python and check 'tcl/tk and IDLE'")
        elif sys.platform == "darwin":
            logger.info("For macOS, use 'brew install python-tk'")
        else:
            logger.info("For Linux, use 'apt install python3-tk' or equivalent")

    # Print installation summary
    print("\nInstallation Summary:")
    for category in install_categories:
        if category in missing:
            print(f"  {category.capitalize()}: {', '.join(missing[category])}")

    print("\nCommands to execute:")
    for cmd in commands:
        print(f"  {cmd}")

    # Confirm installation
    if not args.yes:
        response = input("\nProceed with installation? [y/N] ").strip().lower()
        if response != 'y':
            logger.info("Installation cancelled by user")
            return 0

    # Execute installation commands
    success = True
    for cmd in commands:
        logger.info(f"Running: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, check=True)
            if result.returncode != 0:
                logger.error(f"Command failed with exit code {result.returncode}")
                success = False
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            success = False
        except Exception as e:
            logger.error(f"Error during installation: {e}")
            success = False

    # Print final status
    if success:
        logger.info("Installation completed successfully!")
        # Re-check to make sure everything installed
        new_missing = get_missing_dependencies()
        still_missing = []
        for category in install_categories:
            if category in new_missing:
                still_missing.extend(new_missing[category])

        if still_missing:
            logger.warning(f"Some dependencies could not be installed: {', '.join(still_missing)}")
            if "tkinter" in still_missing:
                logger.warning("Note: tkinter must be installed through your system package manager")
            return 1
        return 0
    else:
        logger.error("Installation failed!")
        return 1

def check_package(package_name):
    """Check if a package is installed."""
    try:
        spec = importlib.util.find_spec(package_name.split('==')[0])
        return spec is not None
    except (ImportError, AttributeError):
        return False

def install_package(package_name, description, verbose=False):
    """Install a package using pip."""
    if check_package(package_name.split('==')[0]):
        print(f"{Colors.GREEN}✓ {package_name} already installed{Colors.ENDC}")
        return True

    print(f"{Colors.YELLOW}→ Installing {package_name} ({description}){Colors.ENDC}")

    try:
        cmd = [sys.executable, "-m", "pip", "install", package_name]
        if verbose:
            result = subprocess.run(cmd)
        else:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode == 0:
            print(f"{Colors.GREEN}✓ Successfully installed {package_name}{Colors.ENDC}")
            return True
        else:
            error_msg = result.stderr.decode('utf-8') if not verbose else "See above error"
            print(f"{Colors.RED}✗ Failed to install {package_name}: {error_msg}{Colors.ENDC}")
            return False
    except Exception as e:
        print(f"{Colors.RED}✗ Error installing {package_name}: {str(e)}{Colors.ENDC}")
        return False

def install_pytorch(verbose=False):
    """Install PyTorch with CUDA support."""
    cuda_version = "cu121"  # Default CUDA version

    print(f"{Colors.YELLOW}→ Installing PyTorch with CUDA support{Colors.ENDC}")

    try:
        # PyTorch 2.5.1 with CUDA 12.1
        cmd = [
            sys.executable, "-m", "pip", "install",
            "torch==2.5.1", "torchvision==0.20.1", "torchaudio==2.5.1",
            "--index-url", f"https://download.pytorch.org/whl/{cuda_version}"
        ]

        if verbose:
            result = subprocess.run(cmd)
        else:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode == 0:
            print(f"{Colors.GREEN}✓ Successfully installed PyTorch with CUDA support{Colors.ENDC}")
            return True
        else:
            error_msg = result.stderr.decode('utf-8') if not verbose else "See above error"
            print(f"{Colors.RED}✗ Failed to install PyTorch: {error_msg}{Colors.ENDC}")

            # Try without CUDA
            print(f"{Colors.YELLOW}→ Trying to install PyTorch without CUDA support{Colors.ENDC}")
            cmd = [sys.executable, "-m", "pip", "install", "torch==2.5.1", "torchvision==0.20.1", "torchaudio==2.5.1"]

            if verbose:
                result = subprocess.run(cmd)
            else:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if result.returncode == 0:
                print(f"{Colors.GREEN}✓ Successfully installed PyTorch without CUDA support{Colors.ENDC}")
                return True
            else:
                error_msg = result.stderr.decode('utf-8') if not verbose else "See above error"
                print(f"{Colors.RED}✗ Failed to install PyTorch: {error_msg}{Colors.ENDC}")
                return False
    except Exception as e:
        print(f"{Colors.RED}✗ Error installing PyTorch: {str(e)}{Colors.ENDC}")
        return False

def check_dependencies(deps_dict, check_only=False, verbose=False):
    """Check and optionally install dependencies from a dictionary."""
    missing = {}
    installed = {}

    for package, description in deps_dict.items():
        is_installed = check_package(package.split('==')[0])
        if is_installed:
            installed[package] = description
        else:
            missing[package] = description

    if check_only:
        return installed, missing

    # Install missing packages
    failed = {}
    for package, description in missing.items():
        if package in ML_DEPENDENCIES and package.startswith("torch"):
            # Skip individual torch packages, they'll be handled by install_pytorch
            continue

        success = install_package(package, description, verbose)
        if not success:
            failed[package] = description

    # If pytorch is missing, install it specially
    if any(p.startswith("torch") for p in missing.keys()):
        pytorch_success = install_pytorch(verbose)
        if not pytorch_success:
            for p in [p for p in missing.keys() if p.startswith("torch")]:
                failed[p] = missing[p]

    return installed, failed

def main() -> int:
    """Main entry point

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="DualGPUOptimizer Dependency Installer")

    # Dependency selection options
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Install all dependencies (default)")
    group.add_argument("--core-only", action="store_true", help="Install only core dependencies")
    group.add_argument("--ui-only", action="store_true", help="Install only UI dependencies")
    group.add_argument("--chat-only", action="store_true", help="Install only chat dependencies")
    group.add_argument("--ml-only", action="store_true", help="Install only ML dependencies")

    # Other options
    parser.add_argument("--check", action="store_true", help="Check dependencies and exit")
    parser.add_argument("-y", "--yes", action="store_true", help="Answer yes to all prompts")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Configure logging based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Just check dependencies if requested
    if args.check:
        print_dependency_status()
        return 0

    # Install dependencies
    return install_dependencies(args)

if __name__ == "__main__":
    sys.exit(main())