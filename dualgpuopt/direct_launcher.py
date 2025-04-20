"""
Direct launcher for DualGPUOptimizer

Provides a simplified entry point with robust dependency handling
"""
import os
import sys
import logging
import tkinter as tk
from pathlib import Path
import importlib.util
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path("logs") / "direct_launcher.log", mode='w'),
    ]
)

logger = logging.getLogger("DualGPUOpt.DirectLauncher")

def create_log_directory():
    """Create the logs directory if it doesn't exist"""
    log_dir = Path("logs")
    if not log_dir.exists():
        log_dir.mkdir(parents=True)
        logger.info(f"Created log directory: {log_dir.absolute()}")

def import_or_mock(module_path: str, mock_obj: Any = None) -> Any:
    """Import a module or return a mock object if it can't be imported
    
    Args:
        module_path: The module path to import
        mock_obj: The mock object to return if import fails
        
    Returns:
        The imported module or mock object
    """
    try:
        return importlib.import_module(module_path)
    except ImportError as e:
        logger.warning(f"Failed to import {module_path}: {e}")
        return mock_obj

def is_direct_app_available() -> bool:
    """Check if run_direct_app.py is available
    
    Returns:
        True if run_direct_app.py is available, False otherwise
    """
    try:
        run_direct_app_path = Path("run_direct_app.py")
        return run_direct_app_path.exists()
    except Exception as e:
        logger.warning(f"Error checking for run_direct_app.py: {e}")
        return False

def run_direct_app(**kwargs):
    """Run the direct application
    
    This function tries to use the run_direct_app.py file if available,
    or falls back to a minimal UI with the most essential features.
    
    Args:
        **kwargs: Additional arguments to pass to the application
    """
    logger.info("Starting DualGPUOptimizer via direct launcher")
    create_log_directory()
    
    # Try to import our dependency manager first
    dependency_manager = import_or_mock("dualgpuopt.dependency_manager", None)
    if dependency_manager:
        logger.info("Using dependency manager for imports")
        dependency_manager.initialize_dependency_status()
        
        # Check required dependencies
        core_available, critical_missing = dependency_manager.verify_core_dependencies()
        if not core_available:
            logger.error(f"Critical dependencies missing: {', '.join(critical_missing)}")
            show_dependency_error(critical_missing)
            return
        
        # Use dynamic importers
        ttk = dependency_manager.DynamicImporter.import_ui()
        gpu_compat = dependency_manager.DynamicImporter.import_gpu_compat()
        telemetry = dependency_manager.DynamicImporter.import_telemetry()
        dashboard = dependency_manager.DynamicImporter.import_dashboard()
        optimizer = dependency_manager.DynamicImporter.import_optimizer()
    else:
        logger.warning("Dependency manager not available, using basic imports")
        # Basic dependency checks
        try:
            import tkinter as tk
            from tkinter import ttk
        except ImportError:
            logger.error("tkinter is required but not installed")
            show_dependency_error(["tkinter"])
            return
            
        # Set mock mode to True for safer operation without proper dependencies
        gpu_compat = {
            "is_mock_mode": lambda: True,
            "set_mock_mode": lambda enabled=True: None,
            "generate_mock_gpus": lambda count=2: [
                {"id": 0, "name": "Mock GPU 0", "mem_total": 24576, "mem_used": 8192, "util": 45},
                {"id": 1, "name": "Mock GPU 1", "mem_total": 12288, "mem_used": 10240, "util": 85}
            ]
        }
        telemetry = {"available": False}
        dashboard = {"available": False}
        optimizer = {"available": False}
    
    # Check if the full run_direct_app.py is available
    if is_direct_app_available():
        logger.info("Found run_direct_app.py, using it for launch")
        try:
            # Add the current directory to sys.path if not already there
            current_dir = str(Path.cwd())
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            
            # Import the run_direct_app module
            import run_direct_app
            
            # If it has a main function, call it
            if hasattr(run_direct_app, "main"):
                run_direct_app.main()
            else:
                # Otherwise assume the import itself ran the app
                pass
            
            return
        except Exception as e:
            logger.error(f"Error running direct app: {e}", exc_info=True)
            logger.info("Falling back to built-in minimal UI")
    
    # If run_direct_app.py isn't available or failed, use our minimal UI
    logger.info("Using built-in minimal UI")
    run_minimal_ui(ttk, gpu_compat, telemetry, dashboard, optimizer)

