"""
Main application module for the DualGPUOptimizer GUI.
"""
from __future__ import annotations

import logging
import os
import queue
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional

# Import ttkbootstrap for modern UI
try:
    import ttkbootstrap as ttk
    from ttkbootstrap import Style
    from ttkbootstrap.constants import *
    TTKBOOTSTRAP_AVAILABLE = True
except ImportError:
    import tkinter.ttk as ttk
    TTKBOOTSTRAP_AVAILABLE = False

# Legacy theme support as fallback
try:
    from ttkthemes import ThemedTk
    TTKTHEMES_AVAILABLE = True
except ImportError:
    TTKTHEMES_AVAILABLE = False

# Import constants first to avoid circular imports
from dualgpuopt.gui.constants import (
    PAD,
    DEFAULT_CHART_BG,
    DEFAULT_CHART_FG,
    DEFAULT_CHART_HEIGHT,
    DEFAULT_FONT,
    DEFAULT_FONT_SIZE,
    UPDATE_INTERVAL_MS
)

# Define the progressbar thickness here since it's specific to this module
PROGRESSBAR_THICKNESS = 8

from dualgpuopt import gpu_info, telemetry
from dualgpuopt.gui.theme import apply_theme, generate_colors, update_widgets_theme
from dualgpuopt.tray import init_tray

# Import GUI components after constants
from dualgpuopt.gui.dashboard import GpuDashboard
from dualgpuopt.gui.launcher import LauncherTab
from dualgpuopt.gui.optimizer import OptimizerTab
from dualgpuopt.gui.settings import SettingsTab
from dualgpuopt.services.config_service import config_service
from dualgpuopt.services.error_service import error_service

# Import services
from dualgpuopt.services.event_service import event_bus
from dualgpuopt.services.state_service import app_state


