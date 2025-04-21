#!/usr/bin/env python3
"""
Simple standalone app for DualGPUOptimizer.
This is a minimal version that just displays a window with information from constants.py.
"""
import os
import sys
import logging
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("SimpleApp")

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# Import the constants directly from the standalone file
from gui_constants import (
    PAD,
    PURPLE_PRIMARY,
    PURPLE_HIGHLIGHT,
    BLUE_ACCENT,
    PINK_ACCENT,
    CYAN_ACCENT,
    ORANGE_ACCENT,
    DARK_BACKGROUND,
    LIGHT_FOREGROUND,
    DEFAULT_FONT,
    DEFAULT_FONT_SIZE,
    GPU_COLORS
)

class SimpleApp:
    """A simple app that displays constants values."""

    def __init__(self, root=None):
        """Initialize the app."""
        # Create root window if not provided
        if root is None:
            self.root = tk.Tk()
            self.root.title("DualGPUOptimizer - Simple App")
            self.root.geometry("800x600")
            self.root.configure(bg=DARK_BACKGROUND)
        else:
            self.root = root

        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=PAD, pady=PAD)

        # Set up style
        self.style = ttk.Style()
        self.style.configure('TFrame', background=DARK_BACKGROUND)
        self.style.configure(
                             'TLabel',
                             background=DARK_BACKGROUND,
                             foreground=LIGHT_FOREGROUND)
        )        self.style.configure(
                             'TButton',
                             background=PURPLE_PRIMARY,
                             foreground=LIGHT_FOREGROUND)
        )
        # Create header
        self.header_label = ttk.Label(
            self.main_frame,
            text="DualGPUOptimizer - GPU Mock Mode",
            font=(DEFAULT_FONT, DEFAULT_FONT_SIZE + 8, "bold"),
            foreground=PURPLE_HIGHLIGHT
        )
        self.header_label.pack(pady=(PAD*2, PAD*4))

        # Create color display
        self.create_color_display()

        # Create mock GPUs display
        self.create_mock_gpu_display()

        # Add exit button
        self.exit_button = ttk.Button(
            self.main_frame,
            text="Exit",
            command=self.root.destroy
        )
        self.exit_button.pack(pady=PAD*2)

    def create_color_display(self):
        """Create a display of the theme colors."""
        # Create frame for colors
        color_frame = ttk.Frame(self.main_frame)
        color_frame.pack(fill=tk.X, padx=PAD, pady=PAD)

        # Add title
        ttk.Label(
            color_frame,
            text="Theme Colors",
            font=(DEFAULT_FONT, DEFAULT_FONT_SIZE + 2),
            foreground=LIGHT_FOREGROUND
        ).pack(anchor=tk.W, pady=PAD)

        # Add color swatches
        colors = [
            ("Primary Purple", PURPLE_PRIMARY),
            ("Highlight Purple", PURPLE_HIGHLIGHT),
            ("Blue Accent", BLUE_ACCENT),
            ("Pink Accent", PINK_ACCENT),
            ("Cyan Accent", CYAN_ACCENT),
            ("Orange Accent", ORANGE_ACCENT)
        ]

        for name, color in colors:
            swatch_frame = ttk.Frame(color_frame)
            swatch_frame.pack(fill=tk.X, pady=2)

            # Create colored rectangle
            color_rect = tk.Canvas(
                swatch_frame,
                width=30,
                height=20,
                bg=color,
                highlightthickness=0
            )
            color_rect.pack(side=tk.LEFT, padx=(PAD, 5))

            # Add label
            ttk.Label(
                swatch_frame,
                text=f"{name} ({color})",
                foreground=LIGHT_FOREGROUND
            ).pack(side=tk.LEFT)

    def create_mock_gpu_display(self):
        """Create a display of mock GPU data."""
        # Create frame for mock GPUs
        gpu_frame = ttk.Frame(self.main_frame)
        gpu_frame.pack(fill=tk.X, padx=PAD, pady=PAD)

        # Add title
        ttk.Label(
            gpu_frame,
            text="Mock GPU Information",
            font=(DEFAULT_FONT, DEFAULT_FONT_SIZE + 2),
            foreground=LIGHT_FOREGROUND
        ).pack(anchor=tk.W, pady=PAD)

        # Add mock GPU data
        mock_gpus = [
            {
                "index": 0,
                "name": "NVIDIA GeForce RTX 4090",
                "memory": "24 GB",
                "color": GPU_COLORS[0]
            },
            {
                "index": 1,
                "name": "NVIDIA GeForce RTX 4080",
                "memory": "16 GB",
                "color": GPU_COLORS[1]
            }
        ]

        for gpu in mock_gpus:
            gpu_card = ttk.Frame(gpu_frame)
            gpu_card.pack(fill=tk.X, pady=5)

            # Create GPU indicator
            indicator = tk.Canvas(
                gpu_card,
                width=10,
                height=40,
                bg=gpu["color"],
                highlightthickness=0
            )
            indicator.pack(side=tk.LEFT, padx=(0, 10))

            # Add GPU info
            info_frame = ttk.Frame(gpu_card)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

            ttk.Label(
                info_frame,
                text=f"GPU {gpu['index']}: {gpu['name']}",
                font=(DEFAULT_FONT, DEFAULT_FONT_SIZE + 2, "bold"),
                foreground=LIGHT_FOREGROUND
            ).pack(anchor=tk.W)

            ttk.Label(
                info_frame,
                text=f"Memory: {gpu['memory']} | Status: Mock Mode",
                foreground=LIGHT_FOREGROUND
            ).pack(anchor=tk.W)

    def run(self):
        """Run the application."""
        self.root.mainloop()

