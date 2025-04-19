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

CFG_FILE = Path.home() / ".dualgpuopt" / "ui.json"
ICON_PATH = Path(__file__).parent.parent / "assets" / "app_64.png"

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
        self.iconphoto(True, tk.PhotoImage(file=ICON_PATH))
        self.style.configure(".", font=("Segoe UI", 10))
        
        cfg = _load_cfg()
        if "theme" in cfg:
            self.style.theme_use(cfg["theme"])
        if "win" in cfg:
            self.geometry(cfg["win"])

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind_all("<Control-q>", lambda *_: self.on_close())
        
        self.pool = ThreadPoolExecutor(max_workers=4)
        self.q = queue.Queue()

        nb = ttk.Notebook(self, bootstyle="dark")
        nb.pack(fill="both", expand=True)
        nb.enable_traversal()

        self._build_tabs(nb)
        self.after(100, self._marquee)  # status reset marquee
        self.after(40, self._poll_queue)

    # ---------------- Tabs -----------------
    def _build_tabs(self, nb):
        # Optimizer placeholder
        nb.add(ttk.Frame(nb), text="Optimizer")

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
        ttk.Label(dash, text="GPU util").grid(row=0, column=0, sticky="w")
        self.util_bar = GradientProgress(dash); self.util_bar.grid(row=0, column=1, padx=6, sticky="ew")
        ttk.Label(dash, text="VRAM").grid(row=1, column=0, sticky="w")
        self.vram_bar = GradientProgress(dash); self.vram_bar.grid(row=1, column=1, padx=6, sticky="ew")
        self.tps_meter = Meter(dash, subtext="toks/s", bootstyle="success"); self.tps_meter.grid(row=0, column=2, rowspan=2, padx=12)
        dash.columnconfigure(1, weight=1)

        # Settings
        st = ttk.Frame(nb, padding=12)
        nb.add(st, text="Settings")
        # Create a custom dark mode switch since Switch widget might not be available
        self.dark_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(st, text="Dark mode", variable=self.dark_var, 
                       command=self._toggle_theme, bootstyle="round-toggle").pack(anchor="w", pady=4)
        if self.style.theme.name != "flatly":
            self.dark_var.set(True)

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

    def _start_vllm(self):
        self.status("Launching vLLM …")
        self.launch_btn.configure(state="disabled")
        self.pool.submit(self._dummy_long_task)

    def _dummy_long_task(self):
        for _ in range(60):
            time.sleep(0.1)
            self.util_bar.set(random.randint(40, 100))
            self.vram_bar.set(random.randint(10, 90))
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
                if kind == "tps":   self.tps_meter.configure(amountused=val)
                elif kind == "chat": self._append_chat(val)
                elif kind == "status": self.status(val)
                elif kind == "toast":
                    try:
                        ToastNotification(title="DualGPUOptimizer", message=val, duration=3000).show_toast()
                    except Exception as e:
                        print(f"Toast notification error: {e}")
        except queue.Empty:
            pass
        self.after(50, self._poll_queue)

    def status(self, msg):
        self.status_var.set(msg)
        self.after(5000, lambda: self.status_var.set("Ready"))

    def _marquee(self):        # periodic status reset safeguard
        if not self.status_var.get():
            self.status_var.set("Ready")
        self.after(60000, self._marquee)

    def on_close(self):
        cfg = {
            "theme": self.style.theme.name,
            "win": self.geometry(),
        }
        _save_cfg(cfg)
        self.pool.shutdown(cancel_futures=True)
        self.destroy()

# ---------------- entry point ----------------
def run_modern_app():
    ModernApp().mainloop()

if __name__ == "__main__":
    run_modern_app() 