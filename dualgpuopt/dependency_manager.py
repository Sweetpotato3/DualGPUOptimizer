"""
Dependency management system for DualGPUOptimizer

This module provides:
1. Dependency checking and validation
2. Graceful fallbacks for missing dependencies
3. Dynamic import helpers for optional components
4. Installation utilities

The dependency system follows these priorities:
- Required: Application won't start without these
- Core: Application works with fallbacks if missing
- Optional: Enhanced functionality when available
"""
import importlib.util
import logging
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("DualGPUOpt.Dependencies")

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
    **ML_DEPENDENCIES,
}

# Dependency state tracking
dependency_status = {name: False for name in ALL_DEPENDENCIES}
dependency_import_errors = {}


@dataclass
class ImportedModule:
    """Container for imported module with fallback and availability info"""

    name: str
    module: Optional[Any] = None
    available: bool = False
    fallback_used: bool = False
    error: Optional[str] = None

    def __bool__(self):
        """Return True if the module is available"""
        return self.available


def is_available(dependency_name: str) -> bool:
    """
    Check if a dependency is available

    Args:
    ----
        dependency_name: Name of the dependency to check

    Returns:
    -------
        True if dependency is available
    """
    return dependency_status.get(dependency_name, False)


def get_module(module_name: str, silent: bool = False) -> ImportedModule:
    """
    Get a module with proper error handling and fallback tracking

    Args:
    ----
        module_name: Name of the module to import
        silent: If True, don't log errors

    Returns:
    -------
        ImportedModule object with module and availability information
    """
    result = ImportedModule(name=module_name)

    try:
        result.module = importlib.import_module(module_name)
        result.available = True
        if not silent:
            logger.debug(f"Successfully imported {module_name}")
    except ImportError as e:
        result.error = str(e)
        dependency_import_errors[module_name] = str(e)
        if not silent:
            logger.debug(f"Failed to import {module_name}: {e}")

    return result


def get_with_fallback(
    primary_module: str, fallback_module: str, silent: bool = False
) -> ImportedModule:
    """
    Try to import a primary module, falling back to an alternative if not available

    Args:
    ----
        primary_module: Name of the preferred module to import
        fallback_module: Name of the fallback module
        silent: If True, don't log warnings for fallbacks

    Returns:
    -------
        ImportedModule with either the primary or fallback module
    """
    primary = get_module(primary_module, silent=True)

    if primary.available:
        return primary

    # Try fallback
    fallback = get_module(fallback_module, silent=True)
    if fallback.available:
        fallback.fallback_used = True
        if not silent:
            logger.warning(f"{primary_module} not available, using {fallback_module} as fallback")
        return fallback

    # Neither available
    if not silent:
        logger.warning(f"Neither {primary_module} nor {fallback_module} are available")

    # Return the primary with error info
    return primary


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


def initialize_dependency_status():
    """Check and initialize the status of all dependencies"""
    global dependency_status

    # Check each dependency
    for name in ALL_DEPENDENCIES:
        is_installed = check_dependency(name)
        dependency_status[name] = is_installed

        if is_installed:
            logger.debug(f"Dependency {name} is available")
        else:
            test_import = ALL_DEPENDENCIES[name].get("test_import", name)
            try:
                # Try an actual import to catch runtime issues
                __import__(test_import)
            except ImportError as e:
                dependency_import_errors[name] = str(e)
                logger.debug(f"Dependency {name} import error: {e}")
            except Exception as e:
                dependency_import_errors[name] = f"Runtime error: {e!s}"
                logger.debug(f"Dependency {name} runtime error: {e}")


def get_missing_dependencies() -> Dict[str, List[str]]:
    """
    Get missing dependencies by category

    Returns
    -------
        Dictionary with categories as keys and lists of missing dependencies as values
    """
    missing = {}

    # Check required dependencies
    required_missing = [name for name in REQUIRED_DEPENDENCIES if not dependency_status[name]]
    if required_missing:
        missing["required"] = required_missing

    # Check core dependencies
    core_missing = [name for name in CORE_DEPENDENCIES if not dependency_status[name]]
    if core_missing:
        missing["core"] = core_missing

    # Check UI dependencies
    ui_missing = [name for name in UI_DEPENDENCIES if not dependency_status[name]]
    if ui_missing:
        missing["ui"] = ui_missing

    # Check chat dependencies
    chat_missing = [name for name in CHAT_DEPENDENCIES if not dependency_status[name]]
    if chat_missing:
        missing["chat"] = chat_missing

    # Check ML dependencies
    ml_missing = [name for name in ML_DEPENDENCIES if not dependency_status[name]]
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
    if "required" in missing_deps:
        required_packages = " ".join(
            REQUIRED_DEPENDENCIES[name]["package"]
            for name in missing_deps["required"]
            if name != "tkinter"  # tkinter requires special handling
        )
        if required_packages:
            commands.append(f"pip install {required_packages}")

    if "core" in missing_deps:
        core_packages = " ".join(
            CORE_DEPENDENCIES[name]["package"] for name in missing_deps["core"]
        )
        if core_packages:
            commands.append(f"pip install {core_packages}")

    if "ui" in missing_deps:
        ui_packages = " ".join(UI_DEPENDENCIES[name]["package"] for name in missing_deps["ui"])
        if ui_packages:
            commands.append(f"pip install {ui_packages}")

    if "chat" in missing_deps:
        chat_packages = " ".join(
            CHAT_DEPENDENCIES[name]["package"] for name in missing_deps["chat"]
        )
        if chat_packages:
            commands.append(f"pip install {chat_packages}")

    if "ml" in missing_deps:
        ml_packages = " ".join(ML_DEPENDENCIES[name]["package"] for name in missing_deps["ml"])
        if ml_packages:
            commands.append(f"pip install {ml_packages}")

    return commands


