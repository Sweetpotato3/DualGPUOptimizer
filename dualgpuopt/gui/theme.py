"""
Theme management for DualGPUOptimizer
Provides custom theme functionality for the application
"""
import os
import sys
import logging
import tkinter as tk
from tkinter import ttk, font
from pathlib import Path

logger = logging.getLogger("DualGPUOpt.Theme")

# Global font scaling - adjust this for larger text across the application
FONT_SCALE = 1.4  # Increase font size by 40%
DEFAULT_FONT_SIZE = 10  # Base font size before scaling
DEFAULT_HEADING_SIZE = 14  # Base heading size before scaling

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

def get_theme_path():
    """Get the path to theme resources"""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_path = Path(getattr(sys, '_MEIPASS', os.path.dirname(sys.executable)))
    else:
        # Running in a normal Python environment
        base_path = Path(__file__).parent.parent
    
    return base_path / "resources"

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
    except Exception as e:
        logger.warning(f"Error configuring fonts: {e}")

def toggle_theme(root):
    """Toggle between light and dark themes
    
    Args:
        root: The root Tk window
        
    Returns:
        The name of the new theme
    """
    global current_theme
    
    # Determine which theme to switch to
    if current_theme == THEME_DARK_PURPLE or current_theme == THEME_NEON_DARK:
        current_theme = THEME_LIGHT
        theme_name = "light"
    else:
        current_theme = THEME_NEON_DARK
        theme_name = "neon_dark"
    
    # Apply the new theme
    apply_custom_styling(root)
    
    # Save theme preference to config if available
    try:
        from dualgpuopt.services.config_service import config_service
        config_service.set("theme", theme_name)
        logger.info(f"Saved theme preference: {theme_name}")
    except ImportError:
        logger.warning("Could not save theme preference: config_service not available")
    
    logger.info(f"Switched to {theme_name} theme")
    return theme_name

def set_theme(root, theme_name):
    """Set a specific theme
    
    Args:
        root: The root Tk window
        theme_name: Name of the theme to set
    Returns:
        The name of the theme that was set
    """
    global current_theme
    
    # Set the theme based on the name
    if theme_name in AVAILABLE_THEMES:
        current_theme = AVAILABLE_THEMES[theme_name]
    else:
        # Default to dark purple if theme not found
        current_theme = THEME_DARK_PURPLE
        theme_name = "dark_purple"
    
    # Apply the theme
    apply_custom_styling(root)
    
    # Save theme preference to config if available
    try:
        from dualgpuopt.services.config_service import config_service
        config_service.set("theme", theme_name)
        logger.info(f"Saved theme preference: {theme_name}")
    except ImportError:
        logger.warning("Could not save theme preference: config_service not available")
    
    logger.info(f"Set theme to {theme_name}")
    return theme_name

def load_theme_from_config(root):
    """Load and apply theme from configuration
    
    Args:
        root: The root Tk window
    
    Returns:
        The name of the loaded theme
    """
    try:
        from dualgpuopt.services.config_service import config_service
        theme_name = config_service.get("theme", "dark_purple")
        logger.info(f"Loading theme from config: {theme_name}")
        return set_theme(root, theme_name)
    except ImportError:
        logger.warning("Could not load theme from config: config_service not available")
        return set_theme(root, "dark_purple")  # Default

def apply_theme(root):
    """Apply the current theme to the application
    
    Args:
        root: The root Tk window
    """
    try:
        # Fix DPI scaling first
        fix_dpi_scaling(root)
        
        # Configure default fonts
        configure_fonts(root)
        
        # Load theme from config
        load_theme_from_config(root)
        
        # Try to load ttkthemes if available
        try:
            from ttkthemes import ThemedTk
            # If the root is not already a ThemedTk, we can't theme it
            if not isinstance(root, ThemedTk):
                logger.warning("Root window is not a ThemedTk, using custom styling instead")
                apply_custom_styling(root)
            else:
                root.set_theme("equilux")  # Dark theme similar to our purple
                adjust_equilux_colors(root)
                
                # Apply font scaling even with ttkthemes
                configure_fonts(root)
        except ImportError:
            logger.info("ttkthemes not available, using custom styling")
            apply_custom_styling(root)
    except Exception as e:
        logger.error(f"Error applying theme: {e}")
        # If anything goes wrong, apply minimal styling
        apply_minimal_styling(root)

