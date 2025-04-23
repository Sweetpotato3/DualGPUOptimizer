"""
Launcher module for DualGPUOptimizer.

This module provides functionality for launching models on multiple GPUs
with optimized configuration parameters.
"""
from __future__ import annotations

from dualgpuopt.gui.launcher.config_handler import ConfigHandler
from dualgpuopt.gui.launcher.launch_controller import LaunchController
from dualgpuopt.gui.launcher.model_validation import ModelValidator
from dualgpuopt.gui.launcher.parameter_resolver import ParameterResolver
from dualgpuopt.gui.launcher.process_monitor import ProcessMonitor

# Import from our refactored modules
from dualgpuopt.gui.launcher.ui_components import LauncherTab

# For backward compatibility, make the primary classes available at the module level
__all__ = [
    "ConfigHandler",
    "LaunchController",
    "LauncherTab",
    "ModelValidator",
    "ParameterResolver",
    "ProcessMonitor",
]
