"""
Settings module for the DualGPUOptimizer GUI.
Provides configuration of application settings, appearance, and GPU overclocking.
"""
from __future__ import annotations

# Re-export the main SettingsTab class
from dualgpuopt.gui.settings.settings_tab import SettingsTab

# Re-export individual components for direct access
from dualgpuopt.gui.settings.appearance import AppearanceFrame
from dualgpuopt.gui.settings.overclocking import OverclockingFrame
from dualgpuopt.gui.settings.application_settings import ApplicationSettingsFrame

# Ensure backward compatibility
from dualgpuopt.gui.settings.compat import *

__all__ = [
    "SettingsTab",
    "AppearanceFrame",
    "OverclockingFrame",
    "ApplicationSettingsFrame",
]
