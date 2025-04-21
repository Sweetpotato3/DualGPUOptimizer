"""
DualGPUOptimizer Qt Interface Module

This module provides a Qt-based graphical user interface for the DualGPUOptimizer
application with real-time GPU monitoring, memory profiling, and model optimization.
"""

__version__ = "1.0.0"
__author__ = "DualGPUOptimizer Team"

import logging
import sys
from pathlib import Path

logger = logging.getLogger("DualGPUOpt.Qt")

# Check if PySide6 is available
try:
    import PySide6
    from PySide6 import QtWidgets, QtCore, QtGui
    logger.info(f"PySide6 version: {PySide6.__version__}")
    QT_AVAILABLE = True
except ImportError as e:
    logger.error(f"PySide6 not available: {e}")
    QT_AVAILABLE = False

# Forward references to prevent circular imports
AppWindow = None
SystemTrayManager = None

def init_qt():
    """Initialize Qt module and imports"""
    global AppWindow, SystemTrayManager
    
    if not QT_AVAILABLE:
        logger.error("Cannot initialize Qt module: PySide6 not available")
        return False
    
    try:
        # Import conditionally to avoid circular imports
        from .app_window import DualGPUOptimizerApp
        from .system_tray import GPUTrayManager
        
        AppWindow = DualGPUOptimizerApp
        SystemTrayManager = GPUTrayManager
        logger.info("Qt module initialized successfully")
        return True
    except ImportError as e:
        logger.error(f"Failed to initialize Qt module: {e}")
        return False

def get_app_window():
    """Get the application window class"""
    if AppWindow is None:
        init_qt()
    return AppWindow

def get_system_tray_manager():
    """Get the system tray manager class"""
    if SystemTrayManager is None:
        init_qt()
    return SystemTrayManager

# Export tab components
from dualgpuopt.qt.dashboard_tab import DashboardTab, GPUCard, GPUChart
from dualgpuopt.qt.launcher_tab import LauncherTab

# Export main application components
from dualgpuopt.qt.main import main
from dualgpuopt.qt.memory_tab import MemoryProfilerTab
from dualgpuopt.qt.optimizer_tab import OptimizerTab
from dualgpuopt.qt.settings_tab import SettingsManager, SettingsTab

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
