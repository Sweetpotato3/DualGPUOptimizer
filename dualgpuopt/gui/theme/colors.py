"""
Theme color definitions for DualGPUOptimizer
"""
import logging

logger = logging.getLogger("DualGPUOpt.Theme.Colors")

# Define theme colors
THEME_DARK_PURPLE = {
    "bg": "#2D1E40",
    "fg": "#FFFFFF",
    "accent": "#8A54FD",
    "accent_light": "#A883FD",
    "accent_dark": "#6A3EBD",
    "warning": "#FF9800",
    "error": "#F44336",
    "success": "#4CAF50",
    "border": "#3D2A50",
    "input_bg": "#241934",
    "secondary_bg": "#372952"
}

# Define light theme
THEME_LIGHT = {
    "bg": "#F5F5F7",
    "fg": "#333333",
    "accent": "#7B3FD5",
    "accent_light": "#9B6AE8",
    "accent_dark": "#5A2DAA",
    "warning": "#F57C00",
    "error": "#D32F2F",
    "success": "#388E3C",
    "border": "#E1E1E6",
    "input_bg": "#FFFFFF",
    "secondary_bg": "#EAEAEF"
}

# Define neon dark theme
THEME_NEON_DARK = {
    "bg": "#1A1A2E",
    "fg": "#E6E6E6",
    "accent": "#9B59B6",
    "accent_light": "#BF7DE0",
    "accent_dark": "#7D3C98",
    "warning": "#FF9800",
    "error": "#F44336",
    "success": "#2ECC71",
    "border": "#2D2D44",
    "input_bg": "#13141C",
    "secondary_bg": "#222235",
    "gradient_start": "#37ECBA",
    "gradient_end": "#E436CA"
}

# Current theme
current_theme = THEME_DARK_PURPLE

# All available themes
AVAILABLE_THEMES = {
    "dark_purple": THEME_DARK_PURPLE,
    "light": THEME_LIGHT,
    "neon_dark": THEME_NEON_DARK
}

def get_theme_by_name(theme_name):
    """Get a theme by name
    
    Args:
        theme_name: Name of the theme
        
    Returns:
        The theme dict or the default theme if not found
    """
    return AVAILABLE_THEMES.get(theme_name, THEME_DARK_PURPLE)

def update_current_theme(theme_name):
    """Update the current theme
    
    Args:
        theme_name: Name of the theme to set as current
        
    Returns:
        The theme dict that was set
    """
    global current_theme
    theme = get_theme_by_name(theme_name)
    current_theme = theme
    logger.debug(f"Updated current theme to {theme_name}")
    return theme 