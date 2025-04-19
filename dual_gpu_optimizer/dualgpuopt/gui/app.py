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

<<<<<<< HEAD
# Import constants first to avoid circular imports
from dualgpuopt.gui.constants import (
    PAD, 
    DEFAULT_CHART_HEIGHT,
    DEFAULT_CHART_BG,
    DEFAULT_CHART_FG,
    GPU_COLORS,
    DEFAULT_FONT,
    DEFAULT_FONT_SIZE,
<<<<<<< HEAD
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

=======
    UPDATE_INTERVAL_MS
)

# Define the progressbar thickness here since it's specific to this module
PROGRESSBAR_THICKNESS = 8

=======
>>>>>>> 3565cbc (Update documentation for DualGPUOptimizer to provide a comprehensive overview of GPU management, model optimization, execution management, and configuration handling. Enhanced descriptions for clarity and organized content for better readability. Adjusted glob patterns for improved file matching, ensuring accurate documentation coverage for multi-GPU setups in machine learning workloads.)
from dualgpuopt import gpu_info, telemetry
from dualgpuopt.tray import init_tray
from dualgpuopt.gui.theme import apply_theme, update_widgets_theme, generate_colors

>>>>>>> 199829b (Update documentation for DualGPUOptimizer to provide a high-level overview of GPU optimization and model inference systems. Organized content into key components: Core GPU Management, Model Optimization Engine, Command System, Monitoring Dashboard, and State Management. Enhanced glob patterns for improved file matching and clarified key implementation files, ensuring comprehensive coverage of system functionalities and integration points.)
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

<<<<<<< HEAD
class DualGpuApp:
    """Main application class for the Dual GPU Optimizer GUI."""
=======
# Import our new services
from dualgpuopt.services.event_service import event_bus
from dualgpuopt.services.state_service import app_state
from dualgpuopt.services.config_service import config_service
from dualgpuopt.services.error_service import error_service


class DualGpuApp(ttk.Frame):
    """Main application class for the DualGPUOptimizer."""
>>>>>>> 3565cbc (Update documentation for DualGPUOptimizer to provide a comprehensive overview of GPU management, model optimization, execution management, and configuration handling. Enhanced descriptions for clarity and organized content for better readability. Adjusted glob patterns for improved file matching, ensuring accurate documentation coverage for multi-GPU setups in machine learning workloads.)
    
    def __init__(self, root: tk.Tk = None, theme: str = None, mock_mode: bool = False):
        """Initialize the application GUI and services."""
        # Set up logging first to ensure it's available throughout initialization
        self.setup_logger()
        self.logger.info("Starting DualGPUOptimizer application")
        
<<<<<<< HEAD
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
=======
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
>>>>>>> 3565cbc (Update documentation for DualGPUOptimizer to provide a comprehensive overview of GPU management, model optimization, execution management, and configuration handling. Enhanced descriptions for clarity and organized content for better readability. Adjusted glob patterns for improved file matching, ensuring accurate documentation coverage for multi-GPU setups in machine learning workloads.)
        
    def create_root_window(self, theme: str = None):
        """Create and configure the root window with appropriate theme support."""
        # Use ttkbootstrap if available
        if TTKBOOTSTRAP_AVAILABLE:
            self.logger.debug("Using ttkbootstrap for theming")
<<<<<<< HEAD
            theme = theme or self.config.get("ui.theme", "vapor")
=======
            theme = theme or self.config.get("ui.theme", "darkly")
>>>>>>> 199829b (Update documentation for DualGPUOptimizer to provide a high-level overview of GPU optimization and model inference systems. Organized content into key components: Core GPU Management, Model Optimization Engine, Command System, Monitoring Dashboard, and State Management. Enhanced glob patterns for improved file matching and clarified key implementation files, ensuring comprehensive coverage of system functionalities and integration points.)
            self.root = ttk.Window(
                title="Dual GPU Optimizer", 
                themename=theme, 
                size=(1024, 768),
                position=(100, 100),
                minsize=(800, 600)
            )
<<<<<<< HEAD
            # Store the theme name used
            self.active_theme_name = theme
        # Fall back to ttkthemes if available
        elif TTKTHEMES_AVAILABLE:
            self.logger.debug("Using ttkthemes for theming")
            theme = theme or self.config.get("ui.theme", "arc")
=======
        # Fall back to ttkthemes if available
        elif TTKTHEMES_AVAILABLE:
            self.logger.debug("Using ttkthemes for theming")
            theme = theme or self.config.get("ui.theme", "black")
>>>>>>> 199829b (Update documentation for DualGPUOptimizer to provide a high-level overview of GPU optimization and model inference systems. Organized content into key components: Core GPU Management, Model Optimization Engine, Command System, Monitoring Dashboard, and State Management. Enhanced glob patterns for improved file matching and clarified key implementation files, ensuring comprehensive coverage of system functionalities and integration points.)
            self.root = ThemedTk(theme=theme)
            self.root.title("Dual GPU Optimizer")
            self.root.geometry("1024x768+100+100")
            self.root.minsize(800, 600)
<<<<<<< HEAD
            self.active_theme_name = theme
        # Last resort: standard Tk with manual styling
        else:
            self.logger.debug("Using basic Tk with manual styling (purple theme)")
=======
        # Last resort: standard Tk with manual styling
        else:
            self.logger.debug("Using basic Tk with manual styling")