class DualGpuApp(ttk.Frame):
    """Main application class for the DualGPUOptimizer."""

    def __init__(self, master: tk.Tk) -> None:
        """
        Initialize the application.

        Args:
            master: The Tk root window
        """
        # Initialize services
        error_service.set_root(master)

        # Load state and config
        app_state.load_from_disk()

        # Register event handlers
        self._register_event_handlers()

        # Convert root window to ThemedTk if available
        if TTKTHEMES_AVAILABLE and not isinstance(master, ThemedTk):
            try:
                # Store attributes from current master
                geometry = master.geometry()
                title = master.title()

                # Create new ThemedTk window
                new_master = ThemedTk(theme=config_service.get("ttk_theme", "equilux"))
                new_master.geometry(geometry)
                new_master.title(title)

                # Replace master
                master.destroy()
                master = new_master

                # Update root in error service
                error_service.set_root(master)
            except Exception as e:
                # Fall back to regular Tk if conversion fails
                error_service.handle_error(e, level="WARNING", title="Theme Error",
                                          context={"operation": "initialize ThemedTk"})

        # Initialize frame
        super().__init__(master)
        self.master = master
        self.logger = logging.getLogger("dualgpuopt.gui.app")
            
        try:
            # Apply theme to root window before creating widgets
            self._apply_theme(master)

            # Use config/state for variables instead of instance variables
            self.model_var = tk.StringVar(value=app_state.get("model_path", ""))
            self.ctx_var = tk.IntVar(value=config_service.get("context_size", 65536))

            # Setup data tracking
            self.tele_q = None
            self.tele_hist = []  # List of GPU load tuples

            # Detect GPUs
            try:
                self.gpus = gpu_info.probe_gpus()
                if len(self.gpus) < 2:
                    self.logger.warning("Fewer than 2 GPUs detected")
                    # Show warning but continue
                    event_bus.publish("gpu_warning", {"message": "Fewer than 2 GPUs detected"})
            except Exception as e:
                # Handle GPU detection errors
                error_service.handle_gpu_error(e, {"operation": "detect_gpus"})
                # Use mock GPUs for now to allow UI to initialize
                os.environ["DGPUOPT_MOCK_GPUS"] = "1"
                self.gpus = gpu_info.probe_gpus()

            # Generate colors for GPU visualization
            self.gpu_colors = generate_colors(len(self.gpus))

            # Initialize UI
            self.init_ui()

            # Setup telemetry
            self.tele_q = telemetry.start_stream(1.0)
            self.after(1000, self._tick_chart)

            # Setup tray
            init_tray(self)

            # Save initial state
            self._save_state()

            # Log successful startup
            self.logger.info("Application initialized successfully")
            event_bus.publish("app_initialized")
        except Exception as err:
            error_service.handle_error(err, level="CRITICAL", title="Initialization Error",
                                      context={"operation": "app_initialization"})

    def _register_event_handlers(self) -> None:
        """Register handlers for application events."""
        # GPU-related events
        event_bus.subscribe("enable_mock_mode", self._enable_mock_mode)
        event_bus.subscribe("gpu_warning", self._handle_gpu_warning)

        # Config and state events
        event_bus.subscribe("config_changed:theme", lambda theme: self._theme_changed(theme))
        event_bus.subscribe("state_changed:model_path", lambda path: self.model_var.set(path))
        event_bus.subscribe("app_exit", self._save_state)

        # Error events for logging
        event_bus.subscribe("error_occurred", self._log_error_event)

    def _log_error_event(self, error_data: Dict[str, Any]) -> None:
        """Log error events from the event bus."""
        # Already logged by error service, just for monitoring
        pass

    def _enable_mock_mode(self, _=None) -> None:
        """Enable mock mode and restart GPU detection."""
        import os

        # Set environment variable for mock mode
        os.environ["DGPUOPT_MOCK_GPUS"] = "1"
        self.logger.info("Mock GPU mode enabled")

        # Clear the current UI
        for widget in self.winfo_children():
            widget.destroy()

        # Try to initialize with mock GPUs
        try:
            self.gpus = gpu_info.probe_gpus()
            self.gpu_colors = generate_colors(len(self.gpus))
            self.init_ui()

            # Setup telemetry again
            self.tele_q = telemetry.start_stream(1.0)
            self.after(1000, self._tick_chart)

            # Notify about mock mode
            event_bus.publish("mock_mode_enabled")
        except Exception as e:
            error_service.handle_error(e, level="CRITICAL", title="Mock Mode Error",
                                     context={"operation": "enable_mock_mode"})
            self.master.destroy()

    def _handle_gpu_warning(self, data: Dict[str, Any]) -> None:
        """Handle GPU warning events."""
        message = data.get("message", "GPU warning")
        self.logger.warning(message)
        # Display in status bar
        if hasattr(self, "status_var"):
            self.status_var.set(f"Warning: {message}")

    def _apply_theme(self, root: tk.Tk) -> None:
        """
        Apply selected theme to the application.

        Args:
            root: The root Tk window
        """
        theme_name = config_service.get("theme", "dark")

        # Apply theme
        self.active_theme = apply_theme(root, theme_name, self.logger)
        self.chart_bg = self.active_theme.get("chart_bg", "#202020")

    def _theme_changed(self, theme_name: str) -> None:
        """
        Handle theme change.

        Args:
            theme_name: New theme name
        """
        # Get ttk theme from config
        ttk_theme = config_service.get("ttk_theme", "")

        # Apply the theme
        self.active_theme = apply_theme(self.master, theme_name, self.logger)

        # Update all widgets
        update_widgets_theme(self, self.active_theme)

        # Update chart background
        self.chart_bg = self.active_theme.get("chart_bg", "#202020")

        # Update the chart canvas background
        if hasattr(self, "dashboard") and hasattr(self.dashboard, "chart_canvas"):
            self.dashboard.chart_canvas.config(bg=self.chart_bg)

        # Publish theme changed event
        event_bus.publish("theme_applied", {"theme": theme_name, "ttk_theme": ttk_theme})

    def _tick_chart(self) -> None:
        """
        Update the chart with new telemetry data.
        
        This is called every second to update the dashboard with fresh data.
        """
        if not self.tele_q:
            self.after(1000, self._tick_chart)
            return

        try:
            # Try to get new telemetry
            telemetry = self.tele_q.get_nowait()

            # Update each chart using the telemetry
            for widget in self.winfo_children():
                if hasattr(widget, "update_telemetry"):
                    widget.update_telemetry(telemetry)

            # Save the telemetry for history
            self.tele_hist.append(telemetry)

            # Limit history to 60 samples
            if len(self.tele_hist) > 60:
                self.tele_hist = self.tele_hist[-60:]

            # Publish telemetry update event
            event_bus.publish("telemetry_updated", telemetry)
        except queue.Empty:
            # No new data, that's okay
            pass
        except Exception as e:
            error_service.handle_error(e, level="WARNING", title="Telemetry Error",
                                     context={"operation": "update_telemetry"})

        # Schedule next update
        self.after(1000, self._tick_chart)

    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Create main frame that fills parent
        self.pack(fill=tk.BOTH, expand=True)

        # Configure row/column weights
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Create notebook widget for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="news")

        # Create dashboard tab
        self.dashboard = GpuDashboard(
            self.notebook,
            self.gpus,
            self.gpu_colors,
            self.chart_bg
        )
        self.notebook.add(self.dashboard, text="Dashboard")

        # Create optimizer tab
        self.optimizer_tab = OptimizerTab(
            self.notebook,
            self.gpus,
            self.model_var,
            self.ctx_var
        )
        self.notebook.add(self.optimizer_tab, text="Optimizer")

        # Create launcher tab
        self.launcher_tab = LauncherTab(
            self.notebook,
            self.gpus,
            self.model_var
        )
        self.notebook.add(self.launcher_tab, text="Launcher")

        # Create settings tab
        self.settings_tab = SettingsTab(
            self.notebook,
            self.gpus,
            config_service
        )
        self.notebook.add(self.settings_tab, text="Settings")

        # Status bar
        status_frame = ttk.Frame(self)
        status_frame.grid(row=1, column=0, sticky="ew")
        status_frame.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor="e")
        status_label.grid(row=0, column=0, sticky="e", padx=8, pady=4)

        # Sync model_var with state
        self.model_var.trace_add("write", self._model_var_changed)

    def _model_var_changed(self, *args) -> None:
        """Handle changes to the model path variable."""
        app_state.set("model_path", self.model_var.get())

    def _save_state(self, *args) -> None:
        """Save application state."""
        # Update state with current values
        app_state.set("model_path", self.model_var.get())

        # Save to disk
        app_state.save_to_disk()
        self.logger.debug("Application state saved")


def run_app(root: tk.Tk) -> None:
    """
    Run the DualGPUOptimizer application.

    Args:
        root: The Tk root window
    """
    app = DualGpuApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root, app))
    root.mainloop()


def on_close(root: tk.Tk, app: DualGpuApp) -> None:
    """
    Handle application close event.

    Args:
        root: The root Tk window
        app: The application instance
    """
    # Publish app_exit event
    event_bus.publish("app_exit")

    # Save state
    app._save_state()

    # Clean up resources
    root.destroy()

if __name__ == "__main__":
    # Create root window
    root = tk.Tk()
    root.title("Dual GPU Optimizer")
    root.geometry("1024x768")
    run_app(root)
