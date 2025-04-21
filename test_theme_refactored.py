"""
Test script to verify the refactored theme module is working correctly
"""
import tkinter as tk
import logging
from tkinter import ttk

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ThemeTest")

# Import from the refactored theme package
from dualgpuopt.gui.theme import (
    apply_theme,
    set_theme,
    current_theme,
    AVAILABLE_THEMES,
    ThemeToggleButton
)

def create_test_window():
    """Create a test window with various widgets"""
    # Create a root window
    root = tk.Tk()
    root.title("Theme Refactoring Test")
    root.geometry("800x600")

    # Apply theme
    logger.info("Applying theme...")
    apply_theme(root)

    # Create a main frame
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    # Add a title
    ttk.Label(
        frame,
        text="Theme Refactoring Test",
        style="Heading.TLabel"
    ).pack(pady=20)

    # Add some widgets
    ttk.Button(frame, text="Test Button").pack(pady=10)
    ttk.Entry(frame).pack(pady=10)
    ttk.Checkbutton(frame, text="Test Checkbox").pack(pady=10)

    # Add a theme toggle button
    ttk.Label(frame, text="Toggle Theme:").pack(pady=5)
    ThemeToggleButton(frame).pack(pady=10)

    # Add theme info
    info_frame = ttk.LabelFrame(frame, text="Current Theme Info")
    info_frame.pack(pady=20, fill=tk.X)

    # Display current theme
    current_theme_var = tk.StringVar()
    ttk.Label(info_frame, text="Current Theme:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    ttk.Label(info_frame, textvariable=current_theme_var).grid(row=0, column=1, padx=10, pady=5, sticky="w")

    # Display theme colors
    bg_var = tk.StringVar()
    fg_var = tk.StringVar()
    accent_var = tk.StringVar()

    ttk.Label(info_frame, text="Background:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    ttk.Label(info_frame, textvariable=bg_var).grid(row=1, column=1, padx=10, pady=5, sticky="w")

    ttk.Label(info_frame, text="Foreground:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    ttk.Label(info_frame, textvariable=fg_var).grid(row=2, column=1, padx=10, pady=5, sticky="w")

    ttk.Label(info_frame, text="Accent:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
    ttk.Label(info_frame, textvariable=accent_var).grid(row=3, column=1, padx=10, pady=5, sticky="w")

    # Add buttons to switch themes
    themes_frame = ttk.Frame(frame)
    themes_frame.pack(pady=10)

    for theme_name in AVAILABLE_THEMES.keys():
        ttk.Button(
            themes_frame,
            text=f"Set {theme_name.title()}",
            command=lambda tn=theme_name: set_theme(root, tn)
        ).pack(side=tk.LEFT, padx=5)

    # Function to update theme info
    def update_theme_info():
        theme_name = next((name for name, colors in AVAILABLE_THEMES.items()
                         if colors == current_theme), "unknown")
        current_theme_var.set(theme_name)
        bg_var.set(current_theme.get("bg", "unknown"))
        fg_var.set(current_theme.get("fg", "unknown"))
        accent_var.set(current_theme.get("accent", "unknown"))

        # Schedule next update
        root.after(100, update_theme_info)

    # Start updating theme info
    update_theme_info()

    return root

if __name__ == "__main__":
    logger.info("Starting theme test application...")
    root = create_test_window()
    logger.info("Running main loop...")
    root.mainloop()