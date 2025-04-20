"""
Test script for theme functionality in DualGPUOptimizer
"""
import os
import sys
import logging
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# Add the parent directory to the path so we can import the dualgpuopt package
parent_dir = str(Path(__file__).resolve().parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from dualgpuopt.gui.theme import AVAILABLE_THEMES, set_theme, load_theme_from_config, current_theme
from dualgpuopt.gui.theme_selector import ThemeSelector
from dualgpuopt.services.config_service import config_service
from dualgpuopt.services.event_service import event_bus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ThemeTest")

class ThemeTestApp(ttk.Frame):
    """Test application for theme functionality"""
    
    def __init__(self, parent):
        """Initialize the test application"""
        super().__init__(parent, padding=20)
        self.parent = parent
        
        # Configure grid layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Title row
        self.rowconfigure(1, weight=0)  # Theme selector row
        self.rowconfigure(2, weight=0)  # Current theme row
        self.rowconfigure(3, weight=1)  # Widget showcase row
        self.rowconfigure(4, weight=0)  # Status row
        
        # Title
        ttk.Label(
            self, 
            text="DualGPUOptimizer Theme Test", 
            style="Heading.TLabel",
            font=("", 16, "bold")
        ).grid(row=0, column=0, pady=20)
        
        # Theme selector
        selector_frame = ttk.Frame(self)
        selector_frame.grid(row=1, column=0, sticky="ew", pady=10)
        
        self.theme_selector = ThemeSelector(
            selector_frame,
            label_text="Select Theme:",
            callback=self._on_theme_changed
        )
        self.theme_selector.pack(anchor="center")
        
        # Current theme info
        info_frame = ttk.LabelFrame(self, text="Current Theme Information")
        info_frame.grid(row=2, column=0, sticky="ew", pady=10)
        info_frame.columnconfigure(1, weight=1)
        
        ttk.Label(info_frame, text="Theme Name:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.theme_name_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.theme_name_var).grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        ttk.Label(info_frame, text="Background:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.bg_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.bg_var).grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        ttk.Label(info_frame, text="Foreground:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.fg_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.fg_var).grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        ttk.Label(info_frame, text="Accent:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.accent_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.accent_var).grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        # Widget showcase
        showcase_frame = ttk.LabelFrame(self, text="Widget Showcase")
        showcase_frame.grid(row=3, column=0, sticky="nsew", pady=10)
        showcase_frame.columnconfigure(0, weight=1)
        showcase_frame.columnconfigure(1, weight=1)
        
        # Buttons
        ttk.Button(showcase_frame, text="Regular Button").grid(row=0, column=0, padx=10, pady=10)
        ttk.Button(showcase_frame, text="Disabled Button", state="disabled").grid(row=0, column=1, padx=10, pady=10)
        
        # Entry
        ttk.Label(showcase_frame, text="Text Entry:").grid(row=1, column=0, sticky="e", padx=10, pady=10)
        ttk.Entry(showcase_frame).grid(row=1, column=1, sticky="w", padx=10, pady=10)
        
        # Combobox
        ttk.Label(showcase_frame, text="Dropdown:").grid(row=2, column=0, sticky="e", padx=10, pady=10)
        ttk.Combobox(showcase_frame, values=["Option 1", "Option 2", "Option 3"]).grid(row=2, column=1, sticky="w", padx=10, pady=10)
        
        # Checkbutton
        ttk.Label(showcase_frame, text="Checkbox:").grid(row=3, column=0, sticky="e", padx=10, pady=10)
        ttk.Checkbutton(showcase_frame, text="Enable option").grid(row=3, column=1, sticky="w", padx=10, pady=10)
        
        # Status frame
        status_frame = ttk.Frame(self)
        status_frame.grid(row=4, column=0, sticky="ew", pady=10)
        
        self.status_var = tk.StringVar(value="Status: Initialized")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side="left")
        
        # Add theme reset button
        ttk.Button(
            status_frame,
            text="Reset to Default",
            command=self._reset_theme
        ).pack(side="right", padx=10)
        
        # Subscribe to theme change events
        event_bus.subscribe("config_changed:theme", self._handle_theme_event)
        
        # Update theme info
        self._update_theme_info()
    
    def _on_theme_changed(self, theme_name):
        """Handle theme changes from selector"""
        self.status_var.set(f"Status: Theme changed to {theme_name}")
        self._update_theme_info()
    
    def _handle_theme_event(self, theme_name):
        """Handle theme change events from event bus"""
        logger.info(f"Theme changed event received: {theme_name}")
        self.status_var.set(f"Status: Theme event received - {theme_name}")
        self._update_theme_info()
    
    def _update_theme_info(self):
        """Update the theme information display"""
        # Find theme name from current_theme
        theme_name = next(
            (name for name, colors in AVAILABLE_THEMES.items() 
             if colors == current_theme),
            "unknown"
        )
        
        # Update display variables
        self.theme_name_var.set(theme_name)
        self.bg_var.set(current_theme.get("bg", "unknown"))
        self.fg_var.set(current_theme.get("fg", "unknown"))
        self.accent_var.set(current_theme.get("accent", "unknown"))
    
    def _reset_theme(self):
        """Reset to default theme"""
        set_theme(self.parent, "dark_purple")
        self.theme_selector.set_theme("dark_purple")
        self.status_var.set("Status: Reset to default theme")


def main():
    """Main entry point"""
    # Initialize Tk
    root = tk.Tk()
    root.title("Theme Test")
    root.geometry("800x600")
    
    # Apply theme from config
    try:
        logger.info("Loading theme from config")
        theme_name = load_theme_from_config(root)
        logger.info(f"Loaded theme: {theme_name}")
    except Exception as e:
        logger.error(f"Error loading theme: {e}")
        # Apply default theme as fallback
        from dualgpuopt.gui.theme import apply_custom_styling
        apply_custom_styling(root)
    
    # Create and show the test app
    app = ThemeTestApp(root)
    app.pack(fill=tk.BOTH, expand=True)
    
    # Run the app
    logger.info("Starting theme test application")
    root.mainloop()
    
    # After main loop, print the final config
    logger.info(f"Final theme setting in config: {config_service.get('theme', 'unknown')}")


if __name__ == "__main__":
    main() 