"""
Main application module for DualGPUOptimizer
Provides the primary entry point for the GUI application
"""
import tkinter as tk
from tkinter import ttk
import threading
import time
import logging
import sys
import os
import tempfile
from pathlib import Path
import queue

# Determine log directory - use temp directory or user home
def get_log_directory():
    """Get an appropriate directory for log files"""
    try:
        # First try to use the same directory as the executable/script
        if getattr(sys, 'frozen', False):
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
    except Exception as e:
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)

logger = logging.getLogger("DualGPUOpt.MainApp")
logger.info(f"Starting application with log file at: {log_file}")

# Import our components
from . import dashboard
from . import optimizer_tab
from . import launcher
from . import theme
from ..telemetry import get_telemetry_service
from ..chat_tab import ChatTab  # Add import for the ChatTab
from .theme_selector import ThemeSelector  # Import theme selector
from ..services.event_service import event_bus  # Import event bus

# Check for advanced feature dependencies
try:
    # Create necessary directories if they don't exist
    for dir_path in ['batch', 'services']:
        Path(__file__).parent.parent.joinpath(dir_path).mkdir(exist_ok=True)
    
    # Create __init__.py in subdirectories if it doesn't exist
    for dir_path in ['batch', 'services']:
        init_path = Path(__file__).parent.parent.joinpath(dir_path, '__init__.py')
        if not init_path.exists():
            init_path.write_text('"""Package for {}."""'.format(dir_path))
    
    HAS_ADVANCED_FEATURES = True
except Exception as e:
    logger.warning(f"Failed to setup directories for advanced features: {e}")
    HAS_ADVANCED_FEATURES = False