>>>>>>> 199829b (Update documentation for DualGPUOptimizer to provide a high-level overview of GPU optimization and model inference systems. Organized content into key components: Core GPU Management, Model Optimization Engine, Command System, Monitoring Dashboard, and State Management. Enhanced glob patterns for improved file matching and clarified key implementation files, ensuring comprehensive coverage of system functionalities and integration points.)
            self.root = tk.Tk()
            self.root.title("Dual GPU Optimizer")
            self.root.geometry("1024x768+100+100")
            self.root.minsize(800, 600)
<<<<<<< HEAD
            self.root.configure(bg=DARK_BACKGROUND)
            self.active_theme_name = "manual_purple"
            
=======
            
            # Apply manual dark theme
            apply_theme(self.root)
            
>>>>>>> 199829b (Update documentation for DualGPUOptimizer to provide a high-level overview of GPU optimization and model inference systems. Organized content into key components: Core GPU Management, Model Optimization Engine, Command System, Monitoring Dashboard, and State Management. Enhanced glob patterns for improved file matching and clarified key implementation files, ensuring comprehensive coverage of system functionalities and integration points.)
        # Increase base font size to Segoe UI 11
        default_font = (DEFAULT_FONT, DEFAULT_FONT_SIZE) if sys.platform == "win32" else ("Helvetica", DEFAULT_FONT_SIZE)
        self.root.option_add("*Font", default_font)
            
        # Set up window icon
        try:
<<<<<<< HEAD
            icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "gpu_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            self.logger.warning(f"Failed to set window icon: {e}")
            
        # Set up close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
<<<<<<< HEAD
    
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
=======
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
>>>>>>> 3565cbc (Update documentation for DualGPUOptimizer to provide a comprehensive overview of GPU management, model optimization, execution management, and configuration handling. Enhanced descriptions for clarity and organized content for better readability. Adjusted glob patterns for improved file matching, ensuring accurate documentation coverage for multi-GPU setups in machine learning workloads.)

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
        
<<<<<<< HEAD
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
=======
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
>>>>>>> 3565cbc (Update documentation for DualGPUOptimizer to provide a comprehensive overview of GPU management, model optimization, execution management, and configuration handling. Enhanced descriptions for clarity and organized content for better readability. Adjusted glob patterns for improved file matching, ensuring accurate documentation coverage for multi-GPU setups in machine learning workloads.)
    
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
                
<<<<<<< HEAD
=======
                # Save the telemetry for history
                self.tele_hist.append(telemetry)
                
                # Limit history to 60 samples
                if len(self.tele_hist) > 60:
                    self.tele_hist = self.tele_hist[-60:]
                    
                # Publish telemetry update event
                event_bus.publish("telemetry_updated", telemetry)
>>>>>>> 3565cbc (Update documentation for DualGPUOptimizer to provide a comprehensive overview of GPU management, model optimization, execution management, and configuration handling. Enhanced descriptions for clarity and organized content for better readability. Adjusted glob patterns for improved file matching, ensuring accurate documentation coverage for multi-GPU setups in machine learning workloads.)
        except queue.Empty:
            # No more messages, schedule next check
            pass
<<<<<<< HEAD
=======
        except Exception as e:
            error_service.handle_error(e, level="WARNING", title="Telemetry Error",
                                     context={"operation": "update_telemetry"})
>>>>>>> 3565cbc (Update documentation for DualGPUOptimizer to provide a comprehensive overview of GPU management, model optimization, execution management, and configuration handling. Enhanced descriptions for clarity and organized content for better readability. Adjusted glob patterns for improved file matching, ensuring accurate documentation coverage for multi-GPU setups in machine learning workloads.)
        
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
    
<<<<<<< HEAD
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
=======
    app = DualGpuApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root, app))
    root.mainloop()


def on_close(root: tk.Tk, app: DualGpuApp) -> None:
>>>>>>> 3565cbc (Update documentation for DualGPUOptimizer to provide a comprehensive overview of GPU management, model optimization, execution management, and configuration handling. Enhanced descriptions for clarity and organized content for better readability. Adjusted glob patterns for improved file matching, ensuring accurate documentation coverage for multi-GPU setups in machine learning workloads.)
    """
    Run the DualGPUOptimizer application.
    
    Args:
<<<<<<< HEAD
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

=======
    
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

>>>>>>> 199829b (Update documentation for DualGPUOptimizer to provide a high-level overview of GPU optimization and model inference systems. Organized content into key components: Core GPU Management, Model Optimization Engine, Command System, Monitoring Dashboard, and State Management. Enhanced glob patterns for improved file matching and clarified key implementation files, ensuring comprehensive coverage of system functionalities and integration points.)
if __name__ == "__main__":
    main() 
=======
        root: The root Tk window
        app: The application instance
    """
    # Publish app_exit event
    event_bus.publish("app_exit")
    
    # Save state
    app._save_state()
    
    # Clean up resources
    root.destroy() 
>>>>>>> 3565cbc (Update documentation for DualGPUOptimizer to provide a comprehensive overview of GPU management, model optimization, execution management, and configuration handling. Enhanced descriptions for clarity and organized content for better readability. Adjusted glob patterns for improved file matching, ensuring accurate documentation coverage for multi-GPU setups in machine learning workloads.)
