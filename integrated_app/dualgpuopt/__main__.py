#!/usr/bin/env python3
"""
Main module for the DualGPUOptimizer.
"""
from __future__ import annotations

import argparse
import logging
import pathlib
import os
import sys
import tkinter as tk
from tkinter import ttk
import threading
from typing import Dict, List, Optional, Any

# Import our module components
from dualgpuopt import __version__, MOCK_MODE
from dualgpuopt.logconfig import setup_logging
from dualgpuopt.gui_constants import (
    DARK_BACKGROUND, LIGHT_FOREGROUND, PURPLE_PRIMARY,
    PURPLE_HIGHLIGHT, DEFAULT_FONT, DEFAULT_FONT_SIZE, PAD
)
from dualgpuopt.gpu_info import probe_gpus
from dualgpuopt.telemetry import start_stream, register_middleware, LoggingMiddleware
from dualgpuopt.gui.dashboard import GPUDashboard
from dualgpuopt.gui.optimizer_tab import OptimizerTab
from dualgpuopt.services.state_service import app_state


class MainApplication:
    """Main Application for DualGPUOptimizer."""

    def __init__(self, args: argparse.Namespace) -> None:
        """Initialize the application."""
        self.args = args
        self.logger = logging.getLogger("dualgpuopt.main")
        self.telemetry_queue = None

        # Probe GPUs
        self.gpus = probe_gpus()
        self.logger.info(f"Detected {len(self.gpus)} GPUs")

        # Create the root window
        self.root = tk.Tk()
        self.root.title(f"DualGPUOptimizer v{__version__}")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        self.root.configure(background=DARK_BACKGROUND)

        # Setup style
        self.setup_style()

        # Build UI
        self.build_ui()

        # Start telemetry collection
        self.start_telemetry()

        # Load application state
        self.load_state()

    def setup_style(self) -> None:
        """Set up the application style."""
        style = ttk.Style()

        # Configure common styles
        style.configure("TFrame", background=DARK_BACKGROUND)
        style.configure("TLabel",
                        background=DARK_BACKGROUND,
                        foreground=LIGHT_FOREGROUND,
                        font=(DEFAULT_FONT, DEFAULT_FONT_SIZE))
        style.configure("TButton",
                        background=PURPLE_PRIMARY,
                        foreground=LIGHT_FOREGROUND,
                        padding=5)
        style.configure("TNotebook",
                        background=DARK_BACKGROUND,
                        tabmargins=[2, 5, 2, 0])
        style.configure("TNotebook.Tab",
                        background=DARK_BACKGROUND,
                        foreground=LIGHT_FOREGROUND,
                        padding=[10, 2],
                        font=(DEFAULT_FONT, DEFAULT_FONT_SIZE))
        style.configure("TLabelframe",
                        background=DARK_BACKGROUND,
                        foreground=LIGHT_FOREGROUND)
        style.configure("TLabelframe.Label",
                        background=DARK_BACKGROUND,
                        foreground=PURPLE_PRIMARY,
                        font=(DEFAULT_FONT, DEFAULT_FONT_SIZE))
        style.configure("TEntry",
                        fieldbackground=DARK_BACKGROUND,
                        foreground=LIGHT_FOREGROUND)

        # Map styles for different states
        style.map("TNotebook.Tab",
                  background=[("selected", PURPLE_PRIMARY)],
                  foreground=[("selected", LIGHT_FOREGROUND)])

        style.map("TButton",
                  background=[("active", PURPLE_HIGHLIGHT)],
                  foreground=[("active", LIGHT_FOREGROUND)])

    def build_ui(self) -> None:
        """Build the user interface."""
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create header frame
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, padx=PAD, pady=PAD)

        # Header with title and version
        ttk.Label(
            self.header_frame,
            text=f"DualGPUOptimizer v{__version__}",
            font=(DEFAULT_FONT, DEFAULT_FONT_SIZE + 8, "bold"),
            foreground=PURPLE_HIGHLIGHT
        ).pack(side=tk.LEFT)

        # Mock mode indicator if applicable
        if MOCK_MODE:
            ttk.Label(
                self.header_frame,
                text="MOCK MODE",
                foreground="#FFA726",  # Orange warning color
                font=(DEFAULT_FONT, DEFAULT_FONT_SIZE + 2)
            ).pack(side=tk.RIGHT)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=PAD, pady=PAD)

        # Create dashboard tab
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="Dashboard")

        # Add dashboard component
        self.dashboard = GPUDashboard(self.dashboard_frame)
        self.dashboard.pack(fill=tk.BOTH, expand=True)

        # Create optimizer tab
        self.optimizer_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.optimizer_frame, text="Optimizer")

        # Add optimizer component
        self.optimizer = OptimizerTab(self.optimizer_frame, self.gpus)
        self.optimizer.pack(fill=tk.BOTH, expand=True)

        # Create footer
        self.footer_frame = ttk.Frame(self.main_frame)
        self.footer_frame.pack(fill=tk.X, padx=PAD, pady=PAD)

        # Add save state button
        self.save_button = ttk.Button(
            self.footer_frame,
            text="Save Settings",
            command=self.save_state
        )
        self.save_button.pack(side=tk.LEFT)

        # Add exit button
        self.exit_button = ttk.Button(
            self.footer_frame,
            text="Exit",
            command=self.on_exit
        )
        self.exit_button.pack(side=tk.RIGHT)

    def start_telemetry(self) -> None:
        """Start telemetry collection in a background thread."""
        try:
            # Register logging middleware if verbose mode is enabled
            if self.args.verbose:
                register_middleware(LoggingMiddleware())

            # Start telemetry stream
            self.telemetry_queue = start_stream(interval=1.0)
            self.logger.info("Telemetry stream started")

        except Exception as e:
            self.logger.error(f"Failed to start telemetry: {e}")

    def save_state(self) -> None:
        """Save application state to disk."""
        try:
            app_state.save_to_disk()
            self.logger.info("Application state saved")
        except Exception as e:
            self.logger.error(f"Failed to save application state: {e}")

    def load_state(self) -> None:
        """Load application state from disk."""
        try:
            app_state.load_from_disk()
            self.logger.info("Application state loaded")
        except Exception as e:
            self.logger.error(f"Failed to load application state: {e}")

    def on_exit(self) -> None:
        """Handle application exit."""
        self.logger.info("Application shutting down")
        self.save_state()
        self.root.destroy()

    def run(self) -> None:
        """Run the application."""
        self.logger.info("Starting application")
        self.root.mainloop()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="DualGPUOptimizer - GPU optimization utility")
    parser.add_argument("--mock", action="store_true", help="Use mock GPU data for testing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--version", action="version", version=f"DualGPUOptimizer v{__version__}")
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    # Parse command line arguments
    args = parse_args()

    # Setup MOCK_GPUS environment variable if --mock flag is used
    if args.mock:
        os.environ["DGPUOPT_MOCK_GPUS"] = "1"

    # Setup logging
    log_dir = pathlib.Path.home() / ".dualgpuopt" / "logs"
    log_file = log_dir / "dualgpuopt.log"
    logger = setup_logging(args.verbose, log_file)

    try:
        # Create and run the application
        app = MainApplication(args)
        app.run()
        return 0

    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())