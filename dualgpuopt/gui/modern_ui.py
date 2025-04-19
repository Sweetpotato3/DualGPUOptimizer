"""
dualgpuopt.gui.modern_ui
Purple themed desktop GUI for DualGPUOptimizer.
"""
from __future__ import annotations
import json, tkinter as tk
from tkinter import messagebox # Import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.widgets import Meter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import queue, threading
import time, random
import logging
import os
from typing import Dict, Optional, Any # Add Optional, Any

try:
    from sseclient import SSEClient
except ImportError:
    # Mock SSEClient for demonstration purposes
    class SSEClient:
        def __init__(self, response):
            self.response = response
        def __iter__(self):
            return self
        def __next__(self):
            class Event:
                def __init__(self):
                    self.data = {"choices": [{"delta": {"content": "..."}}]}
            time.sleep(0.2)
            return Event()

try:
    from ttkbootstrap.toast import ToastNotification
except ImportError:
    # Mock ToastNotification if not available
    class ToastNotification:
        def __init__(self, title, message, duration):
            self.title = title
            self.message = message
            self.duration = duration
        def show_toast(self):
            print(f"Toast: {self.title} - {self.message}")

from dualgpuopt.ui.widgets import GradientProgress, NeonButton
# Import gpu_info to access GPU-related functions
import dualgpuopt.gpu_info as gpu_info
# Import the OptimizerTab
from .optimizer_tab import OptimizerTab
# Import TelemetryService and GPUMetrics
from dualgpuopt.telemetry import TelemetryService, GPUMetrics, get_telemetry_service
# Import the Runner class
from dualgpuopt.runner import Runner

CFG_FILE = Path.home() / ".dualgpuopt" / "ui.json"

# Check multiple possible locations for the icon
ICON_PATH = Path("windowsicongpu.ico")  # Root directory
if not ICON_PATH.exists():
    # Check in dual_gpu_optimizer path
    ICON_PATH = Path("dual_gpu_optimizer/dualgpuopt/assets/windowsicongpu.ico")
    if not ICON_PATH.exists():
        # Check in integrated_app path
        ICON_PATH = Path("integrated_app/dualgpuopt/assets/windowsicongpu.ico")
        if not ICON_PATH.exists():
            # Check in assets directory
            ICON_PATH = Path(__file__).parent.parent / "assets" / "windowsicongpu.ico"
            if not ICON_PATH.exists():
                # Fallback to the original icon
                ICON_PATH = Path(__file__).parent.parent / "assets" / "app_64.png"

logger = logging.getLogger("DualGPUOpt.GUI")

# ---------------- persistence helpers ----------------
def _load_cfg() -> dict:
    try:
        return json.loads(CFG_FILE.read_text())
    except FileNotFoundError:
        return {}

def _save_cfg(data: dict):
    CFG_FILE.parent.mkdir(exist_ok=True)
    CFG_FILE.write_text(json.dumps(data, indent=2))

