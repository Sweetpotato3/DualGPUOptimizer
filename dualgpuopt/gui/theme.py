"""
Theme management for DualGPUOptimizer
Provides custom theme functionality for the application

Note: This module now re-exports the functionality from the refactored
theme package for backward compatibility.
"""
import logging

# Set up the logger for backward compatibility
logger = logging.getLogger("DualGPUOpt.Theme")
logger.info("Using refactored theme system via compatibility layer")

# Re-export everything from the new theme package
from dualgpuopt.gui.theme.compat import (
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

# The original module's implementation has been refactored into the dualgpuopt/gui/theme/ package
# while maintaining backward compatibility through this file