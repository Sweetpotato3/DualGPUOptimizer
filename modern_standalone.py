#!/usr/bin/env python3
"""
Completely standalone modern UI for DualGPUOptimizer
Contains all necessary widgets and functionality in a single file
"""
import tkinter as tk
import threading
import time
import queue
import random
from pathlib import Path

# Try to import ttkbootstrap for better styling
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.scrolled import ScrolledFrame
    from ttkbootstrap.toast import ToastNotification
    TTKBOOTSTRAP_AVAILABLE = True
    print("Using ttkbootstrap for enhanced UI")
except ImportError:
    import tkinter.ttk as ttk
    TTKBOOTSTRAP_AVAILABLE = False
    print("ttkbootstrap not found - using standard ttk")

    # Create a minimal replacement for ScrolledFrame
    class ScrolledFrame(ttk.Frame):
        def __init__(self, master, **kwargs):
            super().__init__(master, **kwargs)
            self.canvas = tk.Canvas(self, highlightthickness=0)
            self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
            self.scrollable_frame = ttk.Frame(self.canvas)

            self.scrollable_frame.bind("<Configure>",
                lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
            self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
            self.canvas.configure(yscrollcommand=self.scrollbar.set)

            self.canvas.pack(side="left", fill="both", expand=True)
            self.scrollbar.pack(side="right", fill="y")

        def display_widget(self, widget_class, **kwargs):
            return widget_class(self.scrollable_frame, **kwargs)

    # Create a minimal Toast notification replacement
    class ToastNotification:
        def __init__(self, title="", message="", duration=3000, **kwargs):
            self.title = title
            self.message = message
            self.duration = duration

        def show_toast(self):
            print(f"TOAST: {self.title} - {self.message}")


# ========== Custom Widgets ==========

class NeonButton(ttk.Button):
    """Button with hover effects"""
    def __init__(self, master, text, **kwargs):
        style_name = "NeonButton.TButton"

        # Create style if not exists
        try:
            style = ttk.Style()
            style.configure(style_name, font=("Arial", 10, "bold"), padding=(10, 5))
            if TTKBOOTSTRAP_AVAILABLE:
                style.configure(style_name, bootstyle="info-outline")
                style.map(style_name, background=[("active", "#BF7DE0")])
        except:
            pass

        super().__init__(master, text=text, style=style_name, **kwargs)

        # Bind hover effects
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None):
        """Mouse enter effect"""
        if TTKBOOTSTRAP_AVAILABLE:
            self.configure(bootstyle="info")

    def _on_leave(self, event=None):
        """Mouse leave effect"""
        if TTKBOOTSTRAP_AVAILABLE:
            self.configure(bootstyle="info-outline")


class GradientBar(tk.Canvas):
    """Animated gradient progress bar"""
    def __init__(self, master, width=260, height=14, **kwargs):
        super().__init__(master, width=width, height=height,
                        highlightthickness=0, **kwargs)
        # Store dimensions and values
        self._width = width
        self._height = height
        self._value = 0.0
        self._target = 0.0

        # Create gradient colors
        self._start_color = "#37ECBA"
        self._end_color = "#E436CA"

        # Create rectangle for the bar
        self._rect_id = self.create_rectangle(
            0, 0, 0, height,
            fill=self._start_color, outline=""
        )

        # Start animation loop
        self._last_time = time.time()
        self.after(16, self._tick)

    def set(self, percent_value):
        """Set the bar's value (0-100)"""
        self._target = max(0.0, min(percent_value, 100.0))

    def _tick(self):
        """Animation update loop"""
        now = time.time()
        dt = now - self._last_time
        self._last_time = now

        # Smooth animation towards target
        if abs(self._value - self._target) > 0.1:
            # Calculate step size - larger when further from target
            step = dt * 80 * (1.0 + abs(self._value - self._target) / 20.0)

            # Move value toward target
            if self._value < self._target:
                self._value = min(self._value + step, self._target)
            else:
                self._value = max(self._value - step, self._target)

            # Update the rectangle width
            bar_width = int((self._width * self._value) / 100.0)
            self.coords(self._rect_id, 0, 0, bar_width, self._height)

            # Update color based on value
            if TTKBOOTSTRAP_AVAILABLE:
                # Try to use ttkbootstrap's gradient if available
                try:
                    pct = self._value / 100.0
                    r1, g1, b1 = int(self._start_color[1:3], 16), int(self._start_color[3:5], 16), int(self._start_color[5:7], 16)
                    r2, g2, b2 = int(self._end_color[1:3], 16), int(self._end_color[3:5], 16), int(self._end_color[5:7], 16)
                    r = int(r1 + (r2 - r1) * pct)
                    g = int(g1 + (g2 - g1) * pct)
                    b = int(b1 + (b2 - b1) * pct)
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    self.itemconfigure(self._rect_id, fill=color)
                except:
                    # Fall back to simple color
                    pass

        # Continue animation
        self.after(16, self._tick)


