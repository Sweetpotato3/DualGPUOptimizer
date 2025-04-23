"""
Settings module for the DualGPUOptimizer GUI.
This file redirects imports to the refactored modular structure.
"""
from __future__ import annotations

import logging
import warnings

# Import everything from the refactored settings module
from dualgpuopt.gui.settings.settings_tab import SettingsTab
from dualgpuopt.gui.settings.appearance import AppearanceFrame
from dualgpuopt.gui.settings.overclocking import OverclockingFrame
from dualgpuopt.gui.settings.application_settings import ApplicationSettingsFrame

# Set up logging
logger = logging.getLogger("dualgpuopt.gui.settings")
logger.info("Using refactored settings module - redirecting from settings.py")

# Issue a deprecation warning
warnings.warn(
    "Direct import from 'dualgpuopt.gui.settings' is deprecated. "
    "Import from 'dualgpuopt.gui.settings.settings_tab' or other submodules instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export main classes and functions for backward compatibility
__all__ = [
    "SettingsTab",
    "AppearanceFrame",
    "OverclockingFrame",
    "ApplicationSettingsFrame",
]
