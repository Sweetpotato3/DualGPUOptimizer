"""
DualGPUOptimizer Qt Interface Module

This module provides a Qt-based graphical user interface for the DualGPUOptimizer
application with real-time GPU monitoring, memory profiling, and model optimization.
"""

__version__ = "1.0.0"
__author__ = "DualGPUOptimizer Team"

from dualgpuopt.qt.app_window import DualGPUOptimizerApp

# Export tab components
from dualgpuopt.qt.dashboard_tab import DashboardTab, GPUCard, GPUChart
from dualgpuopt.qt.launcher_tab import LauncherTab

# Export main application components
from dualgpuopt.qt.main import main
from dualgpuopt.qt.memory_tab import MemoryProfilerTab
from dualgpuopt.qt.optimizer_tab import OptimizerTab
from dualgpuopt.qt.settings_tab import SettingsManager, SettingsTab

# Export system tray components
from dualgpuopt.qt.system_tray import GPUTrayManager

# Version information
VERSION_INFO = {
    "major": 1,
    "minor": 0,
    "patch": 0,
    "release": "stable",
}


def get_version():
    """Return the current version as a string."""
    return f"{VERSION_INFO['major']}.{VERSION_INFO['minor']}.{VERSION_INFO['patch']}-{VERSION_INFO['release']}"