def show_dependency_error(missing_deps: list):
    """Show an error dialog for missing dependencies
    
    Args:
        missing_deps: List of missing dependencies
    """
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()
        
        missing_text = ", ".join(missing_deps)
        messagebox.showerror(
            "Missing Dependencies",
            f"The following required dependencies are missing:\n\n{missing_text}\n\n"
            f"Please install them and try again.\n\n"
            f"Run 'python -m dualgpuopt --install-deps' to install."
        )
        
        root.destroy()
    except Exception as e:
        # If we can't even show a GUI error, fall back to console
        logger.error(f"Missing dependencies: {missing_deps}")
        logger.error(f"Please install them and try again: python -m dualgpuopt --install-deps")
        logger.error(f"Error showing GUI error: {e}")

def run_minimal_ui(ttk, gpu_compat, telemetry, dashboard, optimizer):
    """Run a minimal UI with available components
    
    Args:
        ttk: The ttk module to use
        gpu_compat: The GPU compatibility module
        telemetry: The telemetry module
        dashboard: The dashboard module
        optimizer: The optimizer module
    """
    # Import required tkinter modules
    import tkinter as tk
    
    # Enable mock mode for safe operation
    if hasattr(gpu_compat, "set_mock_mode"):
        gpu_compat["set_mock_mode"](True)
        logger.info("Mock GPU mode enabled for minimal UI")
    
    # Create the main window
    root = tk.Tk()
    root.title("DualGPUOptimizer - Minimal UI")
    root.geometry("800x600")
    
    # Try to set an icon if available
    try:
        icon_path = Path("dualgpuopt") / "resources" / "icon.png"
        if icon_path.exists():
            icon = tk.PhotoImage(file=str(icon_path))
            root.iconphoto(True, icon)
    except Exception as e:
        logger.warning(f"Could not set application icon: {e}")
    
    # Create a notebook for tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create the dashboard tab
    dashboard_frame = ttk.Frame(notebook)
    notebook.add(dashboard_frame, text="Dashboard")
    
    # Check if we can use the real dashboard
    dashboard_available = dashboard.get("available", False) if dashboard else False
    if dashboard_available and dashboard.get("DashboardView"):
        try:
            dashboard_view = dashboard["DashboardView"](dashboard_frame)
            dashboard_view.pack(fill="both", expand=True)
            logger.info("Using real dashboard component")
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            dashboard_available = False
    
    # If real dashboard not available, create a basic GPU info display
    if not dashboard_available:
        logger.info("Using basic GPU info display")
        create_basic_dashboard(dashboard_frame, gpu_compat)
    
    # Create the optimizer tab
    optimizer_frame = ttk.Frame(notebook)
    notebook.add(optimizer_frame, text="Optimizer")
    
    # Check if we can use the real optimizer
    optimizer_available = optimizer.get("available", False) if optimizer else False
    if optimizer_available and optimizer.get("OptimizerTab"):
        try:
            optimizer_tab = optimizer["OptimizerTab"](optimizer_frame)
            optimizer_tab.pack(fill="both", expand=True)
            logger.info("Using real optimizer component")
        except Exception as e:
            logger.error(f"Error creating optimizer: {e}")
            optimizer_available = False
    
    # If real optimizer not available, create a basic optimizer UI
    if not optimizer_available:
        logger.info("Using basic optimizer UI")
        create_basic_optimizer(optimizer_frame)
    
    # Create an info tab with dependency information
    info_frame = ttk.Frame(notebook)
    notebook.add(info_frame, text="Information")
    create_info_tab(info_frame)
    
    # Add a status bar
    status_bar = ttk.Frame(root, relief="sunken", borderwidth=1)
    status_bar.pack(side="bottom", fill="x")
    
    status_label = ttk.Label(
        status_bar,
        text="Running in minimal UI mode - Limited functionality",
        anchor="w",
        padding=(10, 5)
    )
    status_label.pack(side="left")
    
    # Start the main loop
    root.mainloop()

