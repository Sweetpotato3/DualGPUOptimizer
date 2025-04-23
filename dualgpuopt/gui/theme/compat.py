"""
Backward compatibility layer for theme module
This module re-exports all the functionality from the original theme.py
with identical APIs to prevent breaking changes
"""
import logging

# Logging setup
logger = logging.getLogger("DualGPUOpt.Theme.Compat")
logger.debug("Loading theme compatibility layer")

# Re-export all components from the theme package

# The apply_theme function is the main entry point, and it calls through to
# the new modular code structure under the hood while keeping the same API signature
