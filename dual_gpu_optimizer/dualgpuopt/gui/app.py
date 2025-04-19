"""
Main application module for the DualGPUOptimizer GUI.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import queue
import sys
import os
from typing import Dict, List, Optional, Any

# Import ttkbootstrap for modern UI
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    from ttkbootstrap import Style
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
    DEFAULT_CHART_HEIGHT,
    DEFAULT_CHART_BG,
    DEFAULT_CHART_FG,
    GPU_COLORS,
    DEFAULT_FONT,
    DEFAULT_FONT_SIZE,
    UPDATE_INTERVAL_MS
)

# Define the progressbar thickness here since it's specific to this module
PROGRESSBAR_THICKNESS = 8

from dualgpuopt import gpu_info, telemetry
from dualgpuopt.tray import init_tray
from dualgpuopt.gui.theme import apply_theme, update_widgets_theme, generate_colors

# Import services
from dualgpuopt.services.event_service import event_bus
from dualgpuopt.services.state_service import app_state
from dualgpuopt.services.config_service import config_service
from dualgpuopt.services.error_service import error_service

# Import GUI components after constants
from dualgpuopt.gui.dashboard import GpuDashboard
from dualgpuopt.gui.settings import SettingsTab
from dualgpuopt.gui.optimizer import OptimizerTab
from dualgpuopt.gui.launcher import LauncherTab

class DualGpuApp:
    """Main application class for the Dual GPU Optimizer GUI."""
    
    def __init__(self, root: tk.Tk = None, theme: str = None, mock_mode: bool = False):
        """Initialize the application GUI and services."""
        # Set up logging first to ensure it's available throughout initialization
        self.setup_logger()
        self.logger.info("Starting DualGPUOptimizer application")
        
        # Store initialization parameters
        self.root = root
        self.mock_mode = mock_mode
        self.message_queue = queue.Queue()
        
        # Load app state early
        self.logger.debug("Loading application state")
        self.state = app_state
        
        # Initialize config service
        self.logger.debug("Loading configuration")
        self.config = config_service
        
        # Register error handler early
        error_service.register_handler(self.handle_error)
        
        # Initialize GPU information
        self.logger.debug("Initializing GPU information service")
        self.gpu_info = gpu_info.GpuInfo(mock_mode=mock_mode)
        
        # Initialize telemetry service
        self.logger.debug("Initializing telemetry service")
        self.telemetry = telemetry.GpuTelemetry(mock_mode=mock_mode)
        
        # Check if root window provided, otherwise create one
        if self.root is None:
            self.create_root_window(theme)
        else:
            self.setup_root_window(theme)
            
        # Register event handlers for UI updates
        self._register_event_handlers()
        
        # Initialize UI components
        self.init_ui()
        
        # Set up style for themed widgets
        self._setup_style()
        
        # Prepare for tray icon if available
        self.tray_icon = None
        if hasattr(self, 'root') and self.root:
            self.tray_icon = init_tray(self.root)
            
        self.logger.info("Application initialization complete")
            
    def setup_logger(self):
        """Set up application logger."""
        self.logger = logging.getLogger("dualgpuopt.gui")
        
    def create_root_window(self, theme: str = None):
        """Create and configure the root window with appropriate theme support."""
        # Use ttkbootstrap if available
        if TTKBOOTSTRAP_AVAILABLE:
            self.logger.debug("Using ttkbootstrap for theming")
            theme = theme or self.config.get("ui.theme", "darkly")
            self.root = ttk.Window(
                title="Dual GPU Optimizer", 
                themename=theme, 
                size=(1024, 768),
                position=(100, 100),
                minsize=(800, 600)
            )
        # Fall back to ttkthemes if available
        elif TTKTHEMES_AVAILABLE:
            self.logger.debug("Using ttkthemes for theming")
            theme = theme or self.config.get("ui.theme", "black")
            self.root = ThemedTk(theme=theme)
            self.root.title("Dual GPU Optimizer")
            self.root.geometry("1024x768+100+100")
            self.root.minsize(800, 600)
        # Last resort: standard Tk with manual styling
        else:
            self.logger.debug("Using basic Tk with manual styling")
            self.root = tk.Tk()
            self.root.title("Dual GPU Optimizer")
            self.root.geometry("1024x768+100+100")
            self.root.minsize(800, 600)
            
            # Apply manual dark theme
            apply_theme(self.root)
            
        # Increase base font size to Segoe UI 11
        default_font = (DEFAULT_FONT, DEFAULT_FONT_SIZE) if sys.platform == "win32" else ("Helvetica", DEFAULT_FONT_SIZE)
        self.root.option_add("*Font", default_font)
            
        # Set up window icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "gpu_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            self.logger.warning(f"Failed to set window icon: {e}")
            
        # Set up close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_root_window(self, theme: str = None):
        """Configure an existing root window."""
        # Set window title and size
        self.root.title("Dual GPU Optimizer")
        self.root.geometry("1024x768+100+100")
        self.root.minsize(800, 600)
        
        # Apply theme if using standard Tk
        if not TTKBOOTSTRAP_AVAILABLE and not TTKTHEMES_AVAILABLE:
            apply_theme(self.root)
            
        # Increase font size
        default_font = (DEFAULT_FONT, DEFAULT_FONT_SIZE) if sys.platform == "win32" else ("Helvetica", DEFAULT_FONT_SIZE)
        self.root.option_add("*Font", default_font)
            
        # Set up window icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "gpu_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            self.logger.warning(f"Failed to set window icon: {e}")
            
        # Set up close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def _setup_style(self):
        """Configure ttk styles for the application."""
        # Get ttk style object
        if TTKBOOTSTRAP_AVAILABLE:
            style = ttk.Style()
        else:
            style = ttk.Style(self.root)
            
        # Configure progressbar style
        style.configure(
            "GPU.Horizontal.TProgressbar", 
            thickness=PROGRESSBAR_THICKNESS,
            troughcolor=DEFAULT_CHART_BG,
            background="#00FF00"
        )
        
        # Configure blue progressbar variant
        style.configure(
            "GPUBlue.Horizontal.TProgressbar", 
            thickness=PROGRESSBAR_THICKNESS,
            troughcolor=DEFAULT_CHART_BG,
            background="#0078D7"
        )
        
        # Configure red progressbar variant
        style.configure(
            "GPURed.Horizontal.TProgressbar", 
            thickness=PROGRESSBAR_THICKNESS,
            troughcolor=DEFAULT_CHART_BG,
            background="#E81123"
        )
        
        # Configure orange progressbar variant
        style.configure(
            "GPUOrange.Horizontal.TProgressbar", 
            thickness=PROGRESSBAR_THICKNESS,
            troughcolor=DEFAULT_CHART_BG,
            background="#FF8C00"
        )
        
        # Configure notebook style
        style.configure(
            "TNotebook", 
            background=DEFAULT_CHART_BG if not TTKBOOTSTRAP_AVAILABLE else None
        )
        style.configure(
            "TNotebook.Tab", 
            padding=[12, 6],
            font=(DEFAULT_FONT, DEFAULT_FONT_SIZE)
        )
        
        # Configure frame style
        style.configure(
            "TFrame", 
            background=DEFAULT_CHART_BG if not TTKBOOTSTRAP_AVAILABLE else None
        )
        
        # Configure label style
        style.configure(
            "TLabel", 
            background=DEFAULT_CHART_BG if not TTKBOOTSTRAP_AVAILABLE else None,
            foreground=DEFAULT_CHART_FG if not TTKBOOTSTRAP_AVAILABLE else None
        )
    
    def _register_event_handlers(self):
        """Register event handlers for various application events."""
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
    
    def _handle_telemetry_update(self, data: Dict[str, Any]):
        """Handle GPU telemetry update event."""
        # Push to message queue for thread-safe UI updates
        self.message_queue.put(("telemetry", data))
    
    def _handle_gpu_error(self, error_data: Dict[str, Any]):
        """Handle GPU error event."""
        # Push to message queue for thread-safe UI updates
        self.message_queue.put(("gpu_error", error_data))
        
        # Log the error
        self.logger.error(f"GPU error: {error_data.get('message', 'Unknown GPU error')}")
        
        # Show error dialog if critical
        if error_data.get("critical", False):
            messagebox.showerror(
                "GPU Error", 
                f"Critical GPU error: {error_data.get('message', 'Unknown error')}"
            )
    
    def _handle_config_change(self, config_data: Dict[str, Any]):
        """Handle configuration change event."""
        # Push to message queue for thread-safe UI updates
        self.message_queue.put(("config_change", config_data))
    
    def _handle_theme_change(self, theme_data: Dict[str, Any]):
        """Handle theme change event."""
        # Get new theme name
        new_theme = theme_data.get("theme")
        if not new_theme:
            return
            
        # Update configuration
        self.config.set("ui.theme", new_theme)
        self.config.save()
        
        # Inform user about restart requirement
        messagebox.showinfo(
            "Theme Changed", 
            "The theme has been changed. Please restart the application for the changes to take effect."
        )
    
    def _handle_command_generated(self, command_data: Dict[str, Any]):
        """Handle command generation event."""
        # Push to message queue for thread-safe UI updates
        self.message_queue.put(("command_generated", command_data))
    
    def _handle_command_executed(self, execution_data: Dict[str, Any]):
        """Handle command execution event."""
        # Push to message queue for thread-safe UI updates
        self.message_queue.put(("command_executed", execution_data))
    
    def _handle_command_error(self, error_data: Dict[str, Any]):
        """Handle command execution error event."""
        # Push to message queue for thread-safe UI updates
        self.message_queue.put(("command_error", error_data))
        
        # Log the error
        self.logger.error(f"Command error: {error_data.get('message', 'Unknown command error')}")
        
        # Show error dialog
        messagebox.showerror(
            "Command Error", 
            f"Error executing command: {error_data.get('message', 'Unknown error')}"
        )
    
    def _handle_log_event(self, log_data: Dict[str, Any]):
        """Handle log event for status updates."""
        # Push to message queue for thread-safe UI updates
        self.message_queue.put(("log", log_data))
        
        # Update status bar if available
        if hasattr(self, "status_var") and self.status_var:
            level = log_data.get("level", "INFO")
            message = log_data.get("message", "")
            
            # Only show INFO level or higher in status bar
            if level in ["INFO", "WARNING", "ERROR"]:
                self.status_var.set(message)
    
    def handle_error(self, error: Exception, context: str = None):
        """Global error handler for unexpected errors."""
        # Log the error
        if context:
            self.logger.error(f"Error in {context}: {str(error)}", exc_info=error)
        else:
            self.logger.error(f"Unhandled error: {str(error)}", exc_info=error)
            
        # Show error dialog for unexpected errors
        if self.root and self.root.winfo_exists():
            error_msg = f"{str(error)}\n\nSee log for details."
            if context:
                messagebox.showerror(f"Error in {context}", error_msg)
            else:
                messagebox.showerror("Unhandled Error", error_msg)
    
    def process_message_queue(self):
        """Process pending messages in the queue."""
        try:
            # Process all current messages in the queue
            while True:
                message = self.message_queue.get_nowait()
                message_type, data = message
                
                # Dispatch to appropriate handler based on message type
                if message_type == "telemetry" and hasattr(self, "dashboard"):
                    self.dashboard.update_telemetry(data)
                elif message_type == "config_change" and hasattr(self, "settings_tab"):
                    self.settings_tab.refresh_config()
                elif message_type == "command_generated" and hasattr(self, "launcher_tab"):
                    self.launcher_tab.update_command(data.get("command", ""))
                elif message_type == "command_executed" and hasattr(self, "launcher_tab"):
                    self.launcher_tab.update_execution_status(data)
                    
                # Mark message as processed
                self.message_queue.task_done()
                
        except queue.Empty:
            # No more messages, schedule next check
            pass
        
        # Schedule next check
        if self.root and self.root.winfo_exists():
            self.root.after(100, self.process_message_queue)
    
    def init_ui(self):
        """Initialize the user interface components."""
        # Create main container frame
        self.main_frame = ttk.Frame(self.root)
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
        # Import version here to avoid circular import
        from dualgpuopt import VERSION
        self.version_label = ttk.Label(
            self.status_frame,
            text=f"v{VERSION}",
            anchor=tk.E
        )
        self.version_label.pack(side=tk.RIGHT)
        
        # Start message queue processing
        self.process_message_queue()
        
        # Start telemetry updates
        self.update_telemetry()
    
    def update_telemetry(self):
        """Update GPU telemetry data periodically."""
        try:
            # Fetch new telemetry data
            self.telemetry.update()
            
            # Publish telemetry update event
            event_bus.publish("gpu.telemetry.updated", self.telemetry.get_data())
        except Exception as e:
            self.logger.error(f"Error updating telemetry: {e}", exc_info=e)
        
        # Schedule next update
        if self.root and self.root.winfo_exists():
            self.root.after(UPDATE_INTERVAL_MS, self.update_telemetry)
    
    def run(self):
        """Run the application main loop."""
        if self.root:
            try:
                self.root.mainloop()
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=e)
        else:
            self.logger.error("Cannot run application: root window not initialized")
    
    def on_close(self):
        """Handle application close event."""
        # Ask for confirmation
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # Save application state
            self.logger.info("Saving application state")
            app_state.save()
            
            # Save configuration
            self.logger.info("Saving configuration")
            self.config.save()
            
            # Shut down telemetry
            self.logger.info("Shutting down telemetry")
            self.telemetry.shutdown()
            
            # Destroy root window
            if self.root:
                self.root.destroy()
                
            self.logger.info("Application closed")
            
# Application entry point for direct execution
def main():
    """Entry point when module is run directly."""
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create and run application
    app = DualGpuApp()
    app.run()

if __name__ == "__main__":
    main() 