def create_simple_app():
    """Create a simple application to test GUI functionality"""

    # Initialize the root window
    root = tk.Tk()
    root.title("Simple DualGPUOptimizer")
    root.geometry("800x600")

    # Try to apply theme
    try:
        from dualgpuopt.gui.theme import apply_theme
        apply_theme(root)
        logger.info("Applied theme successfully")
    except Exception as e:
        logger.error(f"Error applying theme: {e}")

    # Create main frame
    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Create a notebook with tabs
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Add dashboard tab
    dashboard_tab = ttk.Frame(notebook)
    notebook.add(dashboard_tab, text="Dashboard")

    # Add content to dashboard tab
    dashboard_label = ttk.Label(
                                dashboard_tab,
                                text="Dashboard Tab Content",
                                font=("TkDefaultFont",
                                14))
    )    dashboard_label.pack(pady=20)

    # Add GPU info frame
    gpu_frame = ttk.LabelFrame(dashboard_tab, text="GPU Information")
    gpu_frame.pack(pady=10, padx=10, fill=tk.X)

    # Add some dummy GPU info
    gpu0_label = ttk.Label(gpu_frame, text="GPU 0: NVIDIA GeForce RTX 5070 Ti")
    gpu0_label.pack(pady=5, padx=10, anchor=tk.W)

    gpu1_label = ttk.Label(gpu_frame, text="GPU 1: NVIDIA GeForce RTX 4060 Ti")
    gpu1_label.pack(pady=5, padx=10, anchor=tk.W)

    # Add optimizer tab
    optimizer_tab = ttk.Frame(notebook)
    notebook.add(optimizer_tab, text="Optimizer")

    # Add content to optimizer tab
    optimizer_label = ttk.Label(
                                optimizer_tab,
                                text="Optimizer Tab Content",
                                font=("TkDefaultFont",
                                14))
    )    optimizer_label.pack(pady=20)

    # Add some controls
    controls_frame = ttk.Frame(optimizer_tab)
    controls_frame.pack(pady=10, fill=tk.X)

    ttk.Label(
              controls_frame,
              text="Context Size:").grid(row=0,
              column=0,
              padx=5,
              pady=5,
              sticky=tk.W)
    )    ttk.Entry(controls_frame).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

    ttk.Label(
              controls_frame,
              text="GPU Split:").grid(row=1,
              column=0,
              padx=5,
              pady=5,
              sticky=tk.W)
    )    ttk.Entry(controls_frame).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

    ttk.Button(
               controls_frame,
               text="Calculate").grid(row=2,
               column=0,
               columnspan=2,
               padx=5,
               pady=10)
    )
    # Add launcher tab
    launcher_tab = ttk.Frame(notebook)
    notebook.add(launcher_tab, text="Launcher")

    # Add content to launcher tab
    launcher_label = ttk.Label(
                               launcher_tab,
                               text="Launcher Tab Content",
                               font=("TkDefaultFont",
                               14))
    )    launcher_label.pack(pady=20)

    # Add launch controls
    launch_frame = ttk.Frame(launcher_tab)
    launch_frame.pack(pady=10, fill=tk.X)

    ttk.Label(
              launch_frame,
              text="Model Path:").grid(row=0,
              column=0,
              padx=5,
              pady=5,
              sticky=tk.W)
    )    ttk.Entry(launch_frame).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

    ttk.Label(
              launch_frame,
              text="Framework:").grid(row=1,
              column=0,
              padx=5,
              pady=5,
              sticky=tk.W)
    )    ttk.Combobox(
                 launch_frame,
                 values=["llama.cpp",
                 "vLLM"]).grid(row=1,
                 column=1,
                 padx=5,
                 pady=5,
                 sticky=tk.W)
    )
    ttk.Button(
               launch_frame,
               text="Launch Model").grid(row=2,
               column=0,
               columnspan=2,
               padx=5,
               pady=10)
    )
    # Create status bar
    status_frame = ttk.Frame(main_frame, relief="sunken", borderwidth=1)
    status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)

    status_label = ttk.Label(status_frame, text="Ready")
    status_label.pack(side=tk.LEFT, padx=10)

    version_label = ttk.Label(status_frame, text="v0.2.0")
    version_label.pack(side=tk.RIGHT, padx=10)

    # Run the application
    logger.info("Starting simple application")
    root.mainloop()

def main():
    """Main entry point."""
    # Set environment variable for mock GPU mode
    os.environ["DGPUOPT_MOCK_GPUS"] = "1"

    # Create and run the app
    app = SimpleApp()
    app.run()

    return 0

if __name__ == "__main__":
    sys.exit(main())