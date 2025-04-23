"""
Compatibility layer for the refactored settings module.
Preserves the original API for backward compatibility with the old settings.py module.
"""
from __future__ import annotations

import logging

# Import from refactored modules
from dualgpuopt.gui.settings.settings_tab import SettingsTab

logger = logging.getLogger("dualgpuopt.gui.settings.compat")
logger.info("Using refactored settings module with compatibility layer")

# Re-export main classes and functions
__all__ = ["SettingsTab"]

# For any code that directly imports SettingsTab from the old location,
# this ensures it will still work when settings.py is completely replaced
# with the new, modular version.

# Example usage:
# from dualgpuopt.gui.settings import SettingsTab  # will work with old or new implementation
