"""
Theme management for DualGPUOptimizer
Provides custom theme functionality for the application
"""

import logging

# Configure logger
logger = logging.getLogger("DualGPUOpt.Theme")

# Import and re-export all public theme API
from dualgpuopt.gui.theme.colors import (
    current_theme, AVAILABLE_THEMES, 
    THEME_DARK_PURPLE, THEME_LIGHT, THEME_NEON_DARK
)

from dualgpuopt.gui.theme.dpi import (
    FONT_SCALE, DEFAULT_FONT_SIZE, DEFAULT_HEADING_SIZE,
    fix_dpi_scaling, scale_font_size, configure_fonts, setup_high_dpi
)

from dualgpuopt.gui.theme.styling import (
    apply_minimal_styling, apply_custom_styling, adjust_equilux_colors
)

from dualgpuopt.gui.theme.compatibility import (
    apply_theme_with_compatibility, try_apply_ttkthemes
)

from dualgpuopt.gui.theme.core import (
    get_theme_path, toggle_theme, set_theme, load_theme_from_config, apply_theme,
    ThemeToggleButton
)

# For backward compatibility, export the apply_theme function as the main entry point
__all__ = [
    # Colors
    "current_theme", "AVAILABLE_THEMES", 
    "THEME_DARK_PURPLE", "THEME_LIGHT", "THEME_NEON_DARK",
    
    # DPI and font scaling
    "FONT_SCALE", "DEFAULT_FONT_SIZE", "DEFAULT_HEADING_SIZE",
    "fix_dpi_scaling", "scale_font_size", "configure_fonts", "setup_high_dpi",
    
    # Styling
    "apply_minimal_styling", "apply_custom_styling", "adjust_equilux_colors",
    
    # Compatibility
    "apply_theme_with_compatibility", "try_apply_ttkthemes",
    
    # Core
    "get_theme_path", "toggle_theme", "set_theme", "load_theme_from_config", "apply_theme",
    "ThemeToggleButton"
] 