def apply_custom_styling(root):
    """Apply custom styling using ttk.Style
    
    Args:
        root: The root Tk window
    """
    style = ttk.Style(root)
    
    # Configure TFrame
    style.configure("TFrame", background=current_theme["bg"])
    
    # Configure inner frames in tabs differently
    style.configure("Inner.TFrame", background=current_theme["secondary_bg"])
    
    # Configure TLabel with scaled font
    style.configure("TLabel", 
                    background=current_theme["bg"], 
                    foreground=current_theme["fg"],
                    font=("TkDefaultFont", scale_font_size(DEFAULT_FONT_SIZE)))
    
    # Configure heading style with larger font
    style.configure("Heading.TLabel",
                    background=current_theme["bg"],
                    foreground=current_theme["fg"],
                    font=("TkDefaultFont", scale_font_size(DEFAULT_HEADING_SIZE), "bold"))
    
    # Configure inner labels to match inner frames
    style.configure("Inner.TLabel", 
                    background=current_theme["secondary_bg"],
                    foreground=current_theme["fg"],
                    font=("TkDefaultFont", scale_font_size(DEFAULT_FONT_SIZE)))
    
    # Configure TButton with larger font
    style.configure("TButton", 
                    background=current_theme["accent"],
                    foreground=current_theme["fg"],
                    borderwidth=1,
                    focusthickness=1,
                    focuscolor=current_theme["accent_light"],
                    padding=(10, 6),
                    font=("TkDefaultFont", scale_font_size(DEFAULT_FONT_SIZE)))
    
    style.map("TButton",
               background=[("active", current_theme["accent_light"]),
                          ("disabled", current_theme["bg"])],
               foreground=[("disabled", "#AAAAAA")])
    
    # Configure ThemeToggle.TButton with custom style for theme toggle button
    style.configure("ThemeToggle.TButton", 
                    background=current_theme["secondary_bg"],
                    foreground=current_theme["fg"],
                    borderwidth=1,
                    focusthickness=1,
                    padding=(10, 6),
                    font=("TkDefaultFont", scale_font_size(DEFAULT_FONT_SIZE)))
    
    style.map("ThemeToggle.TButton",
               background=[("active", current_theme["accent"]),
                          ("disabled", current_theme["bg"])],
               foreground=[("disabled", "#AAAAAA")])
    
    # Configure TEntry with larger font
    style.configure("TEntry", 
                    fieldbackground=current_theme["input_bg"],
                    foreground=current_theme["fg"],
                    bordercolor=current_theme["border"],
                    lightcolor=current_theme["accent_light"],
                    darkcolor=current_theme["accent_dark"],
                    insertcolor=current_theme["accent_light"],
                    font=("TkDefaultFont", scale_font_size(DEFAULT_FONT_SIZE)))
    
    # Configure TCombobox with larger font
    style.configure("TCombobox",
                    fieldbackground=current_theme["input_bg"],
                    background=current_theme["bg"],
                    foreground=current_theme["fg"],
                    arrowcolor=current_theme["fg"],
                    bordercolor=current_theme["border"],
                    padding=(5, 4),
                    font=("TkDefaultFont", scale_font_size(DEFAULT_FONT_SIZE)))
    
    style.map("TCombobox",
              fieldbackground=[("readonly", current_theme["input_bg"])],
              selectbackground=[("readonly", current_theme["accent"])],
              selectforeground=[("readonly", current_theme["fg"])])
    
    # Configure option menu
    root.option_add("*TCombobox*Listbox*Background", current_theme["input_bg"])
    root.option_add("*TCombobox*Listbox*Foreground", current_theme["fg"])
    root.option_add("*TCombobox*Listbox*selectBackground", current_theme["accent"])
    root.option_add("*TCombobox*Listbox*selectForeground", current_theme["fg"])
    root.option_add("*TCombobox*Listbox*Font", ("TkDefaultFont", scale_font_size(DEFAULT_FONT_SIZE)))
    
    # Configure TNotebook with larger font
    style.configure("TNotebook", 
                    background=current_theme["bg"],
                    borderwidth=0)
    
    style.configure("TNotebook.Tab", 
                    background=current_theme["bg"],
                    foreground=current_theme["fg"],
                    padding=(12, 5),
                    borderwidth=1,
                    bordercolor=current_theme["border"],
                    font=("TkDefaultFont", scale_font_size(DEFAULT_FONT_SIZE)))
    
    style.map("TNotebook.Tab",
              background=[("selected", current_theme["accent"]),
                          ("active", current_theme["accent_light"])],
              foreground=[("selected", "#FFFFFF"),
                          ("active", "#FFFFFF")])
    
    # Configure TCheckbutton with larger font
    style.configure("TCheckbutton", 
                    background=current_theme["bg"],
                    foreground=current_theme["fg"],
                    indicatorcolor=current_theme["input_bg"],
                    indicatorbackground=current_theme["input_bg"],
                    font=("TkDefaultFont", scale_font_size(DEFAULT_FONT_SIZE)))
    
    style.map("TCheckbutton",
              indicatorcolor=[("selected", current_theme["accent"])],
              background=[("active", current_theme["bg"])])
    
    # Configure Inner.TCheckbutton for checkbuttons inside tab frames
    style.configure("Inner.TCheckbutton", 
                    background=current_theme["secondary_bg"],
                    foreground=current_theme["fg"],
                    indicatorcolor=current_theme["input_bg"],
                    indicatorbackground=current_theme["input_bg"],
                    font=("TkDefaultFont", scale_font_size(DEFAULT_FONT_SIZE)))
    
    style.map("Inner.TCheckbutton",
              indicatorcolor=[("selected", current_theme["accent"])],
              background=[("active", current_theme["secondary_bg"])])
    
    # Configure TProgressbar
    style.configure("TProgressbar", 
                    background=current_theme["accent"],
                    troughcolor=current_theme["secondary_bg"],
                    bordercolor=current_theme["border"],
                    lightcolor=current_theme["accent_light"],
                    darkcolor=current_theme["accent_dark"])
    
    # Configure TLabelframe with larger font
    style.configure("TLabelframe", 
                    background=current_theme["secondary_bg"],
                    foreground=current_theme["fg"],
                    bordercolor=current_theme["border"])
    
    style.configure("TLabelframe.Label", 
                    background=current_theme["bg"],
                    foreground=current_theme["fg"],
                    font=("TkDefaultFont", scale_font_size(DEFAULT_FONT_SIZE)))
    
    # Configure TPanedwindow
    style.configure("TPanedwindow", 
                    background=current_theme["bg"],
                    sashrelief="flat")
    
    # Configure TScale (slider)
    style.configure("TScale", 
                    background=current_theme["bg"],
                    troughcolor=current_theme["secondary_bg"],
                    sliderrelief="flat")
    
    # Root window configuration
    root.configure(background=current_theme["bg"])
    
    # Configure standard Tkinter widgets by updating the option database
    root.option_add("*Text.background", current_theme["input_bg"])
    root.option_add("*Text.foreground", current_theme["fg"])
    root.option_add("*Text.insertBackground", current_theme["fg"])  # Text cursor
    root.option_add("*Text.selectBackground", current_theme["accent"])
    root.option_add("*Text.selectForeground", current_theme["fg"])
    root.option_add("*Text.font", ("TkDefaultFont", scale_font_size(DEFAULT_FONT_SIZE)))
    
    root.option_add("*Listbox.background", current_theme["input_bg"])
    root.option_add("*Listbox.foreground", current_theme["fg"])
    root.option_add("*Listbox.selectBackground", current_theme["accent"])
    root.option_add("*Listbox.selectForeground", current_theme["fg"])
    root.option_add("*Listbox.font", ("TkDefaultFont", scale_font_size(DEFAULT_FONT_SIZE)))
    
    root.option_add("*Canvas.background", current_theme["bg"])
    root.option_add("*Canvas.highlightthickness", 0)  # Remove highlight border
    
    root.option_add("*Menu.background", current_theme["bg"])
    root.option_add("*Menu.foreground", current_theme["fg"])
    root.option_add("*Menu.activeBackground", current_theme["accent"])
    root.option_add("*Menu.activeForeground", current_theme["fg"])
    root.option_add("*Menu.font", ("TkDefaultFont", scale_font_size(DEFAULT_FONT_SIZE)))
    
    # Override any platform-specific appearance
    try:
        root.tk.call("tk_setPalette", current_theme["bg"])
    except Exception:
        pass

