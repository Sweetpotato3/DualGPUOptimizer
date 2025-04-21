"""
Modern UI implementation for DualGPUOptimizer
Uses ttkbootstrap for a contemporary appearance with neon accents
"""

import sys
import time
import logging
import threading
from pathlib import Path
from typing import List

import tkinter as tk
from tkinter import ttk, messagebox

# Import ttkbootstrap for modern UI elements
try:
    import ttkbootstrap as ttk

    # Check if Window class is available (newer versions of ttkbootstrap)
    if hasattr(ttk, 'Window'):
        TTKBOOTSTRAP_WINDOW_AVAILABLE = True
    else:
        TTKBOOTSTRAP_WINDOW_AVAILABLE = False

    TTKBOOTSTRAP_AVAILABLE = True
except ImportError:
    import tkinter.ttk as ttk
    TTKBOOTSTRAP_AVAILABLE = False
    TTKBOOTSTRAP_WINDOW_AVAILABLE = False

# Compatibility class for environments without ttk.Window
class TtkWindow:
    """Compatibility wrapper for environments where ttkbootstrap.Window is not available"""
    def __init__(self, title="", themename="", size=(800, 600), resizable=(True, True), alpha=1.0, **kwargs):
        """Create a tkinter root window with ttkbootstrap-like initialization"""
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{size[0]}x{size[1]}")
        self.root.resizable(*resizable)

        # Apply themename if ttkbootstrap is available
        if TTKBOOTSTRAP_AVAILABLE and hasattr(ttk, 'Style'):
            self.style = ttk.Style()
            if hasattr(self.style, 'theme_use'):
                try:
                    self.style.theme_use(themename)
                except Exception as e:
                    logger.warning(f"Could not set theme {themename}: {e}")

    def __getattr__(self, name):
        """Delegate attribute access to the root window"""
        return getattr(self.root, name)

    def pack(self, *args, **kwargs):
        """Pack this window (no-op for root window)"""

    def destroy(self):
        """Destroy the root window"""
        self.root.destroy()

# Import components - some may be unavailable in certain environments
try:
    from dualgpuopt.gui.dashboard import DashboardView
    from dualgpuopt.gui.optimizer_tab import OptimizerTab
    from dualgpuopt.gui.launcher import LauncherTab
    from dualgpuopt.chat_tab import ChatTab
    CHAT_AVAILABLE = True
except ImportError:
    CHAT_AVAILABLE = False

# Initialize logger
logger = logging.getLogger("DualGPUOpt.ModernUI")

# Import GPU detection functionality
try:
    from dualgpuopt.gpu_info import get_gpu_info, GPU
except ImportError as e:
    logger.error(f"Failed to import GPU detection module: {e}")

    # Mock GPU info for development without GPU detection
    class GPU:
        def __init__(self, name: str = "Mock GPU", memory: int = 8192):
            self.name = name
            self.mem_total = memory

    def get_gpu_info() -> List[GPU]:
        return [GPU({"name": "Mock GPU 1", "mem_total": 8192}),
                GPU({"name": "Mock GPU 2", "mem_total": 10240})]

# Select appropriate window class
if TTKBOOTSTRAP_WINDOW_AVAILABLE:
    logger.info("Using ttkbootstrap Window class")
    WindowClass = ttk.Window
else:
    logger.info("Using compatibility Window class")
    WindowClass = TtkWindow

