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
    UPDATE_INTERVAL_MS,
    # New purple theme colors
    PURPLE_PRIMARY,
    PURPLE_HIGHLIGHT,
    BLUE_ACCENT,
    PINK_ACCENT,
    CYAN_ACCENT,
    ORANGE_ACCENT,
    DARK_BACKGROUND,
    LIGHT_FOREGROUND,
    WARNING_COLOR
)

# Define the progressbar thickness here since it's specific to this module
PROGRESSBAR_THICKNESS = 8

from dualgpuopt import gpu_info, telemetry, VERSION
from dualgpuopt.tray import init_tray

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
            theme = theme or self.config.get("ui.theme", "vapor")
            self.root = ttk.Window(
                title="Dual GPU Optimizer", 
                themename=theme, 
                size=(1024, 768),
                position=(100, 100),
                minsize=(800, 600)
            )
            # Store the theme name used
            self.active_theme_name = theme
        # Fall back to ttkthemes if available
        elif TTKTHEMES_AVAILABLE:
            self.logger.debug("Using ttkthemes for theming")
            theme = theme or self.config.get("ui.theme", "arc")
            self.root = ThemedTk(theme=theme)
            self.root.title("Dual GPU Optimizer")
            self.root.geometry("1024x768+100+100")
            self.root.minsize(800, 600)
            self.active_theme_name = theme
        # Last resort: standard Tk with manual styling
        else:
            self.logger.debug("Using basic Tk with manual styling (purple theme)")
            self.root = tk.Tk()
            self.root.title("Dual GPU Optimizer")
            self.root.geometry("1024x768+100+100")
            self.root.minsize(800, 600)
            self.root.configure(bg=DARK_BACKGROUND)
            self.active_theme_name = "manual_purple"
            
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
            self.root.configure(bg=DARK_BACKGROUND)
            
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
        """Configure ttk styles for the application using the purple theme."""
        try:
            if TTKBOOTSTRAP_AVAILABLE:
                # Use the style from the ttkbootstrap window
                style = self.root.style
            elif TTKTHEMES_AVAILABLE:
                # Get the style associated with the ThemedTk root
                style = ttk.Style(self.root)
            else:
                # Basic Tk, configure manually
                style = ttk.Style(self.root)
                # Basic theme settings for Tk fallback
                style.theme_use('clam') # Use a theme that allows more customization
                style.configure('.', background=DARK_BACKGROUND, foreground=LIGHT_FOREGROUND, font=(DEFAULT_FONT, DEFAULT_FONT_SIZE))
                style.configure("TFrame", background=DARK_BACKGROUND)
                style.configure("TLabel", background=DARK_BACKGROUND, foreground=LIGHT_FOREGROUND)
                style.configure("TButton", background=PURPLE_PRIMARY, foreground=LIGHT_FOREGROUND)
                style.map("TButton", background=[('active', PURPLE_HIGHLIGHT)])
                style.configure("TNotebook", background=DARK_BACKGROUND, borderwidth=0)
                style.configure("TNotebook.Tab", background=PURPLE_PRIMARY, foreground=LIGHT_FOREGROUND, padding=[10, 5], borderwidth=0)
                style.map("TNotebook.Tab", background=[('selected', PURPLE_HIGHLIGHT)])
                style.configure("TLabelframe", background=DARK_BACKGROUND, bordercolor=PURPLE_PRIMARY)
                style.configure("TLabelframe.Label", background=DARK_BACKGROUND, foreground=PURPLE_HIGHLIGHT)
                style.configure("TScrollbar", background=DARK_BACKGROUND, troughcolor=PURPLE_PRIMARY, bordercolor=PURPLE_PRIMARY, arrowcolor=LIGHT_FOREGROUND)
                style.configure("TCombobox", fieldbackground=DARK_BACKGROUND, background=PURPLE_PRIMARY, foreground=LIGHT_FOREGROUND)
                style.configure("TEntry", fieldbackground=DARK_BACKGROUND, foreground=LIGHT_FOREGROUND, insertcolor=LIGHT_FOREGROUND)
                style.configure("Horizontal.TScale", background=DARK_BACKGROUND, troughcolor=PURPLE_PRIMARY)

            # --- Custom Progress Bar Styles (Purple Theme) ---
            # Default progress bar (primary purple)
            style.configure(
                "GPU.Horizontal.TProgressbar", 
                thickness=PROGRESSBAR_THICKNESS,
                troughcolor=DARK_BACKGROUND, # Use dark background for trough
                background=PURPLE_PRIMARY
            )
            
            # Highlight purple variant
            style.configure(
                "GPUPurpleHighlight.Horizontal.TProgressbar", 
                thickness=PROGRESSBAR_THICKNESS,
                troughcolor=DARK_BACKGROUND,
                background=PURPLE_HIGHLIGHT
            )
            
            # Pink accent variant
            style.configure(
                "GPUPink.Horizontal.TProgressbar", 
                thickness=PROGRESSBAR_THICKNESS,
                troughcolor=DARK_BACKGROUND,
                background=PINK_ACCENT
            )
            
            # Cyan accent variant
            style.configure(
                "GPUCyan.Horizontal.TProgressbar", 
                thickness=PROGRESSBAR_THICKNESS,
                troughcolor=DARK_BACKGROUND,
                background=CYAN_ACCENT
            )
            
            # Orange accent / Warning variant
            style.configure(
                "GPUOrange.Horizontal.TProgressbar", 
                thickness=PROGRESSBAR_THICKNESS,
                troughcolor=DARK_BACKGROUND,
                background=ORANGE_ACCENT # Use warning color for this
            )

            # --- Notebook Style (Subtle adjustments if using ttkbootstrap/ttkthemes) ---
            if TTKBOOTSTRAP_AVAILABLE or TTKTHEMES_AVAILABLE:
                style.configure(
                    "TNotebook.Tab", 
                    padding=[12, 6], # Slightly larger padding
                    font=(DEFAULT_FONT, DEFAULT_FONT_SIZE)
                )
                # Potentially customize tab colors further if needed for specific themes
                # style.map("TNotebook.Tab", background=[('selected', PURPLE_HIGHLIGHT)])
            
            # --- Frame and Label styles (ensure consistency if not using bootstrap/themes) ---
            if not (TTKBOOTSTRAP_AVAILABLE or TTKTHEMES_AVAILABLE):
                 # Already configured above in the manual styling section
                 pass
            else:
                # Ensure frames have transparent background to match theme
                style.configure("TFrame", background="") 
                # Labels should inherit background/foreground from theme
                style.configure("TLabel", background="", foreground="")

            # --- Settings Tab Specific Styles ---
            # Style for the 'Danger Zone' in settings
            style.configure(
                "Danger.TLabelframe", 
                bordercolor=WARNING_COLOR, # Use defined warning color
                borderwidth=2
            )
            style.configure(
                "Danger.TLabelframe.Label", 
                foreground=WARNING_COLOR # Use defined warning color
            )

            self.logger.debug("Custom ttk styles configured for purple theme.")

        except tk.TclError as e:
            self.logger.error(f"Failed to configure ttk styles: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during style configuration: {e}", exc_info=True)
    
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
        key = config_data.get("key")
        # If theme changed via config, prompt restart
        if key == "ui.theme":
             self._prompt_restart_for_theme()
        else:
            self.message_queue.put(("config_change", config_data))
    
    def _handle_theme_change(self, theme_data: Dict[str, Any]):
        """Handle theme change event."""
        new_theme = theme_data.get("theme")
        if not new_theme:
            return
        self.logger.info(f"Theme change requested to: {new_theme}")
        # Save the new theme to config
        self.config.set("ui.theme", new_theme)
        self.config.save()
        # Inform user about restart
        self._prompt_restart_for_theme()
    
    def _prompt_restart_for_theme(self):
        """Shows a message box informing the user to restart for theme changes."""
        messagebox.showinfo(
            "Theme Changed", 
            "Theme settings have been updated. Please restart the application for the changes to take full effect.",
            parent=self.root
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
                self.status_var.set(message[:150] + ('...' if len(message) > 150 else ''))
    
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
                    # Only refresh if not a theme change (handled separately)
                    if data.get("key") != "ui.theme":
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
            # If telemetry is a dict, use it directly, otherwise try to get data
            if isinstance(self.telemetry, dict):
                telemetry_data = self.telemetry
            else:
                # Try to get data from telemetry object if it has get_data method
                try:
                    telemetry_data = self.telemetry.get_data()
                except AttributeError:
                    # Fallback - telemetry might be the data itself
                    telemetry_data = self.telemetry
            
            # Publish telemetry update event
            event_bus.publish("gpu.telemetry.updated", telemetry_data)
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

def run_app(mock_mode: bool = False, theme: str = None):
    """
    Run the DualGPUOptimizer application.
    
    Args:
        mock_mode: Whether to use mock GPU data
        theme: Optional theme name to use
    """
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger = logging.getLogger("dualgpuopt.gui.app")
    logger.info(f"Starting application with mock_mode={mock_mode}, theme={theme}")
    
    try:
        # Create application instance
        app = DualGpuApp(
            root=None,
            theme=theme,
            mock_mode=mock_mode
        )
        
        # Run application main loop
        app.run()
        
        return 0
    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True)
        
        # Show error dialog
        if 'tk' in sys.modules:
            messagebox.showerror(
                "Application Error",
                f"Failed to start application: {e}\n\nCheck logs for details."
            )
        
        return 1

if __name__ == "__main__":
    main() 