class MainApplication(ttk.Frame):
    """Main application frame containing all UI components"""
    
    def __init__(self, parent):
        """Initialize the main application
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent, padding=0)
        
        # Start telemetry service
        self.telemetry = get_telemetry_service()
        self.telemetry.start()
        
        # Create chat queue for inter-thread communication
        self.chat_q = queue.Queue()
        
        # Configure grid layout with proper weights for responsive resizing
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)  # Main content area should expand
        
        # Store reference to parent for resize binding
        self.parent = parent
        
        # Bind to window resize event for responsive adjustments
        self.parent.bind("<Configure>", self._on_window_resize)
        
        # Set minimum window size to prevent UI from becoming too cramped
        self.parent.minsize(800, 600)
        
        # Apply theme to parent window from config
        self._apply_theme()
        
        # Subscribe to theme change events
        event_bus.subscribe("config_changed:theme", self._handle_theme_change)
        
        # Header with status
        header_frame = ttk.Frame(self, padding=10)
        header_frame.grid(row=0, column=0, sticky="ew")
        
        # Make header frame columns flexible
        header_frame.columnconfigure(1, weight=1)  # Middle space should expand
        
        # Title aligned left with larger font
        title_label = ttk.Label(header_frame, text="Dual GPU Optimizer", style="Heading.TLabel")
        title_label.grid(row=0, column=0, sticky="w")
        
        # Add theme toggle button to header
        self.theme_toggle = theme.ThemeToggleButton(header_frame)
        self.theme_toggle.grid(row=0, column=1, sticky="e", padx=10)
        
        # Status aligned right
        self.status_var = tk.StringVar(value="Status: Ready")
        status_label = ttk.Label(header_frame, textvariable=self.status_var, 
                                foreground=theme.current_theme["success"])
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
        
        # Add dashboard tab
        self.dashboard_tab = dashboard.DashboardView(self.notebook)
        self.notebook.add(self.dashboard_tab, text="Dashboard")
        
        # Add optimizer tab
        self.optimizer_tab = optimizer_tab.OptimizerTab(self.notebook)
        self.notebook.add(self.optimizer_tab, text="Optimizer")
        
        # Add launcher tab
        self.launcher_tab = launcher.LauncherTab(self.notebook)
        self.notebook.add(self.launcher_tab, text="Launcher")
        
        # Add chat tab
        self.chat_tab = ChatTab(self.notebook, self.chat_q)
        self.notebook.add(self.chat_tab, text="Chat")
        
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
        version_label = ttk.Label(status_frame, text="v0.2.0")
        version_label.grid(row=0, column=2, sticky="e")
        
        # Add tokens-per-second meter to status bar
        self.tps_meter = None
        try:
            # Check if ttkbootstrap is available with Meter widget
            import ttkbootstrap as ttk_bs
            if hasattr(ttk_bs, 'Meter'):
                self.tps_meter = ttk_bs.Meter(status_frame, metersize=50, amounttotal=100,
                                          bootstyle="success", subtext="tok/s",
                                          textright="", interactive=False)
                self.tps_meter.grid(row=0, column=3, padx=10, sticky="e")
            else:
                # Fallback to regular label if Meter not available
                self.tps_label = ttk.Label(status_frame, text="0 tok/s")
                self.tps_label.grid(row=0, column=3, padx=10, sticky="e")
        except Exception as e:
            logger.warning(f"Could not create TPS meter: {e}")
            # Fallback to regular label
            self.tps_label = ttk.Label(status_frame, text="0 tok/s")
            self.tps_label.grid(row=0, column=3, padx=10, sticky="e")
        
        # Start GPU detection
        self.detect_gpus()
        
        # Start message polling
        self._poll()
        
        # Initial resize handling
        self._handle_resize()
    
    def _poll(self):
        """Poll messages from chat queue and dispatch them"""
        try:
            while True:
                kind, val = self.chat_q.get_nowait()
                self.chat_tab.handle_queue(kind, val)
                if kind == "tps":
                    if self.tps_meter is not None:
                        self.tps_meter.configure(amountused=min(val, 100))
                    elif hasattr(self, 'tps_label'):
                        self.tps_label.configure(text=f"{val:.1f} tok/s")
        except queue.Empty:
            pass
        self.after(40, self._poll)
    
    def detect_gpus(self):
        """Detect available GPUs"""
        try:
            # Try to get GPU info from telemetry service
            metrics = self.telemetry.get_metrics()
            gpu_count = len(metrics)
            
            if gpu_count > 0:
                names = [m.name for m in metrics.values()]
                self.gpu_count_var.set(f"GPUs: {gpu_count} - {', '.join(names)}")
            else:
                self.gpu_count_var.set("GPUs: None detected")
            
        except Exception as e:
            logger.error(f"Error detecting GPUs: {e}")
            self.gpu_count_var.set("GPUs: Error detecting")
        
        # Schedule another check in 5 seconds
        self.after(5000, self.detect_gpus)
    
    def destroy(self):
        """Clean up resources when application is closed"""
        # Stop telemetry service
        if self.telemetry and self.telemetry.running:
            self.telemetry.stop()
        
        super().destroy()
    
    def _on_window_resize(self, event=None):
        """Handle window resize events
        
        Args:
            event: The resize event (optional)
        """
        # Debounce resize events to avoid excessive processing
        if hasattr(self, '_resize_timer'):
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
    
    def _handle_theme_change(self, theme_name):
        """Handle theme change events from other components
        
        Args:
            theme_name: Name of the new theme
        """
        logger.info(f"Theme change event received: {theme_name}")
        # Apply the theme to the root window
        theme.set_theme(self.parent, theme_name)
        
        # Update status
        self.status_var.set(f"Theme changed to {theme_name}")
        # Reset status after 3 seconds
        self.after(3000, lambda: self.status_var.set("Status: Ready"))


def find_icon():
    """Find the application icon in various locations
    
    Returns:
        Path to the icon file, or None if not found
    """
    # Check multiple locations for the icon
    potential_paths = []
    
    # If running in PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_dir = Path(sys._MEIPASS)
        exe_dir = Path(sys.executable).parent
        
        potential_paths.extend([
            base_dir / "dualgpuopt" / "resources" / "icon.png",
            base_dir / "dualgpuopt" / "resources" / "icon.ico",
            base_dir / "resources" / "icon.png",
            base_dir / "resources" / "icon.ico",
            exe_dir / "dualgpuopt" / "resources" / "icon.png",
            exe_dir / "dualgpuopt" / "resources" / "icon.ico",
            exe_dir / "resources" / "icon.png",
            exe_dir / "resources" / "icon.ico",
            exe_dir / "icon.png",
            exe_dir / "icon.ico"
        ])
    else:
        # Running in development mode
        current_dir = Path(__file__).parent
        root_dir = current_dir.parent.parent
        
        potential_paths.extend([
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
            Path("icon.ico")
        ])
    
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
    
    # Check if ttkthemes is available, use ThemedTk if it is
    try:
        from ttkthemes import ThemedTk
        root = ThemedTk(theme="equilux")
    except ImportError:
        logger.info("ttkthemes not available, using standard Tk")
        root = tk.Tk()
    
    root.title("DualGPUOptimizer")
    root.geometry("800x600")
    
    # Set application icon
    try:
        icon_path = find_icon()
        if icon_path:
            # Use PhotoImage for PNG or TkImage for ICO
            if icon_path.suffix.lower() == '.png':
                icon = tk.PhotoImage(file=str(icon_path))
                root.iconphoto(True, icon)
            elif icon_path.suffix.lower() == '.ico' and not getattr(sys, 'frozen', False):
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
                (name for name, colors in theme.AVAILABLE_THEMES.items() 
                 if colors == theme.current_theme),
                "dark_purple"
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