class SimpleMeter(ttk.Frame):
    """Simple meter widget"""
    def __init__(self, master, bootstyle="success", subtext="", **kwargs):
        super().__init__(master, **kwargs)

        # Create a canvas for drawing
        self.canvas = tk.Canvas(self, width=100, height=100,
                               highlightthickness=0, bg="#00000000")
        self.canvas.pack(fill="both", expand=True)

        # Store properties
        self.bootstyle = bootstyle
        self._value = 0

        # Draw the meter components
        self._draw_meter()

        # Add the subtext
        self._subtext = subtext
        self._text_id = self.canvas.create_text(
            50, 70, text=subtext, fill=self._get_color()
        )

    def _get_color(self):
        """Get color based on bootstyle"""
        if self.bootstyle == "success":
            return "#4CAF50"  # Green
        elif self.bootstyle == "warning":
            return "#FF9800"  # Orange
        elif self.bootstyle == "danger":
            return "#F44336"  # Red
        else:
            return "#9C27B0"  # Purple

    def _draw_meter(self):
        """Draw the initial meter"""
        # Draw outer circle
        self.canvas.create_oval(10, 10, 90, 90, outline=self._get_color(), width=2)

        # Create meter text
        self._meter_text = self.canvas.create_text(
            50, 50, text="0%", fill=self._get_color(), font=("Arial", 14, "bold")
        )

    def configure(self, **kwargs):
        """Configure the meter"""
        if "amountused" in kwargs:
            self._value = kwargs["amountused"]
            self.canvas.itemconfigure(self._meter_text, text=f"{int(self._value)}%")

        # Pass other kwargs to parent
        super().configure(**{k: v for k, v in kwargs.items() if k != "amountused"})


class Tooltip:
    """Simple tooltip for widgets"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None

        # Set up bindings
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        """Show the tooltip"""
        # Get widget position
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10

        # Create tooltip window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)  # No window decorations
        self.tooltip.wm_geometry(f"+{x}+{y}")

        # Create label with text
        style = ttk.Style()
        style.configure("Tooltip.TLabel", background="#555555", foreground="white")
        label = ttk.Label(self.tooltip, text=self.text,
                         style="Tooltip.TLabel", padding=(5, 3))
        label.pack()

    def hide(self, event=None):
        """Hide the tooltip"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class SimpleTelemetryThread(threading.Thread):
    """Thread generating mock telemetry data"""
    def __init__(self, message_queue):
        super().__init__(daemon=True)
        self.queue = message_queue
        self.running = True

    def run(self):
        """Generate mock data"""
        while self.running:
            # Send random values
            self.queue.put(("util", random.uniform(10, 90)))
            self.queue.put(("vram", random.uniform(20, 80)))
            self.queue.put(("tps", random.uniform(10, 50)))

            # Send at reasonable interval
            time.sleep(1)

    def stop(self):
        """Stop the thread"""
        self.running = False


# ========== Main UI Class ==========

