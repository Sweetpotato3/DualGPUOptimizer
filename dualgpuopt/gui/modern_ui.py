"""
dualgpuopt.gui.modern_ui
Purple themed desktop GUI for DualGPUOptimizer.
"""
from __future__ import annotations
import json, tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.widgets import Meter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import queue, threading
import time, random
import logging
import os
from typing import Dict

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

        nb = ttk.Notebook(self, bootstyle="dark")
        nb.pack(fill="both", expand=True)
        nb.enable_traversal()

        self._build_tabs(nb)
        self.after(100, self._marquee)  # status reset marquee
        self.after(50, self._poll_queue)
        
        # Initial GPU info display relies on telemetry callback now
        # self.after(500, self._refresh_gpu_info) # Removed, handled by telemetry

    # ---------------- Tabs -----------------
    def _build_tabs(self, nb):
        # Optimizer Tab - Now using the real implementation
        optimizer_frame = OptimizerTab(nb)
        nb.add(optimizer_frame, text="Optimizer")

        # Launcher
        launcher = ttk.Frame(nb, padding=12)
        nb.add(launcher, text="Launcher")
        ttk.Label(launcher, text="Model path:").grid(row=0, column=0, sticky="w")
        self.model_var = tk.StringVar(value="")
        ttk.Entry(launcher, textvariable=self.model_var, width=38).grid(row=0, column=1, sticky="ew", padx=6)
        self.launch_btn = NeonButton(launcher, text="Launch vLLM", command=self._start_vllm)
        self.launch_btn.grid(row=0, column=2, padx=8)
        launcher.columnconfigure(1, weight=1)
        
        # Register keyboard shortcut after button creation
        self.bind_all("<Control-l>", lambda *_: self.launch_btn.invoke())

        # Dashboard
        dash = ttk.Frame(nb, padding=12)
        nb.add(dash, text="GPU Dashboard")
        ttk.Label(dash, text="GPU 0 util").grid(row=0, column=0, sticky="w")
        self.util_bar = GradientProgress(dash); self.util_bar.grid(row=0, column=1, padx=6, sticky="ew")
        ttk.Label(dash, text="GPU 0 VRAM").grid(row=1, column=0, sticky="w")
        self.vram_bar = GradientProgress(dash); self.vram_bar.grid(row=1, column=1, padx=6, sticky="ew")
        
        # Try to create a Meter widget, with fallback to a label if it fails
        try:
            self.tps_meter = Meter(dash, subtext="toks/s", bootstyle="success")
            self.tps_meter.grid(row=0, column=2, rowspan=2, padx=12)
            self._has_meter = True
        except Exception as e:
            logger.error(f"Could not create Meter widget: {e}")
            self.tps_var = tk.StringVar(value="0 toks/s")
            self.tps_label = ttk.Label(dash, textvariable=self.tps_var)
            self.tps_label.grid(row=0, column=2, rowspan=2, padx=12)
            self._has_meter = False
            
        dash.columnconfigure(1, weight=1)

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

        # Chat
        chat = ttk.Frame(nb, padding=6)
        nb.add(chat, text="Chat")
        self.chat_box = ScrolledText(chat, autohide=True, height=18, state="disabled")
        self.chat_box.pack(fill="both", expand=True)
        self.chat_entry = ttk.Entry(chat)
        self.chat_entry.pack(fill="x", pady=6, padx=4, side="left", expand=True)
        self.chat_entry.bind("<Return>", self._on_send)
        self.send_btn = NeonButton(chat, text="Send", command=self._on_send)
        self.send_btn.pack(side="right", padx=4)

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
        self.telemetry_service.stop()
        self.telemetry_service.use_mock = True
        self.telemetry_service.start()
        if notify:
            self.status("Mock GPU mode enabled")
            self.q.put(("toast", "Mock GPU mode enabled"))
            # self._refresh_gpu_info() # No need to manually refresh
            
    def _disable_mock_mode(self):
        """Disable mock GPU mode and use real GPUs if available."""
        if not self.mock_mode: return # Already disabled

        logger.info("Attempting to disable mock GPU mode")
        # Clear env variable first
        if "DGPUOPT_MOCK_GPUS" in os.environ:
            del os.environ["DGPUOPT_MOCK_GPUS"]

        # Stop current service, change mode, restart
        self.telemetry_service.stop()
        self.telemetry_service.use_mock = False

        # Need to re-check NVML availability if we start without mock
        try:
            pynvml.nvmlInit()
            gpu_count = pynvml.nvmlDeviceGetCount()
            pynvml.nvmlShutdown()
            if gpu_count == 0:
                raise RuntimeError("No NVIDIA GPUs detected")

            # If real GPUs detected, proceed
            self.mock_mode = False
            self.telemetry_service.start()
            logger.info("Real GPU mode enabled")
            self.status("Real GPU mode enabled")
            self.q.put(("toast", "Real GPU mode enabled"))
            # self._refresh_gpu_info() # No need to manually refresh

        except Exception as e:
            # Failed to detect real GPUs, revert to mock mode
            logger.warning(f"Failed to detect real GPUs ({e}), reverting to mock mode.")
            os.environ["DGPUOPT_MOCK_GPUS"] = "1" # Re-set env var
            self.mock_var.set(True)  # Reset the checkbox
            self.mock_mode = True
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
            # No metrics received yet or an error occurred
            self.util_bar.set(0)
            self.vram_bar.set(0)
            return

        # For now, display GPU 0's metrics
        gpu0_metrics = metrics.get(0)
        if gpu0_metrics:
            self.util_bar.set(gpu0_metrics.utilization)
            self.vram_bar.set(gpu0_metrics.memory_percent)
            # Update status bar maybe?
            # self.status(f"GPU 0: {gpu0_metrics.utilization}% Util, {gpu0_metrics.memory_percent:.1f}% VRAM")
        else:
            # Handle case where GPU 0 data isn't available
            self.util_bar.set(0)
            self.vram_bar.set(0)
            logger.warning("Metrics received, but GPU 0 data missing.")

    def _start_vllm(self):
        self.status("Launching vLLM …")
        self.launch_btn.configure(state="disabled")
        self.pool.submit(self._dummy_long_task)

    def _dummy_long_task(self):
        # Keep TPS simulation for now, until real launcher integration
        for _ in range(60):
            time.sleep(0.1)
            # self.util_bar.set(random.randint(40, 100)) # Let telemetry handle this
            # self.vram_bar.set(random.randint(10, 90)) # Let telemetry handle this
            self.q.put(("tps", random.randint(10, 80)))
        self.q.put(("status", "vLLM ready"))
        self.q.put(("toast", "vLLM finished warm‑up"))
        self.after_idle(lambda: self.launch_btn.configure(state="normal"))

    # chat
    def _on_send(self, *_):
        prompt = self.chat_entry.get().strip()
        if not prompt: return
        self._append_chat(f"🟣 You: {prompt}\n")
        self.chat_entry.delete(0, "end")
        self.send_btn.configure(state="disabled")
        threading.Thread(target=self._chat_worker, args=(prompt,), daemon=True).start()

    def _chat_worker(self, prompt: str):
        try:
            # Simulate API response
            for _ in range(5):
                time.sleep(0.3)
                self.q.put(("chat", "This is a simulated response... "))
            self.q.put(("chat", "\n"))
        except Exception as e:
            self.q.put(("status", f"Chat error: {e}"))
        finally:
            self.after_idle(lambda: self.send_btn.configure(state="normal"))

    # ---------------- Helpers ----------------
    def _append_chat(self, txt: str):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", txt)
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def _poll_queue(self):
        try:
            while True:
                kind, val = self.q.get_nowait()
                if kind == "tps": # Keep TPS polling for now
                    if hasattr(self, '_has_meter') and self._has_meter:
                        self.tps_meter.configure(amountused=val)
                    elif hasattr(self, 'tps_var'):
                        self.tps_var.set(f"{val} toks/s")
                elif kind == "chat":
                    self._append_chat(val)
                elif kind == "status":
                    self.status(val)
                elif kind == "toast":
                    try:
                        ToastNotification(title="DualGPUOptimizer", message=val, duration=3000).show_toast()
                    except Exception as e:
                        logger.error(f"Toast notification error: {e}")
                        print(f"Toast notification error: {e}")
                # Removed util and vram handling, now done by callback
        except queue.Empty:
            pass
        # Reduce polling frequency slightly if only checking for non-telemetry
        self.after(100, self._poll_queue)

    def status(self, msg):
        self.status_var.set(msg)
        self.after(5000, lambda: self.status_var.set("Ready"))

    def _marquee(self):        # periodic status reset safeguard
        if not self.status_var.get():
            self.status_var.set("Ready")
        self.after(60000, self._marquee)

    def on_close(self):
        logger.info("Closing application...")
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