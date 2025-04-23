"""
Main application module for DualGPUOptimizer
Provides the primary entry point for the GUI application
"""

"""
Main application module for DualGPUOptimizer
Provides the primary entry point for the GUI application
"""

import logging
import queue
import sys
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from dualgpuopt.gui.theme.compatibility import ensure_status_var


# Determine log directory - use temp directory or user home
def get_log_directory():
    """Get an appropriate directory for log files"""
    try:
        # First try to use the same directory as the executable/script
        if getattr(sys, "frozen", False):
            # We're running in a PyInstaller bundle
            base_dir = Path(sys._MEIPASS).parent
        else:
            # We're running in a normal Python environment
            base_dir = Path(__file__).parent.parent.parent

        # Try to create a logs directory
        logs_dir = base_dir / "logs"
        logs_dir.mkdir(exist_ok=True)

        # Test if we can write to it
        test_file = logs_dir / "write_test.tmp"
        try:
            test_file.write_text("test")
            test_file.unlink()  # Delete the test file
            return logs_dir
        except (PermissionError, OSError):
            # Fall back to other options if we can't write to the logs directory
            pass

        # Try user home directory
        user_dir = Path.home() / "DualGPUOptimizer" / "logs"
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    except Exception:
        # Use temp directory as last resort
        temp_dir = Path(tempfile.gettempdir()) / "DualGPUOptimizer"
        temp_dir.mkdir(exist_ok=True)
        return temp_dir


# Get log directory and configure logging
log_dir = get_log_directory()
log_file = log_dir / "dualgpuopt.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(log_file)],
)

logger = logging.getLogger("DualGPUOpt.MainApp")
logger.info(f"Starting application with log file at: {log_file}")

# Import UI compatibility modules first to handle missing dependencies
# This needs to be before other imports to ensure proper initialization
try:
    from ..ui.chat_compat import get_chat_tab
    from ..ui.compat import (
        create_widget,
        get_meter_widget,
        get_scrolled_frame,
        get_themed_tk,
    )

    logger.info("UI compatibility modules loaded successfully")
except ImportError as e:
    logger.error(f"Failed to import UI compatibility modules: {e}")
    # Set up minimal fallbacks if even the compatibility modules fail
    from tkinter import Tk as get_themed_tk
    from tkinter import ttk

    def get_meter_widget(parent, **kwargs):
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="0").pack()
        return frame

    def get_scrolled_frame(parent, **kwargs):
        return ttk.Frame(parent)

    def create_widget(widget_name, parent, **kwargs):
        try:
            return getattr(ttk, widget_name)(parent, **kwargs)
        except (AttributeError, tk.TclError):
            frame = ttk.Frame(parent)
            ttk.Label(frame, text=f"{widget_name} unavailable").pack()
            return frame

    def get_chat_tab(master, out_q):
        frame = ttk.Frame(master)
        ttk.Label(frame, text="Chat not available").pack()
        frame.handle_queue = lambda *args: None
        return frame


# Try to import event bus first
try:
    from ..services.event_bus import ConfigChangedEvent, GPUMetricsEvent, event_bus

    event_bus_available = True
    logger.info("Event bus available")
except ImportError:
    event_bus_available = False
    logger.warning("Could not import event_bus, creating minimal implementation")

    # Create a minimal event bus if the real one isn't available
    class MinimalEventBus:
        def subscribe_typed(self, *args, **kwargs):
            pass

        def subscribe(self, *args, **kwargs):
            pass

        def publish_typed(self, *args, **kwargs):
            pass

        def publish(self, *args, **kwargs):
            pass

        def unsubscribe(self, *args, **kwargs):
            pass

    event_bus = MinimalEventBus()

# Import our components
try:
    from ..telemetry import get_telemetry_service
    from . import dashboard, launcher, optimizer_tab, theme

    # We don't import ChatTab directly anymore - using get_chat_tab instead
    # ThemeSelector is imported and used in the MainApplication class
except ImportError as e:
    logger.error(f"Failed to import UI components: {e}")
    sys.exit(1)

