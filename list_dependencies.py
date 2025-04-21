#!/usr/bin/env python3
"""
List required dependencies for DualGPUOptimizer
"""

import importlib.util
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DependencyLister")

# Define dependency categories
CATEGORIES = {
    "core": [
        "pynvml",
        "psutil",
        "numpy",
        "requests",
    ],
    "ui": [
        "tkinter",
        "ttkbootstrap",
        "ttkthemes",
        "ttkwidgets",
    ],
    "pytorch": [
        "torch",
        "torchvision",
        "torchaudio",
    ],
    "chat": [
        "sseclient",
        "websocket-client",
    ],
    "qt": [
        "PySide6",
    ]
}

def check_dependency(name: str) -> bool:
    """Check if a dependency is installed

    Args:
        name: Name of the dependency

    Returns:
        True if installed, False otherwise
    """
    try:
        if name == "tkinter":
            # Special handling for tkinter which is in stdlib
            return True

        spec = importlib.util.find_spec(name)
        return spec is not None
    except (ImportError, ModuleNotFoundError):
        return False

def get_dependency_status() -> dict:
    """Get the status of all dependencies

    Returns:
        Dictionary with dependency status by category
    """
    status = {}

    for category, deps in CATEGORIES.items():
        status[category] = {}
        for dep in deps:
            status[category][dep] = check_dependency(dep)

    return status

def get_uninstalled_dependencies() -> dict:
    """Get all uninstalled dependencies

    Returns:
        Dictionary with uninstalled dependencies by category
    """
    status = get_dependency_status()
    uninstalled = {}

    for category, deps in status.items():
        missing = [dep for dep, installed in deps.items() if not installed]
        if missing:
            uninstalled[category] = missing

    return uninstalled

def get_install_commands() -> dict:
    """Get pip install commands for missing dependencies

    Returns:
        Dictionary with install commands by category
    """
    uninstalled = get_uninstalled_dependencies()
    commands = {}

    for category, deps in uninstalled.items():
        if deps:
            if category == "qt":
                commands[category] = f"pip install {' '.join(deps)}"
            else:
                commands[category] = f"pip install {' '.join(deps)}"

    return commands

def main():
    """Main function"""
    logger.info("Checking DualGPUOptimizer dependencies...")

    # Get dependency status
    status = get_dependency_status()

    # Print status
    print("\n# DualGPUOptimizer Dependencies\n")

    for category, deps in status.items():
        print(f"## {category.title()} Dependencies\n")

        for dep, installed in deps.items():
            status_icon = "✅" if installed else "❌"
            print(f"- {status_icon} {dep}")

        print("")

    # Print install commands
    commands = get_install_commands()
    if commands:
        print("## Installation Commands\n")

        for category, command in commands.items():
            print(f"### {category.title()} Dependencies\n")
            print(f"```\n{command}\n```\n")

    # Print overall status
    uninstalled = get_uninstalled_dependencies()
    if not uninstalled:
        print("All dependencies are installed! 🎉")
    else:
        missing_count = sum(len(deps) for deps in uninstalled.values())
        print(f"Missing {missing_count} dependencies. See installation commands above.")

if __name__ == "__main__":
    main()