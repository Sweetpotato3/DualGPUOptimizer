"""Main application module for DualGPUOptimizer GUI."""
# LEGACY: This is the Tkinter implementation, which is being phased out in favor of the Qt-based UI.
# Use dualgpuopt.qt.app_window instead for the current implementation.
from __future__ import annotations

import logging
import os
import queue
import sys
import tkinter as tk
from tkinter import messagebox
from typing import Any, Dict

# 3rd-party themes
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    TTKBOOTSTRAP = True
except ImportError:  # Fallback to std ttk
    import tkinter.ttk as ttk  # type: ignore
    TTKBOOTSTRAP = False

try:
    from ttkthemes import ThemedTk
    THEMES = True
except ImportError:
    THEMES = False

# project-internal
from dualgpuopt import VERSION, gpu_info, telemetry
from dualgpuopt.gui.constants import (
    PAD,
    UPDATE_INTERVAL_MS,
    DEFAULT_FONT,
    DEFAULT_FONT_SIZE,
)
from dualgpuopt.gui.dashboard import GpuDashboard
from dualgpuopt.gui.launcher import LauncherTab
from dualgpuopt.gui.optimizer import OptimizerTab
from dualgpuopt.gui.settings import SettingsTab
from dualgpuopt.gui.theme import apply_theme, update_widgets_theme
from dualgpuopt.tray import init_tray
from dualgpuopt.services.config_service import config_service
from dualgpuopt.services.error_service import error_service
from dualgpuopt.services.event_service import event_bus
from dualgpuopt.services.state_service import app_state

# Define the progressbar thickness here since it's specific to this module
PROGRESSBAR_THICKNESS = 8


