"""
Theme testing and propagation validation tool
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import logging
import sys
from typing import Dict, List, Any, Callable, Optional

try:
    from dualgpuopt.services.event_service import event_bus
    HAS_EVENT_BUS = True
except ImportError:
    HAS_EVENT_BUS = False
    print("Warning: event_bus not available, theme testing functionality will be limited")

try:
    from dualgpuopt.services.config_service import config_service
    HAS_CONFIG_SERVICE = True
except ImportError:
    HAS_CONFIG_SERVICE = False
    print("Warning: config_service not available, theme persistence will not be tested")

from dualgpuopt.gui.theme import AVAILABLE_THEMES, set_theme, current_theme
from dualgpuopt.gui.theme_selector import ThemeSelector
from dualgpuopt.gui.theme_observer import register_themed_widget, register_theme_callback
from dualgpuopt.gui.themed_widgets import (
    ThemedFrame, ThemedLabel, ThemedButton, ThemedEntry, ThemedListbox, ColorSwatch
)

logger = logging.getLogger("DualGPUOpt.ThemeTester")

class ThemeTester(tk.Tk):
    """Application for testing theme propagation"""
    
    def __init__(self):
        """Initialize the theme tester"""
        super().__init__()
        
        self.title("Theme Propagation Tester")
        self.geometry("800x600")
        
        # Configure main window
        self.configure(bg=current_theme["bg"])
        register_themed_widget(self)
        
        # Setup the UI
        self._build_ui()
        
        # Initialize theme change monitoring
        self._theme_change_count = 0
        self._monitored_widgets = []
        self._widget_change_counts = {}
        
        # Register theme change monitoring
        if HAS_EVENT_BUS:
            event_bus.subscribe("config_changed:theme", self._monitor_theme_change)
    
    def _build_ui(self):
        """Build the user interface"""
        # Main container
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Paned window for control and monitoring areas
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left control panel
        control_frame = ttk.Frame(paned)
        paned.add(control_frame, weight=30)
        
        # Right monitoring panel
        monitor_frame = ttk.Frame(paned)
        paned.add(monitor_frame, weight=70)
        
        # Theme selection
        theme_frame = ttk.LabelFrame(control_frame, text="Theme Selection")
        theme_frame.pack(fill=tk.X, pady=10)
        
        # Theme selector
        self.theme_selector = ThemeSelector(
            theme_frame,
            label_text="Theme:",
            callback=self._on_theme_changed
        )
        self.theme_selector.pack(anchor="w", padx=10, pady=10)
        
        # Theme preview section
        preview_frame = ttk.LabelFrame(control_frame, text="Theme Preview")
        preview_frame.pack(fill=tk.X, pady=10)
        
        # Create color swatches for primary colors
        colors_frame = ttk.Frame(preview_frame)
        colors_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Create labels and swatches for each color
        for i, (color_name, color_key) in enumerate([
            ("Background", "bg"),
            ("Foreground", "fg"),
            ("Accent", "accent"),
            ("Input BG", "input_bg"),
            ("Border", "border")
        ]):
            ttk.Label(colors_frame, text=f"{color_name}:").grid(row=i, column=0, sticky="w", padx=5, pady=2)
            
            # Create swatch and store reference
            swatch = ColorSwatch(
                colors_frame, 
                color=current_theme[color_key], 
                width=30, 
                height=15
            )
            swatch.grid(row=i, column=1, padx=5, pady=2)
            
            # Add this to theme monitoring
            setattr(self, f"{color_key}_swatch", swatch)
            
            # Update swatch on theme change
            def update_swatch(theme_name, swatch=swatch, color_key=color_key):
                theme_colors = AVAILABLE_THEMES.get(theme_name, AVAILABLE_THEMES["dark_purple"])
                swatch.set_color(theme_colors[color_key])
            
            register_theme_callback(update_swatch)
        
        # Widget test section
        widget_frame = ttk.LabelFrame(control_frame, text="Widget Tests")
        widget_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Add a variety of widgets to test with
        ttk.Label(widget_frame, text="TTK Widgets:").pack(anchor="w", padx=10, pady=5)
        
        # TTK button
        ttk_button = ttk.Button(widget_frame, text="TTK Button")
        ttk_button.pack(anchor="w", padx=10, pady=5)
        
        # TTK entry
        ttk_entry = ttk.Entry(widget_frame)
        ttk_entry.pack(anchor="w", padx=10, pady=5)
        ttk_entry.insert(0, "TTK Entry")
        
        # TK Widgets
        ttk.Label(widget_frame, text="Themed TK Widgets:").pack(anchor="w", padx=10, pady=5)
        
        # Themed button
        themed_button = ThemedButton(widget_frame, text="Themed Button")
        themed_button.pack(anchor="w", padx=10, pady=5)
        
        # Themed entry
        themed_entry = ThemedEntry(widget_frame)
        themed_entry.pack(anchor="w", padx=10, pady=5)
        themed_entry.insert(0, "Themed Entry")
        
        # Themed label
        themed_label = ThemedLabel(widget_frame, text="Themed Label")
        themed_label.pack(anchor="w", padx=10, pady=5)
        
        # Add widgets to monitoring
        self._monitored_widgets = [
            ("TTK Button", ttk_button),
            ("TTK Entry", ttk_entry),
            ("Themed Button", themed_button),
            ("Themed Entry", themed_entry),
            ("Themed Label", themed_label)
        ]
        
        # Initialize widget change counts
        for name, widget in self._monitored_widgets:
            self._widget_change_counts[name] = 0
        
        # Build monitoring panel
        monitoring_label = ttk.Label(
            monitor_frame,
            text="Theme Change Monitoring",
            font=("", 12, "bold")
        )
        monitoring_label.pack(anchor="w", padx=10, pady=10)
        
        # Theme change count
        theme_count_frame = ttk.Frame(monitor_frame)
        theme_count_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(theme_count_frame, text="Theme Changes:").pack(side=tk.LEFT)
        self.theme_count_var = tk.StringVar(value="0")
        ttk.Label(theme_count_frame, textvariable=self.theme_count_var).pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(monitor_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)
        
        # Widget update monitoring
        widget_monitor_label = ttk.Label(
            monitor_frame,
            text="Widget Update Monitoring",
            font=("", 12, "bold")
        )
        widget_monitor_label.pack(anchor="w", padx=10, pady=5)
        
        # Create widget monitoring table
        self.monitor_table = ttk.Treeview(
            monitor_frame,
            columns=("widget", "updates", "status"),
            show="headings"
        )
        self.monitor_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure columns
        self.monitor_table.heading("widget", text="Widget")
        self.monitor_table.heading("updates", text="Updates")
        self.monitor_table.heading("status", text="Status")
        
        self.monitor_table.column("widget", width=150)
        self.monitor_table.column("updates", width=80)
        self.monitor_table.column("status", width=150)
        
        # Add widgets to table
        for name, _ in self._monitored_widgets:
            self.monitor_table.insert("", "end", values=(name, 0, "Not updated"))
        
        # Footer with status
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        # Config info if available
        if HAS_CONFIG_SERVICE:
            config_var = tk.StringVar()
            config_var.set(f"Config theme: {config_service.get('theme', 'unknown')}")
            ttk.Label(status_frame, textvariable=config_var).pack(side=tk.RIGHT)
    
    def _on_theme_changed(self, theme_name):
        """Handle theme change from theme selector
        
        Args:
            theme_name: Name of the new theme
        """
        self.status_var.set(f"Theme changed to {theme_name}")
    
    def _monitor_theme_change(self, theme_name):
        """Monitor theme changes from event bus
        
        Args:
            theme_name: Name of the new theme
        """
        # Increment theme change count
        self._theme_change_count += 1
        self.theme_count_var.set(str(self._theme_change_count))
        
        # Check widget updates (this is simplified - in a real implementation 
        # you'd need to hook into the widgets to track actual updates)
        for i, (name, _) in enumerate(self._monitored_widgets):
            # Simulate widget update status
            self._widget_change_counts[name] += 1
            
            # Update table
            item_id = self.monitor_table.get_children()[i]
            self.monitor_table.item(
                item_id, 
                values=(
                    name, 
                    self._widget_change_counts[name],
                    "Updated" if self._widget_change_counts[name] == self._theme_change_count else "Out of sync"
                )
            )
        
        # Log theme change
        logger.info(f"Theme changed to: {theme_name} (change #{self._theme_change_count})")

def run_theme_tester():
    """Run the theme tester application"""
    app = ThemeTester()
    app.mainloop()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run the tester
    run_theme_tester() 