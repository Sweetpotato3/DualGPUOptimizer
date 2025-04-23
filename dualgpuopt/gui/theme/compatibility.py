"""
Theme compatibility layer to handle various UI toolkit configurations
"""
import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict

# Configure logger
logger = logging.getLogger("DualGPUOpt.Theme.Compat")

# Try to import optional theme dependencies
try:
    import ttkthemes
    from ttkthemes import ThemedStyle, ThemedTk

    TTKTHEMES_AVAILABLE = True
    logger.debug("ttkthemes is available")
except ImportError:
    TTKTHEMES_AVAILABLE = False
    logger.debug("ttkthemes is not available")

try:
    import ttkbootstrap as ttk_bs

    TTKBOOTSTRAP_AVAILABLE = True
    logger.debug("ttkbootstrap is available")
except ImportError:
    TTKBOOTSTRAP_AVAILABLE = False
    logger.debug("ttkbootstrap is not available")


def apply_theme_with_compatibility(window: Any, theme_data: Dict[str, Any]) -> None:
    """
    Apply theme with compatibility for different window types

    Args:
    ----
        window: The window or root widget to apply the theme to
        theme_data: Theme data with colors and other settings

    """
    # Check if we have ttkbootstrap window
    if TTKBOOTSTRAP_AVAILABLE and hasattr(window, "style") and hasattr(window.style, "theme_use"):
        try:
            # For ttkbootstrap windows
            logger.debug(
                f"Applying ttkbootstrap theme: {theme_data.get('bootstrap_theme', 'darkly')}"
            )
            window.style.theme_use(theme_data.get("bootstrap_theme", "darkly"))
            return
        except Exception as e:
            logger.warning(f"Failed to apply ttkbootstrap theme: {e}")

    # Check if we have ttkthemes window
    if TTKTHEMES_AVAILABLE and hasattr(window, "set_theme"):
        try:
            # For ThemedTk windows
            logger.debug(f"Applying ttkthemes theme: {theme_data.get('ttk_theme', 'equilux')}")
            window.set_theme(theme_data.get("ttk_theme", "equilux"))
            return
        except Exception as e:
            logger.warning(f"Failed to apply ttkthemes theme: {e}")

    # Fall back to standard ttk styling with our colors
    try:
        # Get or create style
        style = ttk.Style(window)

        # Configure standard styles
        style.configure("TFrame", background=theme_data.get("bg", "#1c1c1c"))
        style.configure(
            "TLabel",
            background=theme_data.get("bg", "#1c1c1c"),
            foreground=theme_data.get("fg", "#ffffff"),
        )
        style.configure(
            "TButton",
            background=theme_data.get("accent", "#5c5c5c"),
            foreground=theme_data.get("fg", "#ffffff"),
        )

        # Configure window background if it's a tk.Tk
        if isinstance(window, (tk.Tk, tk.Toplevel)):
            window.configure(background=theme_data.get("bg", "#1c1c1c"))

        logger.debug("Applied custom ttk styling")
    except Exception as e:
        logger.warning(f"Failed to apply custom styling: {e}")


def try_apply_ttkthemes(root: tk.Tk, theme_name: str = "equilux") -> bool:
    """
    Try to apply a ttkthemes theme

    Args:
    ----
        root: The root window
        theme_name: Name of the ttkthemes theme to apply

    Returns:
    -------
        True if successful, False otherwise

    """
    if not TTKTHEMES_AVAILABLE:
        return False

    try:
        # For already themed windows
        if hasattr(root, "set_theme"):
            root.set_theme(theme_name)
            return True

        # For regular Tk windows
        style = ThemedStyle(root)
        style.set_theme(theme_name)
        return True
    except Exception as e:
        logger.warning(f"Failed to apply ttkthemes theme: {e}")
        return False


def ensure_status_var(app_instance):
    """
    Ensure the application instance has a status_var attribute

    Args:
    ----
        app_instance: The application instance to check/update

    """
    if not hasattr(app_instance, "status_var"):
        logger.debug("Adding missing status_var to application instance")
        app_instance.status_var = tk.StringVar(value="Ready")

    return app_instance.status_var