def install_dependencies(missing_deps: Dict[str, List[str]], interactive: bool = True) -> bool:
    """
    Install missing dependencies

    Args:
    ----
        missing_deps: Dictionary of missing dependencies by category
        interactive: If True, prompt for confirmation before installing

    Returns:
    -------
        True if all installations were successful, False otherwise
    """
    if not missing_deps:
        logger.info("No missing dependencies to install")
        return True

    commands = get_installation_commands(missing_deps)
    if not commands:
        logger.info("No installable dependencies found")
        return False

    # Check for tkinter separately
    if "required" in missing_deps and "tkinter" in missing_deps["required"]:
        logger.warning(
            "tkinter is required and must be installed through your system package manager"
        )
        if sys.platform == "win32":
            logger.info("For Windows, reinstall Python and check 'tcl/tk and IDLE'")
        elif sys.platform == "darwin":
            logger.info("For macOS, use 'brew install python-tk'")
        else:
            logger.info("For Linux, use 'apt install python3-tk' or equivalent")

    # Get confirmation if interactive
    if interactive:
        flat_deps = []
        for category, deps in missing_deps.items():
            for dep in deps:
                if dep == "tkinter":
                    continue
                flat_deps.append(f"{dep} ({ALL_DEPENDENCIES[dep]['description']})")

        print("\nThe following dependencies will be installed:")
        for i, dep in enumerate(flat_deps, 1):
            print(f"  {i}. {dep}")

        print("\nInstallation commands:")
        for cmd in commands:
            print(f"  {cmd}")

        try:
            response = input("\nProceed with installation? [y/N] ").strip().lower()
            if response != "y":
                logger.info("Installation cancelled by user")
                return False
        except (KeyboardInterrupt, EOFError):
            logger.info("Installation cancelled by user")
            return False

    # Install dependencies
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

    # Re-check dependencies
    if success:
        initialize_dependency_status()

        # Check if all dependencies were installed
        updated_missing = get_missing_dependencies()
        for category in missing_deps:
            if category in updated_missing:
                # Some dependencies in this category are still missing
                for dep in updated_missing[category]:
                    if dep in missing_deps[category] and dep != "tkinter":
                        logger.warning(
                            f"Dependency {dep} is still missing after installation attempt"
                        )
                        success = False

    return success


def verify_core_dependencies() -> Tuple[bool, List[str]]:
    """
    Verify that core dependencies are available or have fallbacks

    Returns
    -------
        Tuple of (all_core_available, list of critical missing dependencies)
    """
    check_tkinter = check_dependency("tkinter")
    if not check_tkinter:
        return False, ["tkinter"]

    critical_missing = []

    # Check core dependencies
    for name in CORE_DEPENDENCIES:
        if not dependency_status[name]:
            # Core dependencies can use fallbacks, so they're not critical failures
            logger.warning(f"Core dependency {name} is not available - will use fallback")

    return len(critical_missing) == 0, critical_missing