class ModernDualGUI(tk.Tk):
    """Main application window with modern UI"""
    def __init__(self):
        super().__init__()
        self.title("DualGPUOptimizer - Modern UI")
        self.geometry("1150x730")
        self.configure(bg="#1A1A2E")  # Dark background

        # Set up message queue and telemetry
        self.bus = queue.Queue()
        self.tele = SimpleTelemetryThread(self.bus)

        # Initialize UI
        self._setup_theme()
        self._build_ui()

        # Start background processes
        self.tele.start()
        self.after(40, self._poll_queue)

        # Handle closing
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_theme(self):
        """Set up the application theme"""
        style = ttk.Style()

        if TTKBOOTSTRAP_AVAILABLE:
            style.theme_use("darkly")

        # Basic styles for all widgets
        style.configure("TFrame", background="#1A1A2E")
        style.configure("Card.TFrame", background="#222235", padding=12)
        style.configure("TLabel", foreground="#E6E6E6", background="#1A1A2E")
        style.configure("Card.TLabel", background="#222235")
        style.configure("Title.TLabel", font=("Arial", 14, "bold"))

        # Configure notebook
        style.configure("TNotebook", background="#1A1A2E", borderwidth=0)
        style.configure("TNotebook.Tab",
                       background="#222235",
                       foreground="#E6E6E6",
                       padding=(12, 5))

        # Configure selected tab
        style.map("TNotebook.Tab",
                 background=[("selected", "#9B59B6")],
                 foreground=[("selected", "#FFFFFF")])

    def _build_ui(self):
        """Build the main UI components"""
        # Header toolbar
        header = ttk.Frame(self, style="TFrame", padding=6)
        header.pack(fill="x", pady=(0, 4))

        NeonButton(header, text="Launch Model", command=self._on_launch).pack(side="left")
        NeonButton(header, text="New Session", command=self._on_new_session).pack(side="left", padx=6)

        # Theme toggle button
        ttk.Button(header, text="🌙/☀️", command=self._toggle_theme).pack(side="right", padx=6)

        # Main notebook with tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=6)

        # Create the tabs
        self._build_launcher_tab()
        self._build_dashboard_tab()
        self._build_chat_tab()

        # Status bar
        self.status_var = tk.StringVar(value="Ready - Modern UI Active")
        status_bar = ttk.Frame(self, style="TFrame", padding=2)
        status_bar.pack(fill="x", side="bottom")
        ttk.Label(status_bar, textvariable=self.status_var, anchor="e").pack(fill="x")

    def _build_launcher_tab(self):
        """Build the launcher tab"""
        # Create tab container
        tab = ttk.Frame(self.notebook, style="Card.TFrame")
        self.notebook.add(tab, text="Launcher")

        # Model path input
        ttk.Label(tab, text="Model Path:", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=4, pady=10)
        self.model_var = tk.StringVar(value="TheBloke/dolphin-2.2-yi-34b-200k-AWQ")
        model_entry = ttk.Entry(tab, textvariable=self.model_var, width=55)
        model_entry.grid(row=0, column=1, sticky="ew", padx=6)

        # Launch button
        self.launch_btn = NeonButton(tab, text="Launch", command=self._on_launch)
        self.launch_btn.grid(row=0, column=2, padx=8)
        Tooltip(self.launch_btn, "Start model with AWQ quantization")

        # Configure grid
        tab.columnconfigure(1, weight=1)

        # Output area
        ttk.Label(tab, text="Output Log:", style="Card.TLabel").grid(row=1, column=0, sticky="nw", padx=4, pady=6)
        self.out_box = tk.Text(tab, height=20, bg="#13141C", fg="#E6E6E6",
                              insertbackground="white")
        self.out_box.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=4, pady=4)
        tab.rowconfigure(2, weight=1)

    def _build_dashboard_tab(self):
        """Build the dashboard tab"""
        # Create tab container
        tab = ttk.Frame(self.notebook, style="Card.TFrame")
        self.notebook.add(tab, text="Dashboard")

        # GPU Utilization
        ttk.Label(tab, text="GPU Utilization:", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=4, pady=10)
        self.util_bar = GradientBar(tab)
        self.util_bar.grid(row=0, column=1, sticky="ew", padx=10)

        # VRAM Usage
        ttk.Label(tab, text="VRAM Usage:", style="Card.TLabel").grid(row=1, column=0, sticky="w", padx=4, pady=10)
        self.vram_bar = GradientBar(tab)
        self.vram_bar.grid(row=1, column=1, sticky="ew", padx=10)

        # Performance meter
        self.tps = SimpleMeter(tab, bootstyle="success", subtext="tok/s")
        self.tps.grid(row=0, column=2, rowspan=2, padx=20)

        # Layout
        tab.columnconfigure(1, weight=1)

        # Stats panel
        stats_frame = ttk.LabelFrame(tab, text="GPU Statistics", style="Card.TFrame")
        stats_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=20)

        for i, (label, value) in enumerate([
            ("Temperature:", "45°C"),
            ("Memory:", "8GB / 24GB"),
            ("Power:", "120W / 350W"),
            ("Fan Speed:", "35%")
        ]):
            ttk.Label(stats_frame, text=label, style="Card.TLabel").grid(row=i, column=0, sticky="w", padx=10, pady=6)
            ttk.Label(stats_frame, text=value, style="Card.TLabel").grid(row=i, column=1, sticky="w", padx=10, pady=6)

    def _build_chat_tab(self):
        """Build the chat tab"""
        # Create tab container
        tab = ttk.Frame(self.notebook, style="Card.TFrame")
        self.notebook.add(tab, text="Chat")

        # Message display area
        self.chat_display = tk.Text(tab, wrap="word", bg="#13141C", fg="#E6E6E6",
                                   highlightthickness=0, borderwidth=0)
        chat_scroll = ttk.Scrollbar(tab, command=self.chat_display.yview)
        self.chat_display.configure(yscrollcommand=chat_scroll.set)

        self.chat_display.pack(fill="both", expand=True, side="left", padx=(4, 0), pady=4)
        chat_scroll.pack(fill="y", side="right", padx=(0, 4), pady=4)

        # Input area
        input_frame = ttk.Frame(tab, style="Card.TFrame", padding=4)
        input_frame.pack(fill="x", side="bottom", padx=4, pady=4)

        self.chat_entry = tk.Text(input_frame, height=3, bg="#13141C", fg="#E6E6E6",
                                 wrap="word", highlightthickness=0, borderwidth=0)
        self.chat_entry.pack(fill="x", side="left", expand=True, padx=(0, 4))
        self.chat_entry.bind("<Control-Return>", self._on_send)

        send_btn = NeonButton(input_frame, text="Send", command=self._on_send)
        send_btn.pack(side="right")

        # Configure text tags for user/assistant messages
        self.chat_display.tag_configure("user", foreground="#FFFFFF", background="#371B59")
        self.chat_display.tag_configure("assistant", foreground="#E6E6E6")

    def _toggle_theme(self):
        """Toggle between light and dark themes"""
        # Just a placeholder
        if self.cget("bg") == "#1A1A2E":  # If dark
            # Light theme
            self.configure(bg="#F5F5F7")
            style = ttk.Style()
            style.configure("TFrame", background="#F5F5F7")
            style.configure("Card.TFrame", background="#EAEAEF")
            style.configure("TLabel", foreground="#333333", background="#F5F5F7")
            style.configure("Card.TLabel", background="#EAEAEF")
            self.status_var.set("Light theme activated")
        else:
            # Dark theme
            self.configure(bg="#1A1A2E")
            style = ttk.Style()
            style.configure("TFrame", background="#1A1A2E")
            style.configure("Card.TFrame", background="#222235")
            style.configure("TLabel", foreground="#E6E6E6", background="#1A1A2E")
            style.configure("Card.TLabel", background="#222235")
            self.status_var.set("Dark theme activated")

    def _on_new_session(self):
        """Create a new chat session"""
        # Clear chat display
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")

        # Show notification
        if TTKBOOTSTRAP_AVAILABLE:
            ToastNotification(title="New Session",
                            message="Started a new chat session",
                            duration=1800).show_toast()

        self.status_var.set("New session created")

    def _on_launch(self):
        """Launch the model (simulated)"""
        model = self.model_var.get()
        self.status_var.set(f"Launching {model}...")
        self.launch_btn.configure(state="disabled")

        # Fake model launch with delayed messages
        def fake_launch():
            msgs = [
                "Loading model configuration...",
                "Initializing CUDA context...",
                f"Loading {model}...",
                "Creating tensor parallel layers...",
                "Model loaded successfully!"
            ]

            for msg in msgs:
                # Sleep to simulate processing time
                time.sleep(0.7)
                # Schedule UI update on the main thread
                self.after(10, lambda m=msg: self._append_to_output(m))

            # Re-enable the button
            time.sleep(0.5)
            self.after(10, lambda: self.launch_btn.configure(state="normal"))
            self.after(10, lambda: self.status_var.set("Model loaded successfully"))

        # Run in a separate thread
        threading.Thread(target=fake_launch, daemon=True).start()

    def _append_to_output(self, text):
        """Append text to the output box"""
        self.out_box.insert("end", f"{text}\n")
        self.out_box.see("end")  # Auto-scroll

    def _on_send(self, event=None):
        """Handle sending a chat message"""
        # Get text from entry
        text = self.chat_entry.get("1.0", "end").strip()
        if not text:
            return

        # Clear the entry
        self.chat_entry.delete("1.0", "end")

        # Add user message to display
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"You: {text}\n\n", "user")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

        # Generate response in background thread
        threading.Thread(target=self._generate_response,
                        args=(text,), daemon=True).start()

    def _generate_response(self, user_text):
        """Generate a response to user message"""
        # Simulate thinking time
        time.sleep(1)

        # Create a response - just echo with reversed text as demo
        reversed_text = user_text[::-1]
        response = f"I received your message. Here it is reversed: {reversed_text}"

        # Display the response
        self.after(10, lambda: self._show_response(response))

    def _show_response(self, text):
        """Show assistant response in the chat"""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"Assistant: {text}\n\n", "assistant")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _poll_queue(self):
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

        # Schedule next poll
        self.after(40, self._poll_queue)

    def _on_close(self):
        """Handle window close"""
        # Stop the telemetry thread
        if hasattr(self, 'tele'):
            self.tele.stop()
        self.destroy()


# ========== Main Entry Point ==========

def main():
    """Main entry point"""
    try:
        app = ModernDualGUI()
        app.mainloop()
    except Exception as e:
        import traceback
        print(f"Error starting application: {e}")
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    main()