class ModernApp(WindowClass):
    """Modern application window for DualGPUOptimizer"""

    def __init__(self, master=None, **kwargs):
        """Initialize modern UI window with ttkbootstrap styling"""

        # Get theme from kwargs or use default
        theme = kwargs.pop('theme', 'cyborg')

        # Initialize window
        super().__init__(
            title="DualGPUOptimizer",
            themename=theme,
            size=(1200, 800),
            resizable=(True, True),
            alpha=1.0,
            **kwargs
        )

        # For compatibility layer, we need to get the actual window object
        if not TTKBOOTSTRAP_WINDOW_AVAILABLE:
            self.window = self.root
        else:
            self.window = self

        # Set window icon if method exists
        if hasattr(self, 'iconbitmap'):
            self.iconbitmap(default=self._find_application_icon())

        # Set initial window size and position
        self.center_window(1200, 800)

        # Initialize UI components
        self.tabs = {}
        self.current_tab = None

        # Create main container - use correct parent
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill='both', expand=True)

        # Create sidebar for navigation
        self.setup_sidebar()

        # Create content area
        self.content_frame = ttk.Frame(self.main_frame, padding=10)
        self.content_frame.pack(side='right', fill='both', expand=True)

        # Add status bar at the bottom
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            self.window,
            textvariable=self.status_var,
            relief='sunken',
            anchor='w',
            padding=(5, 2)
        )
        self.status_bar.pack(side='bottom', fill='x')

        # Initialize GPU detection
        self.setup_gpu_detection()

        # Setup close handlers
        if hasattr(self, 'protocol'):
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
        else:
            self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start monitoring thread
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self.update_status_periodically)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

        # Show dashboard by default
        self.show_dashboard()

        logger.info("Modern UI initialized successfully")

    def setup_sidebar(self):
        """Create sidebar with navigation buttons"""
        self.sidebar = ttk.Frame(self.main_frame, bootstyle='dark')
        self.sidebar.pack(side='left', fill='y', padx=0, pady=0)

        # App title in sidebar
        title_frame = ttk.Frame(self.sidebar, bootstyle='dark')
        title_frame.pack(fill='x', padx=10, pady=15)

        app_title = ttk.Label(
            title_frame,
            text="DualGPU\nOptimizer",
            font=('Segoe UI', 16, 'bold'),
            bootstyle='inverse-dark',
            anchor='center'
        )
        app_title.pack(pady=5)

        # Navigation buttons
        self.nav_buttons = {}

        # Dashboard button
        self.nav_buttons['dashboard'] = self.create_nav_button(
            "Dashboard",
            self.show_dashboard,
            "Realtime GPU monitoring"
        )

        # Optimizer button
        self.nav_buttons['optimizer'] = self.create_nav_button(
            "Optimizer",
            self.show_optimizer,
            "Configure GPU splits"
        )

        # Launcher button
        self.nav_buttons['launcher'] = self.create_nav_button(
            "Launcher",
            self.show_launcher,
            "Run models with optimization"
        )

        # Chat button (if available)
        if CHAT_AVAILABLE:
            self.nav_buttons['chat'] = self.create_nav_button(
                "Chat",
                self.show_chat,
                "Interactive chat interface"
            )

        # Settings button
        self.nav_buttons['settings'] = self.create_nav_button(
            "Settings",
            self.show_settings,
            "Configure application settings"
        )

        # Version info at bottom
        version_frame = ttk.Frame(self.sidebar, bootstyle='dark')
        version_frame.pack(side='bottom', fill='x', padx=10, pady=15)

        version_label = ttk.Label(
            version_frame,
            text="Version 2.0.0",
            bootstyle='inverse-dark',
            font=('Segoe UI', 9),
            anchor='center'
        )
        version_label.pack(pady=5)

    def create_nav_button(self, text, command, tooltip=None):
        """Create a styled navigation button for the sidebar"""
        btn_frame = ttk.Frame(self.sidebar, bootstyle='dark')
        btn_frame.pack(fill='x', padx=10, pady=5)

        button = ttk.Button(
            btn_frame,
            text=text,
            command=command,
            bootstyle='outline-light',
            width=15
        )
        button.pack(pady=2, padx=5)

        # Add tooltip if provided
        if tooltip and hasattr(ttk, 'Hovertip'):
            ttk.Hovertip(button, tooltip)

        return button

    def setup_gpu_detection(self):
        """Initialize GPU detection"""
        try:
            self.gpus = get_gpu_info()
            if self.gpus:
                logger.info(f"Detected {len(self.gpus)} GPUs")
                self.status_var.set(f"Detected {len(self.gpus)} GPUs")
            else:
                logger.warning("No GPUs detected")
                self.status_var.set("No GPUs detected")
                messagebox.showwarning(
                    "GPU Detection",
                    "No NVIDIA GPUs detected. Some features may be limited."
                )
        except Exception as e:
            logger.error(f"Error detecting GPUs: {e}")
            self.gpus = []

    def show_dashboard(self):
        """Show dashboard tab"""
        self.clear_content()

        if 'dashboard' not in self.tabs:
            self.tabs['dashboard'] = DashboardView(self.content_frame)
            self.tabs['dashboard'].pack(fill='both', expand=True)
        else:
            self.tabs['dashboard'].pack(fill='both', expand=True)

        self.current_tab = 'dashboard'
        self.highlight_active_nav('dashboard')

    def show_optimizer(self):
        """Show optimizer tab"""
        self.clear_content()

        if 'optimizer' not in self.tabs:
            self.tabs['optimizer'] = OptimizerTab(self.content_frame)
            self.tabs['optimizer'].pack(fill='both', expand=True)
        else:
            self.tabs['optimizer'].pack(fill='both', expand=True)

        self.current_tab = 'optimizer'
        self.highlight_active_nav('optimizer')

    def show_launcher(self):
        """Show launcher tab"""
        self.clear_content()

        if 'launcher' not in self.tabs:
            self.tabs['launcher'] = LauncherTab(self.content_frame)
            self.tabs['launcher'].pack(fill='both', expand=True)
        else:
            self.tabs['launcher'].pack(fill='both', expand=True)

        self.current_tab = 'launcher'
        self.highlight_active_nav('launcher')

    def show_chat(self):
        """Show chat tab if available"""
        if not CHAT_AVAILABLE:
            messagebox.showinfo("Feature Unavailable",
                              "Chat feature is not available in this build.")
            return

        self.clear_content()

        if 'chat' not in self.tabs:
            self.tabs['chat'] = ChatTab(self.content_frame)
            self.tabs['chat'].pack(fill='both', expand=True)
        else:
            self.tabs['chat'].pack(fill='both', expand=True)

        self.current_tab = 'chat'
        self.highlight_active_nav('chat')

    def show_settings(self):
        """Show settings tab"""
        self.clear_content()

        if 'settings' not in self.tabs:
            # Create a simple settings frame for now
            settings_frame = ttk.Frame(self.content_frame)

            # Title
            ttk.Label(
                settings_frame,
                text="Settings",
                font=('Segoe UI', 18, 'bold')
            ).pack(pady=20)

            # Create sections
            self.create_settings_section(settings_frame, "Appearance", [
                ("Theme", self.create_theme_selector),
                ("Scale UI", self.create_scale_selector)
            ])

            self.create_settings_section(settings_frame, "Performance", [
                ("GPU Monitoring Interval", self.create_monitoring_interval),
                ("Enable Advanced Metrics", self.create_advanced_metrics_toggle)
            ])

            # Save button
            ttk.Button(
                settings_frame,
                text="Save Settings",
                bootstyle='success',
                command=self.save_settings
            ).pack(pady=20)

            settings_frame.pack(fill='both', expand=True)
            self.tabs['settings'] = settings_frame
        else:
            self.tabs['settings'].pack(fill='both', expand=True)

        self.current_tab = 'settings'
        self.highlight_active_nav('settings')

    def create_settings_section(self, parent, title, settings):
        """Create a settings section with multiple options"""
        section = ttk.LabelFrame(parent, text=title, padding=15)
        section.pack(fill='x', expand=False, padx=20, pady=10)

        for label, creator_func in settings:
            frame = ttk.Frame(section)
            frame.pack(fill='x', padx=5, pady=5)

            ttk.Label(frame, text=label, width=25).pack(side='left')
            creator_func(frame).pack(side='right', padx=5)

    def create_theme_selector(self, parent):
        """Create theme selection dropdown"""
        themes = ["cyborg", "darkly", "solar", "superhero", "vapor"]
        var = tk.StringVar(value="cyborg")

        dropdown = ttk.Combobox(parent, textvariable=var, values=themes, state="readonly", width=20)
        return dropdown

    def create_scale_selector(self, parent):
        """Create UI scale selector"""
        scales = ["100%", "125%", "150%", "175%", "200%"]
        var = tk.StringVar(value="100%")

        dropdown = ttk.Combobox(parent, textvariable=var, values=scales, state="readonly", width=20)
        return dropdown

    def create_monitoring_interval(self, parent):
        """Create monitoring interval selector"""
        var = tk.IntVar(value=1000)

        scale = ttk.Scale(
            parent,
            from_=500,
            to=5000,
            variable=var,
            length=200,
            orient='horizontal'
        )
        return scale

    def create_advanced_metrics_toggle(self, parent):
        """Create toggle for advanced metrics"""
        var = tk.BooleanVar(value=True)

        toggle = ttk.Checkbutton(
            parent,
            variable=var,
            bootstyle="round-toggle"
        )
        return toggle

    def save_settings(self):
        """Save application settings"""
        messagebox.showinfo("Settings", "Settings saved successfully!")

    def clear_content(self):
        """Clear current content"""
        if self.current_tab and self.current_tab in self.tabs:
            self.tabs[self.current_tab].pack_forget()

    def highlight_active_nav(self, active_tab):
        """Highlight active navigation button"""
        for tab, button in self.nav_buttons.items():
            if tab == active_tab:
                button.configure(bootstyle='success')
            else:
                button.configure(bootstyle='outline-light')

    def update_status_periodically(self):
        """Update status bar with GPU information periodically"""
        while self.monitoring_active:
            if hasattr(self, 'gpus') and self.gpus:
                try:
                    # Get GPU utilization for status bar
                    from dualgpuopt.telemetry import get_gpu_utilization
                    util = get_gpu_utilization()

                    if util:
                        status = "GPUs: " + " | ".join(
                            f"GPU{i}: {u:.1f}%" for i, u in enumerate(util)
                        )
                        self.status_var.set(status)
                except Exception as e:
                    logger.error(f"Error updating GPU status: {e}")

            time.sleep(2)

    def center_window(self, width, height):
        """Center window on screen"""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.geometry(f"{width}x{height}+{x}+{y}")

    def on_closing(self):
        """Handle window closing"""
        self.monitoring_active = False

        # If we have a dashboard with a monitoring thread, stop it
        if 'dashboard' in self.tabs and hasattr(self.tabs['dashboard'], 'stop_monitoring'):
            self.tabs['dashboard'].stop_monitoring()

        self.destroy()

    def _find_application_icon(self) -> str:
        """Find application icon file path"""
        icon_locations = [
            # Look in executable directory
            Path(sys.executable).parent / "icons" / "app_icon.ico",
            # Look in current directory
            Path.cwd() / "icons" / "app_icon.ico",
            # Look in package directory
            Path(__file__).parent / "icons" / "app_icon.ico",
            # Look in bundle directory
            Path(getattr(sys, '_MEIPASS', '.')) / "icons" / "app_icon.ico",
        ]

        for location in icon_locations:
            if location.exists():
                return str(location)

        # Return empty string if icon not found
        return ""