class DualGpuApp(ttk.Frame):
    """Main GUI frame."""

    def __init__(self, master: tk.Tk | None = None, *, theme: str | None = None,
                 mock_mode: bool = False) -> None:
        """Initialize the application GUI and services.
        
        Args:
            master: Optional root window. If None, one will be created.
            theme: Optional theme name to use.
            mock_mode: Whether to use mock GPU data.
        """
        # 1. Set up logging first to ensure it's available throughout initialization
        self.log = logging.getLogger("dualgpuopt.gui.app")
        self.log.debug("GUI init (mock=%s, theme=%s)", mock_mode, theme)

        # 2. Root window bootstrap
        root = master or self._create_root(theme)
        super().__init__(root)
        self.pack(fill="both", expand=True)

        # 3. Service state
        self.mock_mode = mock_mode
        self.msg_q: queue.Queue[tuple[str, Dict[str, Any]]] = queue.Queue()

        # 4. Init backend services
        self._init_services()

        # 5. GUI widgets
        self._build_ui()

        # 6. Start periodic tasks
        root.after(100, self._pump_queue)
        root.after(UPDATE_INTERVAL_MS, self._tick_telemetry)

        # 7. Tray
        self.tray_icon = init_tray(root)
        
        self.log.info("Application initialization complete")

    def _create_root(self, theme: str | None) -> tk.Tk:
        """Create and configure the root window with appropriate theme support.
        
        Args:
            theme: Optional theme name to use.
            
        Returns:
            Configured root window.
        """
        # Use ttkbootstrap if available
        if TTKBOOTSTRAP:
            self.log.debug("Using ttkbootstrap for theming")
            theme = theme or config_service.get("ui.theme", "darkly")
            root = ttk.Window(
                title="Dual GPU Optimizer",
                themename=theme,
                size=(1024, 768),
                position=(100, 100),
                minsize=(800, 600)
            )
        # Fall back to ttkthemes if available
        elif THEMES:
            self.log.debug("Using ttkthemes for theming")
            theme = theme or config_service.get("ui.theme", "black")
            root = ThemedTk(theme=theme)
            root.title("Dual GPU Optimizer")
            root.geometry("1024x768+100+100")
            root.minsize(800, 600)
        # Last resort: standard Tk with manual styling
        else:
            self.log.debug("Using basic Tk with manual styling")
            root = tk.Tk()
            root.title("Dual GPU Optimizer")
            root.geometry("1024x768+100+100")
            root.minsize(800, 600)

            # Apply manual dark theme
            apply_theme(root)

        # Increase base font size
        default_font = (DEFAULT_FONT, DEFAULT_FONT_SIZE) if sys.platform == "win32" else ("Helvetica", DEFAULT_FONT_SIZE)
        root.option_add("*Font", default_font)

        # Set up window icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "gpu_icon.ico")
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except Exception as e:
            self.log.warning(f"Failed to set window icon: {e}")

        # Set up close handler
        root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        return root

    def _init_services(self) -> None:
        """Initialize application services."""
        # Config / state
        self.cfg = config_service
        app_state.load_from_disk()

        # Error handling
        error_service.set_root(self.winfo_toplevel())

        # GPU & telemetry
        try:
            self.gpu_info = gpu_info.GpuInfo(mock_mode=self.mock_mode)
        except Exception as exc:  # fallback to mock
            self.log.warning("GPU probe failed – switching to mock mode: %s", exc, exc_info=True)
            self.gpu_info = gpu_info.GpuInfo(mock_mode=True)

        self.telemetry = telemetry.GpuTelemetry(mock_mode=self.mock_mode)

        # Subscribe to events
        self._register_event_handlers()

    def _register_event_handlers(self) -> None:
        """Register handlers for application events."""
        # GPU telemetry update event
        event_bus.subscribe("gpu.telemetry.updated", self._handle_telemetry_update)

        # GPU error events
        event_bus.subscribe("gpu.error", self._handle_gpu_error)

        # Config change events
        event_bus.subscribe("config.changed", self._handle_config_change)

        # Theme change events
        event_bus.subscribe("ui.theme.changed", self._handle_theme_change)

        # Command events
        event_bus.subscribe("command.generated", self._handle_command_generated)
        event_bus.subscribe("command.executed", self._handle_command_executed)
        event_bus.subscribe("command.error", self._handle_command_error)

        # Log events for status bar
        event_bus.subscribe("log.info", self._handle_log_event)
        event_bus.subscribe("log.warning", self._handle_log_event)
        event_bus.subscribe("log.error", self._handle_log_event)
        
        # Mock mode events
        event_bus.subscribe("enable_mock_mode", self._enable_mock_mode)
        event_bus.subscribe("gpu_warning", self._handle_gpu_warning)

    def _build_ui(self) -> None:
        """Initialize the user interface components."""
        # Create main container frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=PAD, pady=PAD)

        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create GPU Dashboard tab
        dashboard_frame = ttk.Frame(self.notebook)
        self.dashboard = GpuDashboard(dashboard_frame, self.gpu_info, self.telemetry)
        self.notebook.add(dashboard_frame, text="GPU Dashboard")

        # Create Optimizer tab
        optimizer_frame = ttk.Frame(self.notebook)
        self.optimizer_tab = OptimizerTab(optimizer_frame, self.gpu_info)
        self.notebook.add(optimizer_frame, text="Optimizer")

        # Create Launcher tab
        launcher_frame = ttk.Frame(self.notebook)
        self.launcher_tab = LauncherTab(launcher_frame, self.gpu_info)
        self.notebook.add(launcher_frame, text="Launcher")

        # Create Settings tab
        settings_frame = ttk.Frame(self.notebook)
        self.settings_tab = SettingsTab(settings_frame)
        self.notebook.add(settings_frame, text="Settings")

        # Create status bar
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(PAD, 0))

        # Add status variable
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")

        # Create status label
        self.status_label = ttk.Label(
            self.status_frame,
            textvariable=self.status_var,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, side=tk.LEFT)

        # Create version label
        self.version_label = ttk.Label(
            self.status_frame,
            text=f"v{VERSION}",
            anchor=tk.E
        )
        self.version_label.pack(side=tk.RIGHT)

    def _tick_telemetry(self) -> None:
        """Update GPU telemetry data periodically."""
        try:
            data = self.telemetry.get_data()
            event_bus.publish("gpu.telemetry.updated", data)
        except Exception as e:
            self.log.error(f"Error updating telemetry: {e}", exc_info=True)
        finally:
            # Always schedule next update
            self.after(UPDATE_INTERVAL_MS, self._tick_telemetry)

    def _pump_queue(self) -> None:
        """Process pending messages in the queue."""
        try:
            # Process all current messages in the queue
            while True:
                kind, payload = self.msg_q.get_nowait()
                
                if kind == "telemetry" and hasattr(self, "dashboard"):
                    self.dashboard.update_telemetry(payload)
                elif kind == "config_change" and hasattr(self, "settings_tab"):
                    self.settings_tab.refresh_config()
                elif kind == "command_generated" and hasattr(self, "launcher_tab"):
                    self.launcher_tab.update_command(payload.get("command", ""))
                elif kind == "command_executed" and hasattr(self, "launcher_tab"):
                    self.launcher_tab.update_execution_status(payload)
                elif kind == "log":
                    level = payload.get("level", "INFO")
                    message = payload.get("message", "")
                    if level in ["INFO", "WARNING", "ERROR"]:
                        self.status_var.set(message[:160] + ('...' if len(message) > 160 else ''))
                
                self.msg_q.task_done()
        except queue.Empty:
            # No more messages
            pass
        except Exception as e:
            self.log.error(f"Error processing message queue: {e}", exc_info=True)
        
        # Schedule next check
        self.after(100, self._pump_queue)

    def _enable_mock_mode(self, _=None) -> None:
        """Enable mock mode and restart GPU detection."""
        os.environ["DGPUOPT_MOCK_GPUS"] = "1"
        self.log.info("Mock GPU mode enabled")

        # Try to initialize with mock GPUs
        try:
            self.gpu_info = gpu_info.GpuInfo(mock_mode=True)
            self.telemetry = telemetry.GpuTelemetry(mock_mode=True)
            
            # Notify about mock mode
            event_bus.publish("mock_mode_enabled")
        except Exception as e:
            error_service.handle_error(e, level="CRITICAL", title="Mock Mode Error",
                                     context={"operation": "enable_mock_mode"})

    def _handle_gpu_warning(self, data: Dict[str, Any]) -> None:
        """Handle GPU warning events."""
        message = data.get("message", "GPU warning")
        self.log.warning(message)
        
        # Display in status bar
        if hasattr(self, "status_var"):
            self.status_var.set(f"Warning: {message}")

    def _handle_telemetry_update(self, data: Dict[str, Any]) -> None:
        """Handle GPU telemetry update event."""
        # Push to message queue for thread-safe UI updates
        self.msg_q.put(("telemetry", data))

    def _handle_gpu_error(self, error_data: Dict[str, Any]) -> None:
        """Handle GPU error event."""
        # Push to message queue for thread-safe UI updates
        self.msg_q.put(("gpu_error", error_data))

        # Log the error
        self.log.error(f"GPU error: {error_data.get('message', 'Unknown GPU error')}")

        # Show error dialog if critical
        if error_data.get("critical", False):
            messagebox.showerror(
                "GPU Error",
                f"Critical GPU error: {error_data.get('message', 'Unknown error')}"
            )

    def _handle_config_change(self, config_data: Dict[str, Any]) -> None:
        """Handle configuration change event."""
        # Push to message queue for thread-safe UI updates
        self.msg_q.put(("config_change", config_data))

    def _handle_theme_change(self, theme_data: Dict[str, Any]) -> None:
        """Handle theme change event."""
        new_theme = theme_data.get("theme")
        if not new_theme:
            return
            
        # Apply theme in-place
        apply_theme(self.winfo_toplevel(), new_theme, self.log)
        update_widgets_theme(self, {})
        
        # Save the theme in config
        config_service.set("ui.theme", new_theme)
        config_service.save()
        
        # Publish theme applied event
        event_bus.publish("theme_applied", {"theme": new_theme})

    def _handle_command_generated(self, command_data: Dict[str, Any]) -> None:
        """Handle command generation event."""
        # Push to message queue for thread-safe UI updates
        self.msg_q.put(("command_generated", command_data))

    def _handle_command_executed(self, execution_data: Dict[str, Any]) -> None:
        """Handle command execution event."""
        # Push to message queue for thread-safe UI updates
        self.msg_q.put(("command_executed", execution_data))

    def _handle_command_error(self, error_data: Dict[str, Any]) -> None:
        """Handle command execution error event."""
        # Push to message queue for thread-safe UI updates
        self.msg_q.put(("command_error", error_data))

        # Log the error
        self.log.error(f"Command error: {error_data.get('message', 'Unknown command error')}")

        # Show error dialog
        messagebox.showerror(
            "Command Error",
            f"Error executing command: {error_data.get('message', 'Unknown error')}"
        )

    def _handle_log_event(self, log_data: Dict[str, Any]) -> None:
        """Handle log event for status updates."""
        # Push to message queue for thread-safe UI updates
        self.msg_q.put(("log", log_data))

    def _on_close(self) -> None:
        """Handle application close event."""
        # Ask for confirmation
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # Save application state
            self.log.info("Saving application state")
            app_state.save()

            # Save configuration
            self.log.info("Saving configuration")
            config_service.save()

            # Shut down telemetry
            self.log.info("Shutting down telemetry")
            if hasattr(self, "telemetry") and hasattr(self.telemetry, "shutdown"):
                self.telemetry.shutdown()

            # Publish app_exit event
            event_bus.publish("app_exit")

            # Destroy root window
            root = self.winfo_toplevel()
            if root:
                root.destroy()

            self.log.info("Application closed")


def main() -> None:
    """Entry point when module is run directly."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    DualGpuApp().winfo_toplevel().mainloop()


if __name__ == "__main__":
    main()
