#!/usr/bin/env python3
"""
Dependency checker for DualGPUOptimizer

Checks for required and optional dependencies and provides installation instructions
"""
import importlib.util
import platform
import subprocess
import sys
from typing import Dict, List

# Define dependencies by category
CORE_DEPS = {
    "pynvml": {"package": "pynvml>=11.0.0", "description": "NVIDIA GPU monitoring"},
    "tkinter": {"package": "tk", "description": "Base UI framework"},
    "psutil": {"package": "psutil>=5.9.0", "description": "System resource monitoring"},
    "numpy": {"package": "numpy>=1.24.0", "description": "Optimization algorithms"},
}

UI_DEPS = {
    "ttkbootstrap": {"package": "ttkbootstrap>=1.0.0", "description": "Enhanced UI appearance"},
    "ttkthemes": {"package": "ttkthemes>=3.2.0", "description": "Additional UI themes"},
    "ttkwidgets": {"package": "ttkwidgets>=0.13.0", "description": "Additional UI widgets"},
}

CHAT_DEPS = {
    "requests": {"package": "requests>=2.25.0", "description": "API communication"},
    "sseclient": {"package": "sseclient-py>=1.7.2", "description": "Streaming events"},
}

ML_DEPS = {
    "torch": {"package": "torch==2.5.1", "description": "PyTorch for advanced features"},
    "torchvision": {"package": "torchvision==0.20.1", "description": "PyTorch vision utils"},
    "torchaudio": {"package": "torchaudio==2.5.1", "description": "PyTorch audio utils"},
}

# All dependencies
ALL_DEPS = {**CORE_DEPS, **UI_DEPS, **CHAT_DEPS, **ML_DEPS}


def check_dependency(name: str) -> bool:
    """
    Check if a dependency is installed

    Args:
    ----
        name: Name of the dependency

    Returns:
    -------
        True if installed, False otherwise
    """
    if name == "tkinter":
        try:
            import tkinter

            return True
        except ImportError:
            return False
    else:
        return importlib.util.find_spec(name) is not None


def get_missing_dependencies() -> Dict[str, List[str]]:
    """
    Get missing dependencies by category

    Returns
    -------
        Dictionary with categories as keys and lists of missing dependencies as values
    """
    missing = {}

    # Check core dependencies
    core_missing = [name for name in CORE_DEPS if not check_dependency(name)]
    if core_missing:
        missing["core"] = core_missing

    # Check UI dependencies
    ui_missing = [name for name in UI_DEPS if not check_dependency(name)]
    if ui_missing:
        missing["ui"] = ui_missing

    # Check chat dependencies
    chat_missing = [name for name in CHAT_DEPS if not check_dependency(name)]
    if chat_missing:
        missing["chat"] = chat_missing

    # Check ML dependencies
    ml_missing = [name for name in ML_DEPS if not check_dependency(name)]
    if ml_missing:
        missing["ml"] = ml_missing

    return missing


def get_installation_commands(missing_deps: Dict[str, List[str]]) -> List[str]:
    """
    Get pip installation commands for missing dependencies

    Args:
    ----
        missing_deps: Dictionary with categories as keys and lists of missing dependencies as values

    Returns:
    -------
        List of pip install commands
    """
    commands = []

    # Build installation commands by category
    if "core" in missing_deps:
        core_packages = " ".join(
            CORE_DEPS[name]["package"] for name in missing_deps["core"] if name != "tkinter"
        )
        if core_packages:
            commands.append(f"pip install {core_packages}")

    if "ui" in missing_deps:
        ui_packages = " ".join(UI_DEPS[name]["package"] for name in missing_deps["ui"])
        if ui_packages:
            commands.append(f"pip install {ui_packages}")

    if "chat" in missing_deps:
        chat_packages = " ".join(CHAT_DEPS[name]["package"] for name in missing_deps["chat"])
        if chat_packages:
            commands.append(f"pip install {chat_packages}")

    if "ml" in missing_deps:
        ml_packages = " ".join(ML_DEPS[name]["package"] for name in missing_deps["ml"])
        if ml_packages:
            commands.append(f"pip install {ml_packages}")

    return commands


def print_dependency_status() -> None:
    """Print status of all dependencies"""
    print("\nDualGPUOptimizer Dependency Check")
    print("===============================\n")

    # Check Python version
    py_version = platform.python_version()
    print(f"Python version: {py_version}")
    if float(py_version.split(".")[0] + "." + py_version.split(".")[1]) < 3.8:
        print("  ❌ Python 3.8+ is recommended. Some features may not work correctly.")
    else:
        print("  ✅ Python version is compatible.")

    print("\nCore Dependencies:")
    for name, info in CORE_DEPS.items():
        if check_dependency(name):
            print(f"  ✅ {name}: {info['description']}")
        else:
            if name == "tkinter":
                print(f"  ❌ {name}: {info['description']} - REQUIRED, application will not run")
            else:
                print(
                    f"  ❌ {name}: {info['description']} - FALLBACK available but features limited"
                )

    print("\nUI Dependencies:")
    for name, info in UI_DEPS.items():
        if check_dependency(name):
            print(f"  ✅ {name}: {info['description']}")
        else:
            print(f"  ❌ {name}: {info['description']} - FALLBACK available with basic UI")

    print("\nChat Dependencies:")
    for name, info in CHAT_DEPS.items():
        if check_dependency(name):
            print(f"  ✅ {name}: {info['description']}")
        else:
            print(f"  ❌ {name}: {info['description']} - FALLBACK available with limited chat")

    print("\nMachine Learning Dependencies:")
    for name, info in ML_DEPS.items():
        if check_dependency(name):
            print(f"  ✅ {name}: {info['description']}")
        else:
            print(f"  ❌ {name}: {info['description']} - OPTIONAL for advanced features")

    # Check for missing dependencies
    missing = get_missing_dependencies()
    if missing:
        print("\nInstallation Instructions:")
        commands = get_installation_commands(missing)
        for cmd in commands:
            print(f"  {cmd}")
    else:
        print("\nAll dependencies are installed! ✅")

    print("\nApplication Status:")
    if "core" in missing and "tkinter" in missing["core"]:
        print("  ❌ Application cannot run: tkinter is required")
    elif "core" in missing:
        print("  ⚠️ Application can run with limited functionality")
    else:
        print("  ✅ Core functionality available")

    if "ui" in missing:
        print("  ⚠️ Basic UI available (enhanced UI features disabled)")
    else:
        print("  ✅ Enhanced UI available")

    if "chat" in missing:
        print("  ⚠️ Chat functionality limited")
    else:
        print("  ✅ Chat functionality available")

    if "ml" in missing:
        print("  ⚠️ Advanced ML features disabled")
    else:
        print("  ✅ Advanced ML features available")


def main() -> None:
    """Main function"""
    print_dependency_status()

    # If running with --install flag, try to install missing dependencies
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        missing = get_missing_dependencies()
        if missing:
            print("\nInstalling missing dependencies...")
            commands = get_installation_commands(missing)
            for cmd in commands:
                print(f"Running: {cmd}")
                subprocess.run(cmd, shell=True, check=False)

            # Check again
            print("\nChecking dependencies after installation...")
            print_dependency_status()
        else:
            print("\nAll dependencies are already installed.")


if __name__ == "__main__":
    main()