def adjust_equilux_colors(root):
    """Adjust equilux theme to match our purple colors
    
    Args:
        root: The root Tk window
    """
    style = ttk.Style(root)
    
    # Adjust accent colors for buttons
    style.configure("TButton", 
                    background=current_theme["accent"])
    
    style.map("TButton",
              background=[("active", current_theme["accent_light"]),
                          ("disabled", "#555555")])
    
    # Adjust selected tab color
    style.map("TNotebook.Tab",
              background=[("selected", current_theme["accent"]),
                          ("active", current_theme["accent_light"])])
    
    # Configure inner frame style
    style.configure("Inner.TFrame", background=current_theme["secondary_bg"])
    style.configure("Inner.TLabel", background=current_theme["secondary_bg"])
    
    # Configure option menu items
    root.option_add("*TCombobox*Listbox*Background", current_theme["input_bg"])
    root.option_add("*TCombobox*Listbox*Foreground", current_theme["fg"])
    root.option_add("*TCombobox*Listbox*selectBackground", current_theme["accent"])

def apply_minimal_styling(root):
    """Apply minimal styling in case of failures
    
    Args:
        root: The root Tk window
    """
    style = ttk.Style(root)
    
    # Basic button styling
    style.configure("TButton", padding=(10, 5))
    
    # Basic tab styling
    style.configure("TNotebook.Tab", padding=(10, 2))

# Theme Toggle Button Widget
class ThemeToggleButton(ttk.Button):
    """A button that toggles between light and dark themes"""
    
    def __init__(self, master, **kwargs):
        """Initialize a theme toggle button
        
        Args:
            master: Parent widget
            **kwargs: Additional keyword arguments for the button
        """
        # Initialize with theme toggle style
        super().__init__(
            master, 
            text="🌙" if current_theme == THEME_LIGHT else "☀️", 
            style="ThemeToggle.TButton",
            command=self._toggle_theme,
            **kwargs
        )
    
    def _toggle_theme(self):
        """Toggle the theme and update the button text"""
        theme_name = toggle_theme(self.winfo_toplevel())
        
        # Update button text based on new theme
        new_text = "🌙" if theme_name == "light" else "☀️"
        self.configure(text=new_text)
        
        # Publish theme changed event if event_bus is available
        try:
            from dualgpuopt.services.event_service import event_bus
            event_bus.publish("theme_changed", {"theme": theme_name})
        except ImportError:
            pass  # Ignore if event_bus is not available 