def print_dependency_status(include_errors: bool = False) -> None:
    """
    Print status of all dependencies

    Args:
    ----
        include_errors: If True, include error messages for failed imports
    """
    print("\nDualGPUOptimizer Dependency Check")
    print("===============================\n")

    # Check Python version
    py_version = sys.version.split()[0]
    print(f"Python version: {py_version}")
    if float(py_version.split(".")[0] + "." + py_version.split(".")[1]) < 3.8:
        print("  ❌ Python 3.8+ is recommended. Some features may not work correctly.")
    else:
        print("  ✅ Python version is compatible.")

    print("\nRequired Dependencies:")
    for name, info in REQUIRED_DEPENDENCIES.items():
        if dependency_status[name]:
            print(f"  ✅ {name}: {info['description']}")
        else:
            print(f"  ❌ {name}: {info['description']} - REQUIRED, application will not run")
            if include_errors and name in dependency_import_errors:
                print(f"     Error: {dependency_import_errors[name]}")

    print("\nCore Dependencies:")
    for name, info in CORE_DEPENDENCIES.items():
        if dependency_status[name]:
            print(f"  ✅ {name}: {info['description']}")
        else:
            print(f"  ❌ {name}: {info['description']} - FALLBACK available but features limited")
            if include_errors and name in dependency_import_errors:
                print(f"     Error: {dependency_import_errors[name]}")

    print("\nUI Dependencies:")
    for name, info in UI_DEPENDENCIES.items():
        if dependency_status[name]:
            print(f"  ✅ {name}: {info['description']}")
        else:
            print(f"  ❌ {name}: {info['description']} - FALLBACK available with basic UI")
            if include_errors and name in dependency_import_errors:
                print(f"     Error: {dependency_import_errors[name]}")

    print("\nChat Dependencies:")
    for name, info in CHAT_DEPENDENCIES.items():
        if dependency_status[name]:
            print(f"  ✅ {name}: {info['description']}")
        else:
            print(f"  ❌ {name}: {info['description']} - FALLBACK available with limited chat")
            if include_errors and name in dependency_import_errors:
                print(f"     Error: {dependency_import_errors[name]}")

    print("\nMachine Learning Dependencies:")
    for name, info in ML_DEPENDENCIES.items():
        if dependency_status[name]:
            print(f"  ✅ {name}: {info['description']}")
        else:
            print(f"  ❌ {name}: {info['description']} - OPTIONAL for advanced features")
            if include_errors and name in dependency_import_errors:
                print(f"     Error: {dependency_import_errors[name]}")

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
    if "required" in missing and "tkinter" in missing["required"]:
        print("  ❌ Application cannot run: tkinter is required")
    elif "required" in missing:
        print("  ❌ Application cannot run: required dependencies missing")
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


def get_import_wrapper(module_name: str, default_value=None) -> Any:
    """
    Create a wrapper that tries to import a module and returns default if not available

    Args:
    ----
        module_name: Name of the module to import
        default_value: Value to return if module is not available

    Returns:
    -------
        Module if available, else default_value
    """
    try:
        return importlib.import_module(module_name)
    except ImportError:
        logger.debug(f"Import wrapper: {module_name} not available, using default")
        return default_value


class DynamicImporter:
    """Handles dynamic imports with fallbacks based on dependency status"""

    @staticmethod
    def import_ui():
        """Import UI modules with fallbacks"""
        if dependency_status.get("ttkbootstrap", False):
            import ttkbootstrap as ttk

            logger.debug("Using ttkbootstrap for UI")
            return ttk
        else:
            from tkinter import ttk

            logger.debug("Using standard ttk for UI")
            return ttk

    @staticmethod
    def import_gpu_compat():
        """Import GPU compatibility layer with fallbacks"""
        if dependency_status.get("pynvml", False):
            try:
                from dualgpuopt.gpu.compat import generate_mock_gpus, is_mock_mode, set_mock_mode

                logger.debug("Using GPU compatibility layer")
                return {
                    "is_mock_mode": is_mock_mode,
                    "set_mock_mode": set_mock_mode,
                    "generate_mock_gpus": generate_mock_gpus,
                }
            except ImportError:
                logger.warning("GPU compatibility import error, using mock functions")

        # Mock functions if not available
        logger.debug("Using mock GPU functions")
        return {
            "is_mock_mode": lambda: True,
            "set_mock_mode": lambda enabled=True: None,
            "generate_mock_gpus": lambda count=2: [
                {"id": 0, "name": "Mock GPU 0", "mem_total": 24576, "mem_used": 8192, "util": 45},
                {"id": 1, "name": "Mock GPU 1", "mem_total": 12288, "mem_used": 10240, "util": 85},
            ],
        }

    @staticmethod
    def import_telemetry():
        """Import telemetry system with fallbacks"""
        if dependency_status.get("pynvml", False):
            try:
                from dualgpuopt.telemetry import GPUMetrics, get_telemetry_service

                logger.debug("Using telemetry system")
                return {
                    "get_telemetry_service": get_telemetry_service,
                    "GPUMetrics": GPUMetrics,
                    "available": True,
                }
            except ImportError as e:
                logger.warning(f"Telemetry import error: {e}")

        logger.warning("Telemetry system not available, will use mock data")
        return {
            "get_telemetry_service": lambda: None,
            "GPUMetrics": None,
            "available": False,
        }

    @staticmethod
    def import_dashboard():
        """Import dashboard component with fallbacks"""
        try:
            from dualgpuopt.gui.dashboard import DashboardView

            logger.debug("Using dashboard component")
            return {
                "DashboardView": DashboardView,
                "available": True,
            }
        except ImportError as e:
            logger.warning(f"Dashboard import error: {e}")
            return {
                "DashboardView": None,
                "available": False,
            }

    @staticmethod
    def import_optimizer():
        """Import optimizer component with fallbacks"""
        if dependency_status.get("numpy", False):
            try:
                from dualgpuopt.gui.optimizer_tab import OptimizerTab

                logger.debug("Using optimizer component")
                return {
                    "OptimizerTab": OptimizerTab,
                    "available": True,
                }
            except ImportError as e:
                logger.warning(f"Optimizer import error: {e}")
        else:
            logger.warning("Numpy not available, optimizer will not function properly")

        return {
            "OptimizerTab": None,
            "available": False,
        }


# Initialize dependency status when module is imported
initialize_dependency_status()
