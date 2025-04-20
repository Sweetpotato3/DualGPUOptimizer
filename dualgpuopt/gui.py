"""
dualgpuopt.gui – modern neon‑styled GUI
"""
from __future__ import annotations
import queue, platform, threading, time, tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.toast import ToastNotification
from ttkbootstrap.scrolled import ScrolledFrame
from pathlib import Path
from dualgpuopt.ui.neon import init_theme, NeonButton, GradientBar

# Create a simple Tooltip class
class Tooltip:
    """Simple tooltip class"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)
        self.tooltip = None

    def show(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        # Create a toplevel window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(self.tooltip, text=self.text, padding=(5, 3))
        label.pack()

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

# Create a simplified Meter class if not available
class SimpleMeter(ttk.Canvas):
    """Simple meter widget replacement"""
    def __init__(self, master, bootstyle="info", subtext="", **kwargs):
        super().__init__(master, width=100, height=100, **kwargs)
        self.bootstyle = bootstyle
        self._value = 0
        self.create_oval(10, 10, 90, 90, outline=self._get_color(), width=2, fill="")
        self.meter_text = self.create_text(50, 40, text="0%", fill=self._get_color(), font=("Arial", 14, "bold"))
        self.subtext_id = self.create_text(50, 60, text=subtext, fill=self._get_color())

    def _get_color(self):
        if self.bootstyle == "success":
            return "#4CAF50"  # Green
        elif self.bootstyle == "info":
            return "#2196F3"  # Blue
        elif self.bootstyle == "warning":
            return "#FF9800"  # Orange
        elif self.bootstyle == "danger":
            return "#F44336"  # Red
        else:
            return "#9C27B0"  # Purple (default)

    def configure(self, **kwargs):
        if "amountused" in kwargs:
            self._value = kwargs["amountused"]
            self.itemconfigure(self.meter_text, text=f"{int(self._value)}%")
        super().configure(**{k: v for k, v in kwargs.items() if k != "amountused"})

class SimpleTelemetryThread(threading.Thread):
    """Basic telemetry thread sending mock data"""
    def __init__(self, message_queue):
        super().__init__(daemon=True)
        self.queue = message_queue
        self.running = True

    def run(self):
        import random
        while self.running:
            # Send random GPU utilization values (0-100%)
            self.queue.put(("util", random.uniform(10, 90)))
            # Send random VRAM usage values (0-100%)
            self.queue.put(("vram", random.uniform(20, 80)))
            # Send random tokens per second (0-100)
            self.queue.put(("tps", random.uniform(10, 50)))
            time.sleep(1)

    def stop(self):
        self.running = False

class DualGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DualGPUOptimizer - Modern UI")
        try:
            icon_path = Path(__file__).parent / "assets" / "app_64.png"
            self.iconphoto(True, tk.PhotoImage(file=icon_path))
        except Exception:
            pass  # Skip icon if not found

        # Initialize theme
        self._init_theme()

        # Set window size
        self.geometry("1150x730")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Set up message queue for communication between threads
        self.bus = queue.Queue()

        # Set up mock telemetry thread
        self.tele = SimpleTelemetryThread(self.bus)
        self.tele.start()

        # Build UI components
        self._build_ui()

        # Start polling for messages
        self.after(40, self._poll)

    def _init_theme(self):
        """Initialize the theme"""
        # Set up basic style
        if hasattr(ttk, 'Style'):
            style = ttk.Style()
            style.theme_use("darkly")

            # Basic theme settings
            style.configure(".", font=("Arial", 10))
            style.configure("TFrame", background="#2E1D47")
            style.configure("Card.TFrame", background="#2E1D47", padding=12)
            style.configure("TLabel", foreground="#FFFFFF")
            style.configure("Title.TLabel", font=("Arial", 14, "bold"))

            # Configure notebook tabs
            style.map("TNotebook.Tab",
                      background=[("selected", "#371B59")],
                      foreground=[("selected", "white")])
        else:
            # Fallback to basic styling if ttk.Style is not available
            self.configure(background="#2E1D47")

    # ------------------------------ UI building ---------------------------------
    def _build_ui(self):
        # Header toolbar
        hdr = ttk.Frame(self, padding=6, style="Card.TFrame")
        hdr.pack(fill="x")
        NeonButton(hdr, text="Launch Model", command=self._on_launch).pack(side="left")
        NeonButton(hdr, text="New Session", command=self._on_new_session).pack(side="left", padx=6)

        # Add theme toggle button to header toolbar if available
        try:
            from dualgpuopt.gui.theme import ThemeToggleButton
            ThemeToggleButton(hdr).pack(side="right", padx=6)
        except ImportError:
            # Fallback to simple button
            ttk.Button(hdr, text="🌙/☀️", command=self._toggle_theme).pack(side="right", padx=6)

        # Notebook
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, pady=(4,0))
        self._build_launcher(nb)
        self._build_dashboard(nb)
        self._build_chat(nb)

        # Status bar
        self.status = tk.StringVar(value="Ready - Modern UI Active")
        ttk.Label(self, textvariable=self.status, anchor="e").pack(fill="x", side="bottom")

    # ------- launcher tab -------
    def _build_launcher(self, nb):
        page = ttk.Frame(nb, padding=12, style="Card.TFrame")
        nb.add(page, text="Launcher")
        ttk.Label(page, text="Model Path").grid(row=0,column=0,sticky="w")
        self.model_var = tk.StringVar(value="TheBloke/dolphin-2.2-yi-34b-200k-AWQ")
        ttk.Entry(page, textvariable=self.model_var, width=55).grid(row=0,column=1,sticky="ew",padx=6)
        self.launch_btn = NeonButton(page, text="Launch", command=self._on_launch)
        self.launch_btn.grid(row=0,column=2,padx=8)
        page.columnconfigure(1, weight=1)
        Tooltip(self.launch_btn, text="Start model with AWQ quantization")

        # Output box for logs
        self.out_box = tk.Text(page, height=18, bg="#13141c", fg="#E6E6E6",
                              insertbackground="white")
        self.out_box.grid(row=2,column=0,columnspan=3,sticky="nsew",pady=(12,0))
        page.rowconfigure(2, weight=1)

    # ------- dashboard -------
    def _build_dashboard(self, nb):
        dash = ttk.Frame(nb, padding=12, style="Card.TFrame")
        nb.add(dash,text="Dashboard")
        ttk.Label(dash,text="GPU Utilisation").grid(row=0,column=0,sticky="w")
        self.util_bar = GradientBar(dash)
        self.util_bar.grid(row=0,column=1,sticky="ew")
        ttk.Label(dash,text="VRAM Usage").grid(row=1,column=0,sticky="w",pady=8)
        self.vram_bar = GradientBar(dash)
        self.vram_bar.grid(row=1,column=1,sticky="ew")

        # Use our SimpleMeter if ttkbootstrap.Meter is not available
        try:
            from ttkbootstrap import Meter
            self.tps = Meter(dash, bootstyle="success", subtext="tok/s")
        except (ImportError, AttributeError):
            self.tps = SimpleMeter(dash, bootstyle="success", subtext="tok/s")

        self.tps.grid(row=0,column=2,rowspan=2,padx=12)
        dash.columnconfigure(1, weight=1)

    # ------- chat -------
    def _build_chat(self, nb):
        chat = ttk.Frame(nb, padding=6, style="Card.TFrame")
        nb.add(chat,text="Chat")

        # Simple scrollable text area for messages
        self.chat_frame = ttk.Frame(chat)
        self.chat_frame.pack(fill="both", expand=True)

        # Message display area
        self.msg_text = tk.Text(self.chat_frame, wrap="word", bg="#221638", fg="#E6E6E6")
        scrollbar = ttk.Scrollbar(self.chat_frame, command=self.msg_text.yview)
        self.msg_text.configure(yscrollcommand=scrollbar.set)
        self.msg_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Input area
        input_frame = ttk.Frame(chat)
        input_frame.pack(fill="x", pady=6)
        self.entry = tk.Text(input_frame, height=3, wrap="word", bg="#221638", fg="#E6E6E6")
        self.entry.pack(fill="x", side="left", expand=True)
        self.entry.bind("<Control-Return>", self._on_send)
        NeonButton(input_frame, text="Send", command=self._on_send).pack(side="left", padx=4)

    # ------------------------------ Actions ---------------------------------
    def _toggle_theme(self):
        """Simple theme toggle between dark and light"""
        # This is a placeholder for actual theme toggling
        self.status.set("Theme toggling not implemented in this simplified version")

    def _append_message(self, text, is_user=False):
        """Add a message to the chat window"""
        self.msg_text.configure(state="normal")

        if is_user:
            self.msg_text.insert("end", f"You: {text}\n\n", "user")
            self.msg_text.tag_configure("user", foreground="#FFFFFF", background="#371B59")
        else:
            self.msg_text.insert("end", f"Assistant: {text}\n\n", "assistant")
            self.msg_text.tag_configure("assistant", foreground="#E6E6E6")

        self.msg_text.configure(state="disabled")
        self.msg_text.see("end")  # Scroll to the bottom

    def _on_send(self, *_):
        """Handle sending a message"""
        txt = self.entry.get("1.0","end").strip()
        if not txt:
            return

        self.entry.delete("1.0","end")
        self._append_message(txt, is_user=True)

        # Echo the message backwards as a simple demo
        threading.Thread(target=self._fake_assistant_reply, args=(txt,), daemon=True).start()

    def _fake_assistant_reply(self, txt):
        """Simulate an assistant reply for demo purposes"""
        # Simple echo with a delay
        time.sleep(0.5)
        self.after(100, lambda: self._append_message(f"You said: {txt}"))

        # Then send individual characters with a delay
        reversed_text = txt[::-1]
        reply = f"Here's your text reversed: {reversed_text}"
        time.sleep(1)
        self.after(100, lambda: self._append_message(reply))

    # ---------------- telemetry + queue ----------------
    def _poll(self):
        """Poll the message queue for updates"""
        try:
            while True:
                kind, val = self.bus.get_nowait()
                if kind == "util":
                    self.util_bar.set(val)
                elif kind == "vram":
                    self.vram_bar.set(val)
                elif kind == "tps":
                    self.tps.configure(amountused=min(val, 100))
        except queue.Empty:
            pass
        self.after(40, self._poll)

    # ---------------- misc actions ----------------
    def _on_new_session(self):
        """Create a new chat session"""
        # Clear the chat window
        self.msg_text.configure(state="normal")
        self.msg_text.delete("1.0", "end")
        self.msg_text.configure(state="disabled")

        # Show a notification
        try:
            ToastNotification(
                title="New Session",
                message="Started a new chat session",
                duration=1800
            ).show_toast()
        except:
            # Fallback if ToastNotification fails
            self.status.set("New session created")
            self.after(3000, lambda: self.status.set("Ready - Modern UI Active"))

    def _on_launch(self):
        """Launch a model (demo only)"""
        model = self.model_var.get()
        self.status.set(f"Launching {model}...")
        self.launch_btn.configure(state="disabled")

        # Simulate model launch
        def simulate_launch():
            # Add some fake startup messages to the output box
            for msg in [
                "Loading model configuration...",
                "Initializing CUDA context...",
                f"Loading {model}...",
                "Creating tensor parallel layers...",
                "Model loaded successfully!"
            ]:
                time.sleep(0.7)
                self.after(10, lambda m=msg: self._append_to_output(m))

            # Re-enable button and update status
            time.sleep(0.5)
            self.after(10, lambda: self.launch_btn.configure(state="normal"))
            self.after(10, lambda: self.status.set("Ready - Model loaded"))

        # Run in background thread
        threading.Thread(target=simulate_launch, daemon=True).start()

    def _append_to_output(self, text):
        """Add text to the output box"""
        self.out_box.insert("end", f"{text}\n")
        self.out_box.see("end")  # Scroll to the bottom

    def _on_close(self):
        """Handle window closing"""
        if hasattr(self, 'tele') and self.tele:
            self.tele.stop()
        self.destroy()

def run_app():
    """Start the UI application"""
    app = DualGUI()
    app.mainloop()

if __name__ == "__main__":
    run_app()