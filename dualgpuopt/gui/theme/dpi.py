"""
DPI and font scaling utilities for theme system
"""
import sys
import logging
from tkinter import font

logger = logging.getLogger("DualGPUOpt.Theme.DPI")

# Global font scaling - adjust this for larger text across the application
FONT_SCALE = 1.4  # Increase font size by 40%
DEFAULT_FONT_SIZE = 10  # Base font size before scaling
DEFAULT_HEADING_SIZE = 14  # Base heading size before scaling

def fix_dpi_scaling(root):
    """Fix DPI scaling issues with Windows

    Args:
        root: The root Tk window
    """
    try:
        # Try to set DPI awareness programmatically
        if sys.platform == 'win32':
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)  # Process_System_DPI_Aware
            except Exception:
                pass  # Ignore if it fails

        # Force a specific scaling factor if needed
        root.tk.call('tk', 'scaling', 1.3)  # Increase scaling for better readability

        logger.info("Applied DPI scaling fixes")
    except Exception as e:
        logger.warning(f"Failed to fix DPI scaling: {e}")

def scale_font_size(size):
    """Scale a font size by the global scale factor

    Args:
        size: Original font size

    Returns:
        Scaled font size (integer)
    """
    return int(size * FONT_SCALE)

def configure_fonts(root):
    """Configure default fonts for the application

    Args:
        root: The root Tk window
    """
    try:
        # Get available font families
        families = sorted(font.families())

        # Prefer common, well-scaling fonts that look good on high DPI displays
        preferred_fonts = ["Segoe UI", "Helvetica", "Arial", "DejaVu Sans", "Verdana", "Tahoma"]

        # Find the first available preferred font
        main_font = next((f for f in preferred_fonts if f in families), "TkDefaultFont")

        # Configure default fonts
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family=main_font, size=scale_font_size(DEFAULT_FONT_SIZE))

        text_font = font.nametofont("TkTextFont")
        text_font.configure(family=main_font, size=scale_font_size(DEFAULT_FONT_SIZE))

        fixed_font = font.nametofont("TkFixedFont")
        fixed_font.configure(size=scale_font_size(DEFAULT_FONT_SIZE))

        # Update all existing widgets to use the new font
        root.option_add("*Font", default_font)

        logger.info(f"Configured application fonts: {main_font} at size {scale_font_size(DEFAULT_FONT_SIZE)}")
        return main_font
    except Exception as e:
        logger.warning(f"Error configuring fonts: {e}")
        return None

def setup_high_dpi(root):
    """Setup high DPI support for the application

    Args:
        root: The root Tk window
    """
    # Fix DPI scaling first
    fix_dpi_scaling(root)

    # Configure default fonts
    main_font = configure_fonts(root)

    return main_font