def create_basic_dashboard(parent, gpu_compat):
    """Create a basic dashboard with GPU information
    
    Args:
        parent: The parent widget
        gpu_compat: The GPU compatibility module
    """
    # Create a label frame for GPU info
    gpu_frame = ttk.LabelFrame(parent, text="GPU Information")
    gpu_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Get mock GPU data
    gpus = gpu_compat["generate_mock_gpus"](2)
    
    # Display each GPU
    for i, gpu in enumerate(gpus):
        # GPU header
        ttk.Label(
            gpu_frame,
            text=f"GPU {i}: {gpu['name']}",
            font=("TkDefaultFont", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(10 if i == 0 else 20, 5))
        
        # Memory usage
        mem_used = gpu["mem_used"]
        mem_total = gpu["mem_total"]
        mem_percent = int((mem_used / mem_total) * 100)
        
        ttk.Label(
            gpu_frame,
            text=f"Memory: {mem_used}MB / {mem_total}MB ({mem_percent}%)"
        ).pack(anchor="w", padx=20, pady=2)
        
        # Create progress bar for memory
        mem_bar = ttk.Progressbar(
            gpu_frame,
            value=mem_percent,
            maximum=100,
            length=300
        )
        mem_bar.pack(anchor="w", padx=20, pady=(0, 5))
        
        # GPU utilization
        ttk.Label(
            gpu_frame,
            text=f"Utilization: {gpu['util']}%"
        ).pack(anchor="w", padx=20, pady=2)
        
        # Create progress bar for utilization
        util_bar = ttk.Progressbar(
            gpu_frame,
            value=gpu['util'],
            maximum=100, 
            length=300
        )
        util_bar.pack(anchor="w", padx=20, pady=(0, 5))
        
        # Add mock temperature and power (not in the original mock data)
        ttk.Label(
            gpu_frame,
            text=f"Temperature: 65°C"
        ).pack(anchor="w", padx=20, pady=2)
        
        ttk.Label(
            gpu_frame,
            text=f"Power: 150W / 300W"
        ).pack(anchor="w", padx=20, pady=2)
    
    # Add note about mock data
    note_frame = ttk.Frame(parent)
    note_frame.pack(fill="x", padx=10, pady=10)
    
    ttk.Label(
        note_frame,
        text="Note: Using mock GPU data. Install pynvml for real GPU monitoring.",
        font=("TkDefaultFont", 10, "italic"),
        foreground="gray"
    ).pack(anchor="w")

def create_basic_optimizer(parent):
    """Create a basic optimizer UI
    
    Args:
        parent: The parent widget
    """
    # Create a label frame for the optimizer
    optimizer_frame = ttk.LabelFrame(parent, text="GPU Split Optimizer")
    optimizer_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Message about optimizer functionality
    ttk.Label(
        optimizer_frame,
        text="The GPU Split Optimizer functionality is not available in minimal UI mode.",
        font=("TkDefaultFont", 12)
    ).pack(pady=20)
    
    ttk.Label(
        optimizer_frame,
        text="This component would calculate optimal GPU split configurations\nfor running large language models across multiple GPUs.",
        justify="center"
    ).pack(pady=10)
    
    # Sample configuration
    sample_frame = ttk.LabelFrame(optimizer_frame, text="Sample Split Configuration")
    sample_frame.pack(padx=20, pady=20, fill="x")
    
    ttk.Label(sample_frame, text="Tensor Parallel Size:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
    ttk.Label(sample_frame, text="2 GPUs").grid(row=0, column=1, sticky="w", padx=10, pady=5)
    
    ttk.Label(sample_frame, text="GPU Split Ratio:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
    ttk.Label(sample_frame, text="0.67, 0.33").grid(row=1, column=1, sticky="w", padx=10, pady=5)
    
    ttk.Label(sample_frame, text="Context Length:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
    ttk.Label(sample_frame, text="4096 tokens").grid(row=2, column=1, sticky="w", padx=10, pady=5)
    
    # Installation instructions
    install_frame = ttk.Frame(optimizer_frame)
    install_frame.pack(pady=20, fill="x")
    
    ttk.Label(
        install_frame,
        text="To enable this functionality, install the required dependencies:",
        font=("TkDefaultFont", 10, "italic")
    ).pack(anchor="w", padx=20)
    
    # Code frame with dependencies
    code_frame = ttk.Frame(optimizer_frame, relief="sunken", borderwidth=1)
    code_frame.pack(padx=30, pady=10, fill="x")
    
    ttk.Label(
        code_frame,
        text="pip install numpy pynvml ttkbootstrap",
        font=("Courier", 10),
        justify="left"
    ).pack(padx=10, pady=10, anchor="w")

def create_info_tab(parent):
    """Create an information tab with dependency status
    
    Args:
        parent: The parent widget
    """
    # Create a frame for dependency info
    info_frame = ttk.Frame(parent)
    info_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Add header
    ttk.Label(
        info_frame,
        text="DualGPUOptimizer Information",
        font=("TkDefaultFont", 16, "bold")
    ).pack(anchor="w", pady=(0, 10))
    
    # Python version
    import platform
    py_version = platform.python_version()
    ttk.Label(
        info_frame,
        text=f"Python Version: {py_version}",
        font=("TkDefaultFont", 12)
    ).pack(anchor="w", pady=5)
    
    # Dependency status
    ttk.Label(
        info_frame,
        text="Dependency Status:",
        font=("TkDefaultFont", 12, "bold")
    ).pack(anchor="w", pady=(10, 5))
    
    # Check common dependencies
    dependencies = [
        ("tkinter", "Base UI framework", True),  # tkinter is available since we're running
        ("pynvml", "NVIDIA GPU monitoring", check_dependency("pynvml")),
        ("numpy", "Optimization algorithms", check_dependency("numpy")),
        ("ttkbootstrap", "Enhanced UI appearance", check_dependency("ttkbootstrap")),
        ("requests", "API communication", check_dependency("requests")),
        ("sseclient", "Streaming events", check_dependency("sseclient")),
        ("torch", "PyTorch for advanced features", check_dependency("torch")),
    ]
    
    # Create a frame for the dependencies
    dep_frame = ttk.Frame(info_frame)
    dep_frame.pack(fill="x", pady=5)
    
    # Add headers
    ttk.Label(dep_frame, text="Dependency", font=("TkDefaultFont", 10, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
    ttk.Label(dep_frame, text="Description", font=("TkDefaultFont", 10, "bold")).grid(row=0, column=1, padx=10, pady=5, sticky="w")
    ttk.Label(dep_frame, text="Status", font=("TkDefaultFont", 10, "bold")).grid(row=0, column=2, padx=10, pady=5, sticky="w")
    
    # Add separator
    ttk.Separator(dep_frame, orient="horizontal").grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
    
    # Add each dependency
    for i, (name, desc, available) in enumerate(dependencies, 2):
        ttk.Label(dep_frame, text=name).grid(row=i, column=0, padx=10, pady=2, sticky="w")
        ttk.Label(dep_frame, text=desc).grid(row=i, column=1, padx=10, pady=2, sticky="w")
        
        status_text = "Available ✓" if available else "Missing ✗"
        status_color = "dark green" if available else "red"
        
        status_label = ttk.Label(dep_frame, text=status_text, foreground=status_color)
        status_label.grid(row=i, column=2, padx=10, pady=2, sticky="w")
    
    # Installation instructions
    ttk.Label(
        info_frame,
        text="Installation Instructions:",
        font=("TkDefaultFont", 12, "bold")
    ).pack(anchor="w", pady=(20, 5))
    
    ttk.Label(
        info_frame,
        text="To install missing dependencies, run:",
        font=("TkDefaultFont", 10)
    ).pack(anchor="w", pady=(0, 5))
    
    # Command label
    command_frame = ttk.Frame(info_frame, relief="sunken", borderwidth=1)
    command_frame.pack(fill="x", padx=20, pady=5)
    
    ttk.Label(
        command_frame,
        text="python -m dualgpuopt --install-deps",
        font=("Courier", 10),
        padding=(10, 5)
    ).pack(anchor="w")
    
    # Version information
    ttk.Label(
        info_frame,
        text="Version Information:",
        font=("TkDefaultFont", 12, "bold")
    ).pack(anchor="w", pady=(20, 5))
    
    # Try to get version
    try:
        from dualgpuopt import __version__
        version = __version__
    except (ImportError, AttributeError):
        version = "Unknown"
    
    ttk.Label(
        info_frame,
        text=f"DualGPUOptimizer Version: {version}",
        font=("TkDefaultFont", 10)
    ).pack(anchor="w", pady=2)
    
    # Add run date
    from datetime import datetime
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    ttk.Label(
        info_frame,
        text=f"Run Date: {run_date}",
        font=("TkDefaultFont", 10)
    ).pack(anchor="w", pady=2)

def check_dependency(name: str) -> bool:
    """Check if a dependency is installed
    
    Args:
        name: Name of the dependency
        
    Returns:
        True if installed, False otherwise
    """
    if name == "tkinter":
        try:
            import tkinter
            return True
        except ImportError:
            return False
    else:
        spec = importlib.util.find_spec(name)
        return spec is not None

if __name__ == "__main__":
    run_direct_app() 