"""
Compatibility module for theme system
Provides compatibility with third-party theming systems
"""
import logging
import tkinter as tk
from tkinter import ttk

from dualgpuopt.gui.theme.styling import apply_custom_styling, adjust_equilux_colors, apply_minimal_styling
from dualgpuopt.gui.theme.dpi import setup_high_dpi

logger = logging.getLogger("DualGPUOpt.Theme.Compatibility")

def try_apply_ttkthemes(root):
    """Try to apply ttkthemes if available
    
    Args:
        root: The root Tk window
        
    Returns:
        bool: True if ttkthemes was successfully applied, False otherwise
    """
    try:
        from ttkthemes import ThemedTk
        
        # If the root is not already a ThemedTk, we can't theme it
        if not isinstance(root, ThemedTk):
            logger.warning("Root window is not a ThemedTk, using custom styling instead")
            return False
            
        # Apply a dark theme similar to our purple
        root.set_theme("equilux")
        
        # Adjust colors to match our theme
        adjust_equilux_colors(root)
        
        logger.info("Applied ttkthemes equilux theme with custom adjustments")
        return True
    except ImportError:
        logger.info("ttkthemes not available, using custom styling")
        return False
    except Exception as e:
        logger.error(f"Error applying ttkthemes: {e}")
        return False

def apply_theme_with_compatibility(root):
    """Apply theme with compatibility considerations
    
    Args:
        root: The root Tk window
    """
    try:
        # Fix DPI scaling and configure fonts
        setup_high_dpi(root)
        
        # Try to use ttkthemes if available
        if not try_apply_ttkthemes(root):
            # Fall back to custom styling
            apply_custom_styling(root)
            
    except Exception as e:
        logger.error(f"Error applying theme: {e}")
        # If anything goes wrong, apply minimal styling
        apply_minimal_styling(root) 