# ---------------- Main window ------------------------
class ModernApp(ttk.Window):
    """Modern UI main window using ttkbootstrap."""
    
    def __init__(self):
        """Initialize the Modern UI window."""
        super().__init__(themename="superhero")
        self.title("DualGPUOptimizer")
        
        # Try to load the icon, but continue if it fails
        try:
            if ICON_PATH.exists():
                if ICON_PATH.suffix.lower() == '.ico':
                    # For .ico files, we need to use a different approach
                    self.iconbitmap(str(ICON_PATH))
                else:
                    # For .png files, use PhotoImage
                    icon = tk.PhotoImage(file=str(ICON_PATH))
                    self.iconphoto(True, icon)
            else:
                logger.warning(f"Icon file not found: {ICON_PATH}")
        except Exception as e:
            logger.error(f"Failed to load icon: {e}")
        
        self.style.configure(".", font=("Segoe UI", 10))
        
        cfg = _load_cfg()
        if "theme" in cfg:
            self.style.theme_use(cfg["theme"])
        if "win" in cfg:
            self.geometry(cfg["win"])
        
        # Default to real GPU mode
        self.mock_mode = False
        
        # If environment variable is set, respect it (mainly for backwards compatibility)
        if os.environ.get("DGPUOPT_MOCK_GPUS") == "1":
            self.mock_mode = True
            logger.info("Mock GPU mode enabled via environment variable")
            
        # Clear the mock mode environment variable if it exists and we're not in mock mode
        if not self.mock_mode and "DGPUOPT_MOCK_GPUS" in os.environ:
            del os.environ["DGPUOPT_MOCK_GPUS"]
            logger.info("Disabled mock GPU mode (environment variable cleared)")

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind_all("<Control-q>", lambda *_: self.on_close())
        
        self.pool = ThreadPoolExecutor(max_workers=4)
        self.q = queue.Queue()

        # Initialize and start Telemetry Service
        self.telemetry_service = get_telemetry_service() # Use singleton
        self.telemetry_service.use_mock = self.mock_mode # Ensure service knows the mode
        self.telemetry_service.register_callback(self._update_dashboard)
        self.telemetry_service.start()
        logger.info(f"Telemetry service started (mock_mode={self.mock_mode})")

        self.active_runner: Optional[Runner] = None # Track the active runner
        self.gpu_widgets: Dict[int, Dict[str, Any]] = {} # Store dynamically created GPU widgets
        self.dashboard_widgets_created = False # Flag for dynamic creation

        nb = ttk.Notebook(self, bootstyle="dark")
        nb.pack(fill="both", expand=True)
        nb.enable_traversal()

        self._build_tabs(nb)
        self.after(100, self._marquee)  # status reset marquee
        self.after(100, self._poll_queue) # Poll queue for non-telemetry events
        
        # Initial GPU info display relies on telemetry callback now
        # self.after(500, self._refresh_gpu_info) # Removed, handled by telemetry

    # ---------------- Tabs -----------------
    def _build_tabs(self, nb):
        # Optimizer Tab - Store instance for later access
        self.optimizer_tab = OptimizerTab(nb)
        nb.add(self.optimizer_tab, text="Optimizer")

        # Launcher
        launcher = ttk.Frame(nb, padding=12)
        nb.add(launcher, text="Launcher")
        ttk.Label(launcher, text="Model path:").grid(row=0, column=0, sticky="w")
        self.model_var = tk.StringVar(value="")
        ttk.Entry(launcher, textvariable=self.model_var, width=38).grid(row=0, column=1, sticky="ew", padx=6)
        self.launch_vllm_btn = NeonButton(launcher, text="Launch vLLM", command=lambda: self._start_framework("vllm"))
        self.launch_vllm_btn.grid(row=0, column=2, padx=8)
        self.launch_llama_btn = NeonButton(launcher, text="Launch llama.cpp", command=lambda: self._start_framework("llama.cpp"))
        self.launch_llama_btn.grid(row=1, column=2, padx=8, pady=5)
        self.stop_btn = NeonButton(launcher, text="Stop Process", command=self._stop_process, state="disabled")
        self.stop_btn.grid(row=0, column=3, rowspan=2, padx=8)
        launcher.columnconfigure(1, weight=1)
        
        # Register keyboard shortcut after button creation
        self.bind_all("<Control-l>", lambda *_: self.launch_vllm_btn.invoke())

        # Dashboard
        dash = ttk.Frame(nb, padding=12)
        nb.add(dash, text="GPU Dashboard")
        dash.columnconfigure(0, weight=1) # Make GPU frame expand

        # Container for GPU widgets - will be populated dynamically
        self.dashboard_gpu_frame = ttk.Frame(dash)
        self.dashboard_gpu_frame.grid(row=0, column=0, sticky="nsew")
        # Make columns inside the dynamic frame configurable
        self.dashboard_gpu_frame.columnconfigure(1, weight=1)
        self.dashboard_gpu_frame.columnconfigure(3, weight=1)

        # TPS Meter (stays outside the dynamic frame)
        tps_frame = ttk.Frame(dash)
        tps_frame.grid(row=0, column=1, sticky="ne", padx=(20, 0))
        try:
            self.tps_meter = Meter(tps_frame, metersize=120, amounttotal=100, 
                                   subtext="toks/s", bootstyle="success")
            self.tps_meter.pack()
            self._has_meter = True
        except Exception as e:
            logger.error(f"Could not create Meter widget: {e}")
            self.tps_var = tk.StringVar(value="0 toks/s")
            self.tps_label = ttk.Label(tps_frame, textvariable=self.tps_var)
            self.tps_label.pack()
            self._has_meter = False
            
        # Configure row/column weights for the main dash frame
        dash.rowconfigure(0, weight=1)

        # Settings
        st = ttk.Frame(nb, padding=12)
        nb.add(st, text="Settings")
        
        # Create a settings frame for organization
        settings_frame = ttk.Labelframe(st, text="Display Settings", padding=10)
        settings_frame.pack(fill="x", pady=5)
        
        # Create a custom dark mode switch
        self.dark_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="Dark mode", variable=self.dark_var, 
                       command=self._toggle_theme, bootstyle="round-toggle").pack(anchor="w", pady=4)
        if self.style.theme.name != "flatly":
            self.dark_var.set(True)
            
        # Create GPU settings frame
        gpu_frame = ttk.Labelframe(st, text="GPU Settings", padding=10)
        gpu_frame.pack(fill="x", pady=5)
        
        # Add mock mode toggle
        self.mock_var = tk.BooleanVar(value=self.mock_mode)
        ttk.Checkbutton(gpu_frame, text="Enable Mock GPU Mode", variable=self.mock_var, 
                      command=self._toggle_mock_mode, bootstyle="round-toggle").pack(anchor="w", pady=4)
        
        # Add mock mode description
        ttk.Label(gpu_frame, text="Mock mode simulates GPU hardware for testing\nwhen no physical GPUs are available.", 
                 font=("Segoe UI", 9), foreground="gray").pack(anchor="w", pady=4)
                 
        # Add refresh button for real GPU detection (less critical now with telemetry)
        # refresh_button = ttk.Button(gpu_frame, text="Refresh GPU Information", 
        #                           command=self._refresh_gpu_info, bootstyle="info-outline")
        # refresh_button.pack(anchor="w", pady=8) # Keep commented or remove

        # Chat (will be repurposed for Logs)
        log_frame = ttk.Frame(nb, padding=6)
        nb.add(log_frame, text="Logs")
        self.log_box = ScrolledText(log_frame, autohide=True, height=18, state="disabled", font=("Consolas", 9))
        self.log_box.pack(fill="both", expand=True)

        # status bar
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var, anchor="e").pack(fill="x", side="bottom")

    # ---------------- Actions ----------------
    def _toggle_theme(self):
        new = "flatly" if self.dark_var.get() else "superhero"
        self.style.theme_use(new)
        
    def _toggle_mock_mode(self):
        """Toggle mock GPU mode on/off based on checkbox state."""
        if self.mock_var.get():
            self._enable_mock_mode()
        else:
            self._disable_mock_mode()
            
    def _enable_mock_mode(self, notify=True):
        """Enable mock GPU mode."""
        if self.mock_mode: return # Already enabled

        os.environ["DGPUOPT_MOCK_GPUS"] = "1"
        self.mock_mode = True
        logger.info("Enabling mock GPU mode")
        if hasattr(self, 'telemetry_service') and self.telemetry_service:
             self.telemetry_service.stop()
             self.telemetry_service.use_mock = True
             self.telemetry_service.start()
        if notify:
            self.status("Mock GPU mode enabled")
            self.q.put(("toast", "Mock GPU mode enabled"))

    def _disable_mock_mode(self):
        """Disable mock GPU mode and use real GPUs if available."""
        if not self.mock_mode: return # Already disabled

        logger.info("Attempting to disable mock GPU mode")
        # Clear env variable first
        if "DGPUOPT_MOCK_GPUS" in os.environ:
            del os.environ["DGPUOPT_MOCK_GPUS"]

        # Stop current service, change mode, restart
        if hasattr(self, 'telemetry_service') and self.telemetry_service:
            self.telemetry_service.stop()
            self.telemetry_service.use_mock = False

        # Need to re-check NVML availability if we start without mock
        try:
            import pynvml # Re-import might be needed if error occurred
            pynvml.nvmlInit()
            gpu_count = pynvml.nvmlDeviceGetCount()
            pynvml.nvmlShutdown()
            if gpu_count == 0:
                raise RuntimeError("No NVIDIA GPUs detected")

            # If real GPUs detected, proceed
            self.mock_mode = False
            if hasattr(self, 'telemetry_service') and self.telemetry_service:
                self.telemetry_service.start()
            logger.info("Real GPU mode enabled")
            self.status("Real GPU mode enabled")
            self.q.put(("toast", "Real GPU mode enabled"))

        except Exception as e:
            # Failed to detect real GPUs, revert to mock mode
            logger.warning(f"Failed to detect real GPUs ({e}), reverting to mock mode.")
            os.environ["DGPUOPT_MOCK_GPUS"] = "1" # Re-set env var
            self.mock_var.set(True)  # Reset the checkbox
            self.mock_mode = True
            if hasattr(self, 'telemetry_service') and self.telemetry_service:
                self.telemetry_service.use_mock = True # Set flag back
                self.telemetry_service.start() # Restart in mock mode
            error_msg = f"No real GPUs detected: {e}. Using mock mode."
            self.status(error_msg)
            self.q.put(("toast", error_msg))

    def _refresh_gpu_info(self):
        """Manually trigger GPU info refresh (less critical now)."""
        # This might be useful if telemetry stops or for explicit checks
        self.status("Refreshing GPU information...")
        # The TelemetryService handles periodic refresh, so this might
        # just involve querying the service's current state or
        # potentially asking the service to refresh immediately if implemented.
        latest_metrics = self.telemetry_service.get_metrics()
        self._update_dashboard(latest_metrics) # Update UI with latest known

    def _get_gpu_info(self):
        """Get real GPU information or mock data."""
        # This method is largely replaced by the telemetry service callback
        # Kept for potential direct calls if needed, but should rely on telemetry
        logger.debug("Direct _get_gpu_info called - relying on telemetry service.")
        latest_metrics = self.telemetry_service.get_metrics()
        self._update_dashboard(latest_metrics) # Update UI with latest known

    def _update_dashboard(self, metrics: Dict[int, GPUMetrics]):
        """Callback function to update dashboard widgets with new telemetry."""
        if not metrics:
            if not self.dashboard_widgets_created:
                # Display waiting message if widgets not yet created
                for widget in self.dashboard_gpu_frame.winfo_children():
                    widget.destroy()
                ttk.Label(self.dashboard_gpu_frame, text="Waiting for GPU data...").pack()
            return

        # --- Dynamic Widget Creation (First time only) ---
        if not self.dashboard_widgets_created:
            logger.info(f"Creating dashboard widgets for {len(metrics)} GPUs")
            # Clear placeholder/waiting message
            for widget in self.dashboard_gpu_frame.winfo_children():
                widget.destroy()

            self.gpu_widgets = {}
            gpu_ids = sorted(metrics.keys())

            for row_idx, gpu_id in enumerate(gpu_ids):
                gpu_metrics = metrics[gpu_id]
                gpu_frame = ttk.Labelframe(self.dashboard_gpu_frame, text=f" GPU {gpu_id}: {gpu_metrics.name} ", padding=10)
                gpu_frame.grid(row=row_idx, column=0, columnspan=4, sticky="ew", pady=5, padx=5)
                # Configure columns within the GPU frame (4 columns for label/widget pairs)
                gpu_frame.columnconfigure(1, weight=1)
                gpu_frame.columnconfigure(3, weight=1)

                widgets = {}

                # Row 0: Utilization and Temperature
                ttk.Label(gpu_frame, text="Utilization:").grid(row=0, column=0, sticky="w", padx=5)
                widgets['util_bar'] = GradientProgress(gpu_frame)
                widgets['util_bar'].grid(row=0, column=1, sticky="ew", padx=5, pady=2)

                widgets['temp_var'] = tk.StringVar(value="--°C")
                ttk.Label(gpu_frame, text="Temp:").grid(row=0, column=2, sticky="e", padx=(15, 5))
                ttk.Label(gpu_frame, textvariable=widgets['temp_var']).grid(row=0, column=3, sticky="w", padx=5)

                # Row 1: VRAM and Power
                ttk.Label(gpu_frame, text="VRAM:").grid(row=1, column=0, sticky="w", padx=5)
                widgets['vram_bar'] = GradientProgress(gpu_frame) # TODO: Add text label?
                widgets['vram_bar'].grid(row=1, column=1, sticky="ew", padx=5, pady=2)

                widgets['power_var'] = tk.StringVar(value="-- W")
                ttk.Label(gpu_frame, text="Power:").grid(row=1, column=2, sticky="e", padx=(15, 5))
                ttk.Label(gpu_frame, textvariable=widgets['power_var']).grid(row=1, column=3, sticky="w", padx=5)

                # Row 2: Clocks (Optional - add if needed)
                # widgets['clocks_var'] = tk.StringVar(value="Clocks: --/-- MHz")
                # ttk.Label(gpu_frame, textvariable=widgets['clocks_var']).grid(row=2, column=0, columnspan=4, sticky="w", padx=5)

                # Row 3: PCIe (Optional - add if needed)
                # widgets['pcie_var'] = tk.StringVar(value="PCIe: -- MB/s")
                # ttk.Label(gpu_frame, textvariable=widgets['pcie_var']).grid(row=3, column=0, columnspan=4, sticky="w", padx=5)

                self.gpu_widgets[gpu_id] = widgets

            self.dashboard_widgets_created = True

        # --- Update Existing Widgets ---
        for gpu_id, gpu_metrics in metrics.items():
            if gpu_id in self.gpu_widgets:
                widgets = self.gpu_widgets[gpu_id]
                widgets['util_bar'].set(gpu_metrics.utilization)
                widgets['vram_bar'].set(gpu_metrics.memory_percent)
                widgets['temp_var'].set(f"{gpu_metrics.temperature}°C")
                widgets['power_var'].set(f"{gpu_metrics.power_usage:.1f} W")
                # Optional: Update clocks/PCIe if widgets exist
                # if 'clocks_var' in widgets:
                #     widgets['clocks_var'].set(f"Clocks: {gpu_metrics.clock_sm}/{gpu_metrics.clock_memory} MHz")
                # if 'pcie_var' in widgets:
                #     widgets['pcie_var'].set(f"PCIe TX/RX: {gpu_metrics.pcie_tx/1024:.1f}/{gpu_metrics.pcie_rx/1024:.1f} MB/s")
            else:
                logger.warning(f"Received metrics for GPU {gpu_id}, but no widgets found.")

    def _start_framework(self, framework: str):
        """Start the selected framework (vLLM or llama.cpp)."""
        if self.active_runner:
            messagebox.showwarning("Process Running", "Another process is already running.", parent=self)
            return

        # Get command from Optimizer Tab
        if framework == "vllm":
            command_string = self.optimizer_tab.vllm_cmd_var.get()
            status_msg = "Launching vLLM..."
        elif framework == "llama.cpp":
            command_string = self.optimizer_tab.llama_cmd_var.get()
            status_msg = "Launching llama.cpp..."
        else:
            logger.error(f"Unknown framework requested: {framework}")
            messagebox.showerror("Error", f"Unknown framework: {framework}", parent=self)
            return

        if not command_string:
            messagebox.showerror("Error", f"{framework.upper()} command is empty. Calculate optimization first.", parent=self)
            return

        model_path = self.model_var.get()
        if not model_path:
             messagebox.showerror("Error", f"Model path cannot be empty.", parent=self)
             return
        # TODO: Properly inject model path into the command string if needed
        # This currently assumes the optimizer tab generated the full command.

        self.status(status_msg)
        logger.info(f"Starting {framework} with command: {command_string}")
        # Disable launch buttons, enable stop button
        self.launch_vllm_btn.configure(state="disabled")
        self.launch_llama_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._clear_logs()
        self._append_log(f"--- Starting {framework} ---")
        self._append_log(f"Command: {command_string}")

        try:
            self.active_runner = Runner(cmd=command_string)
            self.active_runner.start()
            # Start monitoring the runner output in a separate thread
            self.pool.submit(self._monitor_runner)
        except Exception as e:
            logger.error(f"Failed to start runner for {framework}: {e}", exc_info=True)
            messagebox.showerror("Launch Error", f"Failed to start {framework}:\n{e}", parent=self)
            self.status(f"{framework.capitalize()} launch failed")
            self.launch_vllm_btn.configure(state="normal")
            self.launch_llama_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.active_runner = None

    def _monitor_runner(self):
        """Monitor the output queue of the active runner process."""
        if not self.active_runner or not self.active_runner.proc:
            return

        runner = self.active_runner # Local reference
        while True:
            try:
                line = runner.q.get(timeout=0.2) # Check queue periodically
                self.q.put(("runner_log", line)) # Send log line to main thread queue
            except queue.Empty:
                # Check if process has ended
                if runner.proc and runner.proc.poll() is not None:
                    exit_code = runner.proc.poll()
                    status_msg = f"Process finished with exit code {exit_code}."
                    self.q.put(("status", status_msg))
                    logger.info(status_msg)
                    self.q.put(("runner_stopped", None)) # Signal completion
                    break # Exit monitoring loop
            except Exception as e:
                logger.error(f"Error monitoring runner: {e}", exc_info=True)
                self.q.put(("status", "Error monitoring process"))
                self.q.put(("runner_stopped", None))
                break

    def _stop_process(self):
        """Stop the currently active runner process."""
        if self.active_runner:
            logger.info("Stopping active process...")
            self.status("Stopping process...")
            try:
                self.active_runner.stop()
                # Give monitor time to notice and exit
                # The runner_stopped signal will re-enable buttons
            except Exception as e:
                 logger.error(f"Error stopping process: {e}", exc_info=True)
                 messagebox.showerror("Error", f"Failed to stop process: {e}", parent=self)
                 # Force re-enable buttons if stop fails badly
                 self._on_runner_stopped()
        else:
            logger.warning("Stop requested but no active runner found.")

    def _on_runner_stopped(self):
        """Actions to perform when the runner stops (called from main thread)."""
        self.launch_vllm_btn.configure(state="normal")
        self.launch_llama_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.active_runner = None
        logger.info("Runner stopped, UI updated.")

    def _dummy_long_task(self):
        # This is now replaced by _start_framework and _monitor_runner
        pass

    # ---------------- Helpers ----------------
    def _append_log(self, txt: str):
        """Append text to the log box."""
        self.log_box.configure(state="normal")
        self.log_box.insert("end", txt + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _clear_logs(self):
        """Clear the log box."""
        self.log_box.configure(state="normal")
        self.log_box.delete(1.0, "end")
        self.log_box.configure(state="disabled")

    def _poll_queue(self):
        try:
            while True:
                kind, val = self.q.get_nowait()
                if kind == "tps": # Keep TPS polling for now
                    if hasattr(self, '_has_meter') and self._has_meter:
                        self.tps_meter.configure(amountused=val)
                    elif hasattr(self, 'tps_var'):
                        self.tps_var.set(f"{val} toks/s")
                elif kind == "runner_log":
                    self._append_log(str(val))
                elif kind == "status":
                    self.status(val)
                elif kind == "toast":
                    try:
                        ToastNotification(title="DualGPUOptimizer", message=val, duration=3000).show_toast()
                    except Exception as e:
                        logger.error(f"Toast notification error: {e}")
                        print(f"Toast notification error: {e}")
                elif kind == "runner_stopped":
                     self._on_runner_stopped()
                # Removed util and vram handling, now done by callback
        except queue.Empty:
            pass
        # Reduce polling frequency slightly if only checking for non-telemetry
        self.after(100, self._poll_queue)

    def status(self, msg):
        self.status_var.set(msg)
        # Clear status after a delay unless it's replaced by another message
        self.after(10000, lambda current_msg=msg: \
                   self.status_var.set("Ready") if self.status_var.get() == current_msg else None)

    def _marquee(self):        # periodic status reset safeguard
        self.after(60000, self._marquee)

    def on_close(self):
        logger.info("Closing application...")
        # Stop any active runner
        self._stop_process()

        # Stop telemetry service
        if hasattr(self, 'telemetry_service') and self.telemetry_service:
            self.telemetry_service.stop()
            logger.info("Telemetry service stopped.")

        cfg = {
            "theme": self.style.theme.name,
            "win": self.geometry(),
            "mock_mode": self.mock_mode,  # Save mock mode setting
        }
        _save_cfg(cfg)
        self.pool.shutdown(wait=False, cancel_futures=True) # Don't wait indefinitely
        self.destroy()

# ---------------- entry point ----------------
def run_modern_app():
    ModernApp().mainloop()

if __name__ == "__main__":
    run_modern_app() 