def run_modern_app():
    """Run the modern ttkbootstrap application"""
    try:
        # Configure logging if it hasn't been configured yet
        if not logging.getLogger().handlers:
            logging_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            logging.basicConfig(
                level=logging.INFO,
                format=logging_format
            )

        logger.info("Starting DualGPUOptimizer modern UI")

        # Check if ttkbootstrap is available
        if not TTKBOOTSTRAP_AVAILABLE:
            logger.warning("ttkbootstrap not available, using standard ttk")
            messagebox.showwarning(
                "Missing Component",
                "ttkbootstrap package not found. Using standard UI components instead."
            )

            # Fall back to standard UI
            from dualgpuopt.gui.main_app import run
            return run()

        # Create and run application
        app = ModernApp(theme="cyborg")

        # For compatibility with both window classes
        if TTKBOOTSTRAP_WINDOW_AVAILABLE:
            app.mainloop()
        else:
            app.root.mainloop()

    except Exception as e:
        logger.error(f"Error starting modern UI: {e}", exc_info=True)

        # Show error dialog
        messagebox.showerror(
            "Application Error",
            f"Failed to start DualGPUOptimizer: {e}\n\n"
            "Please check logs for more details."
        )

        # Try to fall back to standard UI
        try:
            from dualgpuopt.gui.main_app import run
            logger.info("Attempting fallback to standard UI")
            run()
        except Exception:
            logger.critical("Failed to launch even fallback UI", exc_info=True)

if __name__ == "__main__":
    run_modern_app()