# Check for advanced feature dependencies
try:
    # Create necessary directories if they don't exist
    for dir_path in ["batch", "services"]:
        Path(__file__).parent.parent.joinpath(dir_path).mkdir(exist_ok=True)

    # Create __init__.py in subdirectories if it doesn't exist
    for dir_path in ["batch", "services"]:
        init_path = Path(__file__).parent.parent.joinpath(dir_path, "__init__.py")
        if not init_path.exists():
            init_path.write_text(f'"""Package for {dir_path}."""')

    HAS_ADVANCED_FEATURES = True
except Exception as e:
    logger.warning(f"Failed to setup directories for advanced features: {e}")
    HAS_ADVANCED_FEATURES = False


class MainApplication(ttk.Frame):
    """Main application frame containing all UI components"""

    def __init__(self, parent):
        """
        Initialize the main application

        Args:
        ----
            parent: Parent widget
        """
        super().__init__(parent, padding=0)

        # Start telemetry service
        try:
            self.telemetry = get_telemetry_service()
            self.telemetry.start()
        except Exception as e:
            logger.error(f"Failed to start telemetry service: {e}")

            # Create a minimal telemetry service that won't break the app
            class MinimalTelemetry:
                def __init__(self):
                    self.running = False

                def start(self):
                    self.running = True

                def stop(self):
                    self.running = False

                def get_metrics(self):
                    return {}

            self.telemetry = MinimalTelemetry()
            self.telemetry.start()

        # Create chat queue for inter-thread communication
        self.chat_q = queue.Queue()

        # Configure grid layout with proper weights for responsive resizing
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)  # Main content area should expand

        # Store reference to parent for resize binding
        self.parent = parent

        # Initialize status var early to prevent theme errors
        self.status_var = tk.StringVar(value="Status: Ready")
        # Ensure status_var is available for theme system
        ensure_status_var(self)

        # Bind to window resize event for responsive adjustments
        self.parent.bind("<Configure>", self._on_window_resize)

        # Set minimum window size to prevent UI from becoming too cramped
        self.parent.minsize(800, 600)

        # Apply theme to parent window from config
        self._apply_theme()

        # Subscribe to events using event bus
        if event_bus_available:
            # Subscribe to theme changes
            event_bus.subscribe("config_changed.theme", self._handle_theme_change)
            # Subscribe to GPU metrics for status updates
            event_bus.subscribe_typed(GPUMetricsEvent, self._handle_gpu_metrics)
            # Subscribe to configuration changes
            event_bus.subscribe_typed(ConfigChangedEvent, self._handle_config_change)

        # Header with status
        header_frame = ttk.Frame(self, padding=10)
        header_frame.grid(row=0, column=0, sticky="ew")

        # Make header frame columns flexible
        header_frame.columnconfigure(1, weight=1)  # Middle space should expand

        # Title aligned left with larger font
        title_label = ttk.Label(header_frame, text="Dual GPU Optimizer", style="Heading.TLabel")
        title_label.grid(row=0, column=0, sticky="w")

        # Add theme toggle button to header - use create_widget for safe creation
        self.theme_toggle = create_widget(
            "ThemeToggleButton",
            header_frame,
            module_name="theme",
            fallback_class=ttk.Button,
        )
        if isinstance(self.theme_toggle, ttk.Button) and not hasattr(
            self.theme_toggle,
            "toggle_theme",
        ):
            # We got a fallback button, set up minimal functionality
            self.theme_toggle.configure(
                text="Toggle Theme",
                command=lambda: theme.toggle_theme(self.parent),
            )
        self.theme_toggle.grid(row=0, column=1, sticky="e", padx=10)

        # Status aligned right
        status_label = ttk.Label(
            header_frame,
            textvariable=self.status_var,
            foreground=theme.current_theme.get("success", "green"),
        )
        status_label.grid(row=0, column=2, sticky="e")

        # Create a PanedWindow to allow resizing content area
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.grid(row=1, column=0, sticky="nsew")

        # Create a container frame for the notebook
        self.notebook_container = ttk.Frame(self.paned)
        self.paned.add(self.notebook_container, weight=85)

        # Create notebook for tabs with proper padding and expansion
        self.notebook = ttk.Notebook(self.notebook_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add dashboard tab with error handling
        try:
            self.dashboard_tab = dashboard.DashboardView(self.notebook)
            self.notebook.add(self.dashboard_tab, text="Dashboard")
            logger.info("Dashboard tab created successfully")
        except Exception as e:
            logger.error(f"Error creating dashboard tab: {e}")
            self.dashboard_tab = ttk.Frame(self.notebook)
            error_label = ttk.Label(
                self.dashboard_tab,
                text=f"Dashboard unavailable: {str(e)[:100]}...",
            )
            error_label.pack(pady=20)
            retry_button = ttk.Button(
                self.dashboard_tab,
                text="Retry",
                command=self._retry_dashboard_tab,
            )
            retry_button.pack(pady=10)
            self.notebook.add(self.dashboard_tab, text="Dashboard")

        # Add optimizer tab with error handling
        try:
            self.optimizer_tab = optimizer_tab.OptimizerTab(self.notebook)
            self.notebook.add(self.optimizer_tab, text="Optimizer")
            logger.info("Optimizer tab created successfully")
        except Exception as e:
            logger.error(f"Error creating optimizer tab: {e}")
            self.optimizer_tab = ttk.Frame(self.notebook)
            error_label = ttk.Label(
                self.optimizer_tab,
                text=f"Optimizer unavailable: {str(e)[:100]}...",
            )
            error_label.pack(pady=20)

            # Add button to show detailed error
            def show_error_details():
                top = tk.Toplevel(self.parent)
                top.title("Error Details")
                top.geometry("600x400")
                text = tk.Text(top, wrap="word")
                text.insert("1.0", f"Error creating optimizer tab:\n\n{e!s}")
                text.pack(fill="both", expand=True, padx=10, pady=10)
                ttk.Button(top, text="Close", command=top.destroy).pack(pady=10)

            details_button = ttk.Button(
                self.optimizer_tab,
                text="Error Details",
                command=show_error_details,
            )
            details_button.pack(pady=5)

            retry_button = ttk.Button(
                self.optimizer_tab,
                text="Retry",
                command=self._retry_optimizer_tab,
            )
            retry_button.pack(pady=10)
            self.notebook.add(self.optimizer_tab, text="Optimizer")

        # Add launcher tab with error handling
        try:
            self.launcher_tab = launcher.LauncherTab(self.notebook)
            self.notebook.add(self.launcher_tab, text="Launcher")
            logger.info("Launcher tab created successfully")
        except Exception as e:
            logger.error(f"Error creating launcher tab: {e}")
            self.launcher_tab = ttk.Frame(self.notebook)
            error_label = ttk.Label(
                self.launcher_tab,
                text=f"Launcher unavailable: {str(e)[:100]}...",
            )
            error_label.pack(pady=20)
            retry_button = ttk.Button(
                self.launcher_tab,
                text="Retry",
                command=self._retry_launcher_tab,
            )
            retry_button.pack(pady=10)
            self.notebook.add(self.launcher_tab, text="Launcher")

        # Add chat tab using our compatibility function with error handling
        try:
            self.chat_tab = get_chat_tab(self.notebook, self.chat_q)
            self.notebook.add(self.chat_tab, text="Chat")
            logger.info("Chat tab created successfully")
        except Exception as e:
            logger.error(f"Error creating chat tab: {e}")
            self.chat_tab = ttk.Frame(self.notebook)
            ttk.Label(self.chat_tab, text=f"Chat unavailable: {str(e)[:100]}...").pack(pady=20)

            # Add instructions for installing chat dependencies
            ttk.Label(
                self.chat_tab,
                text="To enable chat functionality, install these dependencies:",
            ).pack(pady=10)
            ttk.Label(self.chat_tab, text="pip install requests sseclient-py").pack()

            self.notebook.add(self.chat_tab, text="Chat")
            # Create a minimal handler for chat queue
            self.chat_tab.handle_queue = lambda *args: None

        # Create bottom container for status and metrics
        self.bottom_container = ttk.Frame(self.paned)
        self.paned.add(self.bottom_container, weight=15)

        # Status bar with proper structure for multiple elements
        status_frame = ttk.Frame(self.bottom_container, relief="sunken", padding=(10, 5))
        status_frame.pack(fill=tk.BOTH, expand=True)
        status_frame.columnconfigure(1, weight=1)  # Middle space expands

        # GPU count indicator on left
        self.gpu_count_var = tk.StringVar(value="GPUs: Detecting...")
        gpu_count_label = ttk.Label(status_frame, textvariable=self.gpu_count_var)
        gpu_count_label.grid(row=0, column=0, sticky="w")

        # Version on right
        version_label = ttk.Label(status_frame, text="v0.2.1")
        version_label.grid(row=0, column=2, sticky="e")

        # Add tokens-per-second meter to status bar using our compatibility function
        try:
            self.tps_meter = get_meter_widget(
                status_frame,
                metersize=50,
                amounttotal=100,
                bootstyle="success",
                subtext="tok/s",
                textright="",
                interactive=False,
            )
            self.tps_meter.grid(row=0, column=3, padx=10, sticky="e")
        except Exception as e:
            logger.error(f"Error creating TPS meter: {e}")
            # Create a minimal label as fallback
            self.tps_var = tk.StringVar(value="0 tok/s")
            self.tps_meter = ttk.Label(status_frame, textvariable=self.tps_var)
            self.tps_meter.grid(row=0, column=3, padx=10, sticky="e")
            # Add configure method for compatibility
            self.tps_meter.configure = lambda **kwargs: self.tps_var.set(
                f"{kwargs.get('amountused', 0)} tok/s",
            )

        # Start GPU detection if not using event bus
        if not event_bus_available:
            self.detect_gpus()

        # Start message polling
        self._poll()

        # Initial resize handling
        self._handle_resize()

        # Log successful initialization
        logger.info("MainApplication initialized successfully")

    def _retry_dashboard_tab(self):
        """Retry loading the dashboard tab after failure"""
        try:
            # Remove the old tab
            self.notebook.forget(self.notebook.index(self.dashboard_tab))

            # Create a new dashboard tab
            self.dashboard_tab = dashboard.DashboardView(self.notebook)
            self.notebook.insert(0, self.dashboard_tab, text="Dashboard")
            self.notebook.select(0)
            logger.info("Dashboard tab successfully reloaded")

            # Show success message
            self.status_var.set("Dashboard tab reloaded successfully")
            self.after(3000, lambda: self.status_var.set("Status: Ready"))
        except Exception as e:
            logger.error(f"Error recreating dashboard tab: {e}")
            # Create a new error frame
            self.dashboard_tab = ttk.Frame(self.notebook)
            ttk.Label(self.dashboard_tab, text=f"Dashboard unavailable: {str(e)[:100]}...").pack(
                pady=20,
            )
            retry_button = ttk.Button(
                self.dashboard_tab,
                text="Retry",
                command=self._retry_dashboard_tab,
            )
            retry_button.pack(pady=10)
            self.notebook.insert(0, self.dashboard_tab, text="Dashboard")
            self.notebook.select(0)

            # Show error message
            self.status_var.set("Failed to reload dashboard tab")
            self.after(3000, lambda: self.status_var.set("Status: Ready"))

    def _retry_optimizer_tab(self):
        """Retry loading the optimizer tab after failure"""
        try:
            # Get tab index
            tab_index = self.notebook.index(self.optimizer_tab)

            # Remove the old tab
            self.notebook.forget(tab_index)

            # Create a new optimizer tab
            self.optimizer_tab = optimizer_tab.OptimizerTab(self.notebook)
            self.notebook.insert(tab_index, self.optimizer_tab, text="Optimizer")
            self.notebook.select(tab_index)
            logger.info("Optimizer tab successfully reloaded")

            # Show success message
            self.status_var.set("Optimizer tab reloaded successfully")
            self.after(3000, lambda: self.status_var.set("Status: Ready"))
        except Exception as e:
            logger.error(f"Error recreating optimizer tab: {e}")
            # Create a new error frame
            self.optimizer_tab = ttk.Frame(self.notebook)
            ttk.Label(self.optimizer_tab, text=f"Optimizer unavailable: {str(e)[:100]}...").pack(
                pady=20,
            )
            retry_button = ttk.Button(
                self.optimizer_tab,
                text="Retry",
                command=self._retry_optimizer_tab,
            )
            retry_button.pack(pady=10)
            self.notebook.insert(tab_index, self.optimizer_tab, text="Optimizer")
            self.notebook.select(tab_index)

            # Show error message
            self.status_var.set("Failed to reload optimizer tab")
            self.after(3000, lambda: self.status_var.set("Status: Ready"))

    def _retry_launcher_tab(self):
        """Retry loading the launcher tab after failure"""
        try:
            # Get tab index
            tab_index = self.notebook.index(self.launcher_tab)

            # Remove the old tab
            self.notebook.forget(tab_index)

            # Create a new launcher tab
            self.launcher_tab = launcher.LauncherTab(self.notebook)
            self.notebook.insert(tab_index, self.launcher_tab, text="Launcher")
            self.notebook.select(tab_index)
            logger.info("Launcher tab successfully reloaded")

            # Show success message
            self.status_var.set("Launcher tab reloaded successfully")
            self.after(3000, lambda: self.status_var.set("Status: Ready"))
        except Exception as e:
            logger.error(f"Error recreating launcher tab: {e}")
            # Create a new error frame
            self.launcher_tab = ttk.Frame(self.notebook)
            ttk.Label(self.launcher_tab, text=f"Launcher unavailable: {str(e)[:100]}...").pack(
                pady=20,
            )
            retry_button = ttk.Button(
                self.launcher_tab,
                text="Retry",
                command=self._retry_launcher_tab,
            )
            retry_button.pack(pady=10)
            self.notebook.insert(tab_index, self.launcher_tab, text="Launcher")
            self.notebook.select(tab_index)

            # Show error message
            self.status_var.set("Failed to reload launcher tab")
            self.after(3000, lambda: self.status_var.set("Status: Ready"))

    def _poll(self):
        """Poll messages from chat queue and dispatch them"""
        try:
            while True:
                kind, val = self.chat_q.get_nowait()
                # Handle chat messages
                try:
                    self.chat_tab.handle_queue(kind, val)
                except Exception as e:
                    logger.error(f"Error handling chat message: {e}")

                # Update TPS meter if we got TPS info
                if kind == "tps":
                    try:
                        self.tps_meter.configure(amountused=min(val, 100))
                    except (AttributeError, Exception) as e:
                        logger.debug(f"TPS meter update failed: {e}")
        except queue.Empty:
            pass
        except Exception as e:
            logger.error(f"Error in message polling: {e}")
        finally:
            # Continue polling regardless of errors
            self.after(40, self._poll)

    def detect_gpus(self):
        """Detect available GPUs (used if event bus not available)"""
        try:
            # Try to get GPU info from telemetry service
            metrics = self.telemetry.get_metrics()
            gpu_count = len(metrics)

            if gpu_count > 0:
                # Extract GPU names if available, otherwise use generic description
                if hasattr(next(iter(metrics.values())), "name"):
                    names = [m.name for m in metrics.values()]
                    self.gpu_count_var.set(f"GPUs: {gpu_count} - {', '.join(names)}")
                else:
                    self.gpu_count_var.set(f"GPUs: {gpu_count} detected")
            else:
                self.gpu_count_var.set("GPUs: None detected")

        except Exception as e:
            logger.error(f"Error detecting GPUs: {e}")
            self.gpu_count_var.set("GPUs: Error detecting")

        # Schedule another check in 5 seconds
        self.after(5000, self.detect_gpus)

    def _handle_gpu_metrics(self, event):
        """
        Handle GPU metrics events from the event bus

        Args:
        ----
            event: GPUMetricsEvent object
        """
        # Update GPU count display if this is the first GPU (avoid duplicate updates)
        if event.gpu_index == 0:
            metrics = self.telemetry.get_metrics()
            gpu_count = len(metrics)

            if gpu_count > 0:
                if hasattr(next(iter(metrics.values())), "name"):
                    names = [m.name for m in metrics.values()]
                    self.gpu_count_var.set(f"GPUs: {gpu_count} - {', '.join(names[:2])}")
                    if len(names) > 2:
                        self.gpu_count_var.set(f"{self.gpu_count_var.get()} +{len(names)-2} more")
                else:
                    self.gpu_count_var.set(f"GPUs: {gpu_count} detected")
            else:
                self.gpu_count_var.set("GPUs: None detected")

    def _handle_config_change(self, event):
        """
        Handle configuration change events

        Args:
        ----
            event: ConfigChangedEvent object
        """
        # Handle specific configuration changes
        if event.config_key == "theme":
            # Theme changes are handled by _handle_theme_change via string events
            pass
        elif event.config_key in ["context_size", "gpu_split", "thread_count"]:
            # Show a status message for important config changes
            self.status_var.set(f"Configuration updated: {event.config_key}")
            self.after(3000, lambda: self.status_var.set("Status: Ready"))

    def destroy(self):
        """Clean up resources when application is closed"""
        # Unsubscribe from events if event bus is available
        if event_bus_available:
            if hasattr(self, "_handle_gpu_metrics"):
                event_bus.unsubscribe(GPUMetricsEvent, self._handle_gpu_metrics)
            if hasattr(self, "_handle_theme_change"):
                event_bus.unsubscribe("config_changed.theme", self._handle_theme_change)
            if hasattr(self, "_handle_config_change"):
                event_bus.unsubscribe(ConfigChangedEvent, self._handle_config_change)

        # Stop telemetry service
        if (
            hasattr(self, "telemetry")
            and self.telemetry
            and getattr(self.telemetry, "running", False)
        ):
            self.telemetry.stop()

        super().destroy()

    def _on_window_resize(self, event=None):
        """
        Handle window resize events

        Args:
        ----
            event: The resize event (optional)
        """
        # Debounce resize events to avoid excessive processing
        if hasattr(self, "_resize_timer"):
            self.after_cancel(self._resize_timer)
        self._resize_timer = self.after(100, self._handle_resize)

    def _handle_resize(self):
        """Adjust UI elements based on current window size"""
        try:
            # Get current window dimensions
            width = self.parent.winfo_width()
            height = self.parent.winfo_height()

            # Adjust vertical paned window proportions based on window height
            if height > 800:
                # For taller windows, give more space to the main content
                self.paned.sashpos(0, int(height * 0.85))
            elif height > 600:
                # For medium height windows
                self.paned.sashpos(0, int(height * 0.8))
            else:
                # For smaller windows
                self.paned.sashpos(0, int(height * 0.75))

            # Adjust padding based on window size
            if width < 1000:
                # Smaller padding for small windows
                self.notebook.configure(padding=(5, 5))
            else:
                # More padding for larger windows
                self.notebook.configure(padding=(10, 10))

            # Log resize for debugging
            logger.debug(f"Window resized to {width}x{height}, adjustments applied")

        except Exception as e:
            logger.warning(f"Error handling resize: {e}")

        # Ensure all widgets are properly updated
        self.update_idletasks()

    def _apply_theme(self):
        """Apply theme from configuration to the application"""
        try:
            # Load and apply theme from config
            theme.load_theme_from_config(self.parent)
            logger.info(f"Applied theme from config: {theme.current_theme}")

            # Update status
            self.status_var.set("Theme applied from config")
            # Reset status after 3 seconds
            self.after(3000, lambda: self.status_var.set("Status: Ready"))
        except Exception as e:
            logger.error(f"Error applying theme: {e}")

    def _handle_theme_change(self, theme_data):
        """
        Handle theme change events from other components

        Args:
        ----
            theme_data: Theme data, either name or dictionary with theme information
        """
        try:
            # Extract theme name based on data type
            if isinstance(theme_data, dict) and "value" in theme_data:
                theme_name = theme_data["value"]
            elif isinstance(theme_data, str):
                theme_name = theme_data
            else:
                theme_name = str(theme_data)

            logger.info(f"Theme change event received: {theme_name}")

            # Apply the theme to the root window
            theme.set_theme(self.parent, theme_name)

            # Update status
            self.status_var.set(f"Theme changed to {theme_name}")
            # Reset status after 3 seconds
            self.after(3000, lambda: self.status_var.set("Status: Ready"))
        except Exception as e:
            logger.error(f"Error handling theme change: {e}")


def find_icon():
    """
    Find the application icon in various locations

    Returns
    -------
        Path to the icon file, or None if not found
    """
    # Check multiple locations for the icon
    potential_paths = []

    # If running in PyInstaller bundle
    if getattr(sys, "frozen", False):
        # Running in PyInstaller bundle
        base_dir = Path(sys._MEIPASS)
        exe_dir = Path(sys.executable).parent

        potential_paths.extend(
            [
                base_dir / "dualgpuopt" / "resources" / "icon.png",
                base_dir / "dualgpuopt" / "resources" / "icon.ico",
                base_dir / "resources" / "icon.png",
                base_dir / "resources" / "icon.ico",
                exe_dir / "dualgpuopt" / "resources" / "icon.png",
                exe_dir / "dualgpuopt" / "resources" / "icon.ico",
                exe_dir / "resources" / "icon.png",
                exe_dir / "resources" / "icon.ico",
                exe_dir / "icon.png",
                exe_dir / "icon.ico",
            ],
        )
    else:
        # Running in development mode
        current_dir = Path(__file__).parent
        root_dir = current_dir.parent.parent

        potential_paths.extend(
            [
                current_dir / "resources" / "icon.png",
                current_dir.parent / "resources" / "icon.png",
                root_dir / "dualgpuopt" / "resources" / "icon.png",
                root_dir / "assets" / "icon.png",
                root_dir / "dualgpuopt" / "resources" / "icon.ico",
                root_dir / "assets" / "icon.ico",
                Path("dualgpuopt") / "resources" / "icon.png",
                Path("dualgpuopt") / "resources" / "icon.ico",
                Path("assets") / "icon.png",
                Path("assets") / "icon.ico",
                Path("icon.png"),
                Path("icon.ico"),
            ],
        )

    # Check each path and return the first one that exists
    for path in potential_paths:
        if path.exists():
            logger.info(f"Found icon at: {path}")
            return path

    # No icon found
    logger.warning("No icon found in any of the expected locations")
    return None


def run():
    """Main entry point for the application"""
    # Import config service to ensure it's initialized
    try:
        from ..services.config_service import config_service

        logger.info("Config service initialized")
    except ImportError:
        logger.warning("Could not import config_service, theme persistence may not work")

    # Use our compatibility function to get the best available themed Tk window
    root = get_themed_tk()

    root.title("DualGPUOptimizer")
    root.geometry("800x600")

    # Set application icon
    try:
        icon_path = find_icon()
        if icon_path:
            # Use PhotoImage for PNG or TkImage for ICO
            if icon_path.suffix.lower() == ".png":
                icon = tk.PhotoImage(file=str(icon_path))
                root.iconphoto(True, icon)
            elif icon_path.suffix.lower() == ".ico" and not getattr(sys, "frozen", False):
                # In development mode, try to use the .ico file directly
                root.iconbitmap(str(icon_path))
        else:
            logger.warning("No application icon found")
    except Exception as e:
        logger.warning(f"Failed to load application icon: {e}")

    # Apply initial minimal theme (full theme will be applied by MainApplication)
    theme.fix_dpi_scaling(root)
    theme.configure_fonts(root)

    # Create and configure main application
    app = MainApplication(root)
    app.pack(fill=tk.BOTH, expand=True)

    # Handle window close
    def on_closing():
        # Save theme preference if config service is available
        try:
            from ..services.config_service import config_service

            current_theme_name = next(
                (
                    name
                    for name, colors in theme.AVAILABLE_THEMES.items()
                    if colors == theme.current_theme
                ),
                "dark_purple",
            )
            config_service.set("theme", current_theme_name)
            logger.info(f"Saved theme preference on exit: {current_theme_name}")
        except (ImportError, Exception) as e:
            logger.warning(f"Could not save theme preference on exit: {e}")

        app.destroy()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Start the main loop
    root.mainloop()


if __name__ == "__main__":
    run()
