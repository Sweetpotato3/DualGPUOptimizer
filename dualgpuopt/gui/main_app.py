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
        
        # Configure grid layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Apply theme to parent window
        theme.apply_custom_styling(parent)
        
        # Header with status
        header_frame = ttk.Frame(self, padding=10)
        header_frame.grid(row=0, column=0, sticky="ew")
        
        title_label = ttk.Label(header_frame, text="Dual GPU Optimizer", font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        self.status_var = tk.StringVar(value="Status: Ready")
        status_label = ttk.Label(header_frame, textvariable=self.status_var, foreground=theme.THEME_DARK_PURPLE["success"])
        status_label.pack(side=tk.RIGHT)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Add dashboard tab
        self.dashboard_tab = dashboard.DashboardView(self.notebook)
        self.notebook.add(self.dashboard_tab, text="Dashboard")
        
        # Add optimizer tab
        self.optimizer_tab = optimizer_tab.OptimizerTab(self.notebook)
        self.notebook.add(self.optimizer_tab, text="Optimizer")
        
        # Add launcher tab
        self.launcher_tab = launcher.LauncherTab(self.notebook)
        self.notebook.add(self.launcher_tab, text="Launcher")
        
        # Status bar
        status_frame = ttk.Frame(self, relief="sunken", padding=(5, 2))
        status_frame.grid(row=2, column=0, sticky="ew")
        
        # GPU count indicator
        self.gpu_count_var = tk.StringVar(value="GPUs: Detecting...")
        gpu_count_label = ttk.Label(status_frame, textvariable=self.gpu_count_var)
        gpu_count_label.pack(side=tk.LEFT)
        
        # Version
        version_label = ttk.Label(status_frame, text="v0.2.0")
        version_label.pack(side=tk.RIGHT)
        
        # Start GPU detection
        self.detect_gpus()
    
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
    
    # Apply theme
    theme.apply_theme(root)
    
    # Create and configure main application
    app = MainApplication(root)
    app.pack(fill=tk.BOTH, expand=True)
    
    # Handle window close
    def on_closing():
        app.destroy()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the main loop
    root.mainloop()


if __name__ == "__main__":
    run() 