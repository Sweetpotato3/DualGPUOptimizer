"""
Launcher tab for running models with optimized settings

This module re-exports classes from the new modular structure
to maintain backward compatibility.
"""
from __future__ import annotations

import logging

from dualgpuopt.gui.launcher.config_handler import ConfigHandler

# Import from refactored modules for direct access
from dualgpuopt.gui.launcher.launch_controller import LaunchController
from dualgpuopt.gui.launcher.model_validation import ModelValidator
from dualgpuopt.gui.launcher.parameter_resolver import ParameterResolver
from dualgpuopt.gui.launcher.process_monitor import ProcessMonitor

# Import from the compatibility layer
from dualgpuopt.gui.launcher_compat import LauncherTab, ModelRunner

# Initialize logger
logger = logging.getLogger("DualGPUOpt.Launcher")

# Re-export classes for backward compatibility
__all__ = [
    "ConfigHandler",
    "LaunchController",
    "LauncherTab",
    "ModelRunner",
    "ModelValidator",
    "ParameterResolver",
    "ProcessMonitor",
]


# Import the estimate_model_size function for backward compatibility
def model_name_to_params(model_name: str) -> float:
    """
    Extract model size in billions from model name

    Args:
    ----
        model_name: Model name or path

    Returns:
    -------
        Model size in billions of parameters

    """
    controller = LaunchController()
    return controller._estimate_model_size(model_name)
