"""
Main application module for the DualGPUOptimizer GUI.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import queue
import sys
from typing import Dict, List, Optional, Any

try:
    from ttkthemes import ThemedTk
    TTKTHEMES_AVAILABLE = True
except ImportError:
    TTKTHEMES_AVAILABLE = False

from dualgpuopt import gpu_info, configio, telemetry
from dualgpuopt.tray import init_tray
from dualgpuopt.gui.theme import apply_theme, update_widgets_theme, generate_colors
from dualgpuopt.gui.dashboard import GpuDashboard
from dualgpuopt.gui.optimizer_tab import OptimizerTab
from dualgpuopt.gui.launcher import LauncherTab
from dualgpuopt.gui.settings import SettingsTab


class DualGpuApp(ttk.Frame):
    """Main application class for the DualGPUOptimizer."""
    
    def __init__(self, master: tk.Tk) -> None:
        """
        Initialize the main application.
        
        Args:
            master: The Tk root window
        """
        # Load config before initializing UI
        self.cfg = configio.load_cfg()
        
        # Convert root window to ThemedTk if available
        if TTKTHEMES_AVAILABLE and not isinstance(master, ThemedTk):
            try:
                # Store attributes from current master
                geometry = master.geometry()
                title = master.title()
                
                # Create new ThemedTk window
                new_master = ThemedTk(theme=self.cfg.get("ttk_theme", "equilux"))
                new_master.geometry(geometry)
                new_master.title(title)
                
                # Replace master
                master.destroy()
                master = new_master
            except Exception as e:
                # Fall back to regular Tk if conversion fails
                print(f"Warning: Failed to initialize ThemedTk: {e}")
        
        # Initialize frame
        super().__init__(master)
        self.master = master
        self.logger = logging.getLogger("dualgpuopt.gui")
        
        try:
            # Apply theme to root window before creating widgets
            self._apply_theme(master)
            
            self.model_var = tk.StringVar(value=self.cfg.get("last_model", "dolphin-2.5-mixtral-8x7b.Q3_K_M.gguf"))
            self.ctx_var = tk.IntVar(value=self.cfg.get("context_size", 65536))
            self.tele_q = None
            self.tele_hist = []  # List of GPU load tuples
            
            # Detect GPUs
            self.gpus = gpu_info.probe_gpus()
            if len(self.gpus) < 2:
                self.show_error("Need ≥ 2 GPUs for optimal operation")
                # Continue anyway for now, but show a warning
            
            # Generate colors for GPU visualization
            self.gpu_colors = generate_colors(len(self.gpus))

            self.init_ui()
            
            # Setup telemetry
            self.tele_q = telemetry.start_stream(1.0)
            self.after(1000, self._tick_chart)
            
            # Setup tray
            init_tray(self)
        except Exception as err:
            self.show_error(f"Error initializing application: {err}")
    
    def show_error(self, message: str, title: str = "Error") -> None:
        """
        Show an error dialog and log the error.
        
        Args:
            message: Error message to display
            title: Dialog title
        """
        self.logger.error(message)
        messagebox.showerror(title, message)
        
        # Add a simple interface with mock mode option if this is a GPU detection error
        if "GPU detection failed" in message or "NVML" in message:
            frame = ttk.Frame(self)
            frame.pack(padx=20, pady=20, fill="both", expand=True)
            
            ttk.Label(frame, text="GPU detection failed. Would you like to:").pack(pady=10)
            
            # Mock mode button
            mock_btn = ttk.Button(frame, text="Launch in Mock Mode", 
                               command=self.enable_mock_mode)
            mock_btn.pack(pady=10)
            
            # Exit button
            exit_btn = ttk.Button(frame, text="Exit", 
                               command=self.master.destroy)
            exit_btn.pack(pady=10)
            
    def enable_mock_mode(self) -> None:
        """Enable mock mode and restart the application."""
        import os
        
        # Set environment variable for mock mode
        os.environ["DGPUOPT_MOCK_GPUS"] = "1"
        
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
        except Exception as e:
            self.show_error(f"Failed to initialize even in mock mode: {e}")
            self.master.destroy()

    def _apply_theme(self, root: tk.Tk) -> None:
        """
        Apply selected theme to the application.
        
        Args:
            root: The root Tk window
        """
        theme_name = self.cfg.get("theme", "dark")
        ttk_theme = self.cfg.get("ttk_theme", "")
        
        # Apply theme
        self.active_theme = apply_theme(root, theme_name, self.logger)
        self.chart_bg = self.active_theme.get("chart_bg", "#202020")
    
    def _theme_changed(self, theme_name: str, ttk_theme: str) -> None:
        """
        Handle theme change from settings.
        
        Args:
            theme_name: New theme name
            ttk_theme: New TTK theme name
        """
        # Apply the theme
        self.active_theme = apply_theme(self.master, theme_name, self.logger)
        
        # Update all widgets
        update_widgets_theme(self, self.active_theme)
        
        # Save to config (already done in settings tab)
        self.chart_bg = self.active_theme.get("chart_bg", "#202020")
        
        # Update the chart canvas background
        if hasattr(self, "dashboard") and hasattr(self.dashboard, "chart_canvas"):
            self.dashboard.chart_canvas.config(bg=self.chart_bg)

    def init_ui(self) -> None:
        """Initialize the user interface."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Use notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        
        # Create optimizer tab
        self.optimizer_tab = OptimizerTab(self.notebook, self.gpus)
        self.notebook.add(self.optimizer_tab, text="Optimizer")
        
        # Create launcher tab
        self.launcher_tab = LauncherTab(self.notebook, self.gpus)
        self.notebook.add(self.launcher_tab, text="Launcher")
        
        # Create dashboard tab
        self.dashboard = GpuDashboard(self.notebook, self.gpu_colors)
        self.notebook.add(self.dashboard, text="GPU Dashboard")
        
        # Initialize dashboard with GPU list
        self.dashboard.initialize_gpu_metrics(self.gpus)
        
        # Create settings tab
        self.settings_tab = SettingsTab(
            self.notebook, 
            self.gpus, 
            self.cfg,
            self._theme_changed
        )
        self.notebook.add(self.settings_tab, text="Settings")
        
        # Status bar
        status_frame = ttk.Frame(self)
        status_frame.grid(row=1, column=0, sticky="ew")
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor="e")
        status_label.grid(row=0, column=0, sticky="e", padx=8, pady=4)
    
    def _tick_chart(self) -> None:
        """Update the dashboard with the latest telemetry data."""
        try:
            # Check if there's telemetry data in the queue
            if self.tele_q and not self.tele_q.empty():
                # Get the latest telemetry
                telemetry = self.tele_q.get_nowait()
                
                # Update the dashboard
                if hasattr(self, "dashboard"):
                    self.dashboard.update(telemetry)
                
                # Save the telemetry for history
                self.tele_hist.append(telemetry)
                
                # Limit history to 60 samples
                if len(self.tele_hist) > 60:
                    self.tele_hist = self.tele_hist[-60:]
        except queue.Empty:
            pass
        except Exception as e:
            self.logger.error(f"Error updating telemetry: {e}")
        
        # Schedule the next update
        self.after(1000, self._tick_chart)


def run_app() -> None:
    """Run the DualGPUOptimizer application."""
    root = tk.Tk() if not TTKTHEMES_AVAILABLE else ThemedTk()
    root.title("DualGPUOptimizer")
    root.geometry("800x600")
    
    # Increase font size slightly on high-DPI displays
    if hasattr(root, "winfo_fpixels"):
        dpi = root.winfo_fpixels('1i') / 72.0
        if dpi > 1.5:  # High-DPI display
            default_font = ("Segoe UI", int(9 * dpi)) if sys.platform == "win32" else ("Helvetica", int(10 * dpi))
            root.option_add("*Font", default_font)
    
    app = DualGpuApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root))
    root.mainloop()


def on_close(root: tk.Tk) -> None:
    """
    Handle window close event.
    
    Args:
        root: The root Tk window
    """
    # Clean up resources
    root.destroy() 