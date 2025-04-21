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
from dualgpuopt.gui.theme import (
    # Colors
    current_theme, AVAILABLE_THEMES,
    THEME_DARK_PURPLE, THEME_LIGHT, THEME_NEON_DARK,

    # DPI and font scaling
    FONT_SCALE, DEFAULT_FONT_SIZE, DEFAULT_HEADING_SIZE,
    fix_dpi_scaling, scale_font_size, configure_fonts,

    # Styling
    apply_minimal_styling, apply_custom_styling, adjust_equilux_colors,

    # Core
    get_theme_path, toggle_theme, set_theme, load_theme_from_config, apply_theme,
    ThemeToggleButton
)

# The apply_theme function is the main entry point, and it calls through to
# the new modular code structure under the hood while keeping the same API signature