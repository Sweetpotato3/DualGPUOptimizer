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
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dualgpuopt.log')
    ]
)

logger = logging.getLogger("DualGPUOpt.MainApp")

# Import our components
from . import dashboard
from . import optimizer_tab
from . import launcher
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
        
        # Header with status
        header_frame = ttk.Frame(self, padding=10)
        header_frame.grid(row=0, column=0, sticky="ew")
        
        title_label = ttk.Label(header_frame, text="Dual GPU Optimizer", font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        self.status_var = tk.StringVar(value="Status: Ready")
        status_label = ttk.Label(header_frame, textvariable=self.status_var, foreground="green")
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


def run():
    """Main entry point for the application"""
    root = tk.Tk()
    root.title("DualGPUOptimizer")
    root.geometry("800x600")
    
    # Set application icon
    try:
        # Look for icon in various locations
        icon_paths = [
            Path("assets/icon.png"),
            Path(__file__).parent / "assets" / "icon.png",
            Path(__file__).parent.parent.parent / "assets" / "icon.png"
        ]
        
        for icon_path in icon_paths:
            if icon_path.exists():
                icon = tk.PhotoImage(file=str(icon_path))
                root.iconphoto(True, icon)
                break
    except Exception as e:
        logger.warning(f"Failed to load application icon: {e}")
    
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