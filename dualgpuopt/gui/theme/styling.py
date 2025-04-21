"""
Theme styling utilities for applying styles to widgets
"""
import tkinter as tk
from tkinter import ttk
import logging

from dualgpuopt.gui.theme.colors import current_theme, AVAILABLE_THEMES
from dualgpuopt.gui.theme.dpi import scale_font_size, DEFAULT_FONT_SIZE, DEFAULT_HEADING_SIZE

logger = logging.getLogger("DualGPUOpt.Theme.Styling")

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
    root.option_add("*TCombobox*Listbox*selectForeground", current_theme["fg"])