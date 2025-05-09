from __future__ import annotations

import logging
import queue
import threading
import time
import tkinter as tk

# Configure logger
# Configure logger
from dualgpuopt.engine.pool import EnginePool
from dualgpuopt.ui.chat_compat import DEPENDENCIES as CHAT_DEPENDENCIES

# Configure logger
logger = logging.getLogger("DualGPUOpt.ChatTab")

# Use dependencies from the compatibility layer
if CHAT_DEPENDENCIES["requests"]["available"] and CHAT_DEPENDENCIES["sseclient"]["available"]:
    requests = CHAT_DEPENDENCIES["requests"]["module"]
    sseclient = CHAT_DEPENDENCIES["sseclient"]["module"]
    CHAT_DEPS_AVAILABLE = True
    logger.info("Chat dependencies available via compatibility layer")
else:
    CHAT_DEPS_AVAILABLE = False
    logger.warning(
        "Chat dependencies (requests/sseclient) not available - chat functionality will be limited",
    )

# Try importing ttkbootstrap - fall back to standard ttk if not available
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.scrolled import ScrolledFrame
    from ttkbootstrap.widgets import Meter

    TTKBOOTSTRAP_AVAILABLE = True
except ImportError:
    from tkinter import ttk

    TTKBOOTSTRAP_AVAILABLE = False

    # Mock the missing classes
    class Meter:
        def __init__(self, *args, **kwargs):
            self.frame = ttk.Frame(*args)
            self.label = ttk.Label(self.frame, text="Meter not available")
            self.label.pack()

        def pack(self, *args, **kwargs):
            self.frame.pack(*args, **kwargs)

        def configure(self, **kwargs):
            pass

    class ScrolledFrame(ttk.Frame):
        def __init__(self, parent, **kwargs):
            super().__init__(parent)
            self.canvas = tk.Canvas(self)
            self.canvas.pack(fill="both", expand=True)

        def pack(self, *args, **kwargs):
            super().pack(*args, **kwargs)


# Try to import the UI chat widgets
try:
    from dualgpuopt.ui.chat_widgets import Bubble

    CHAT_WIDGETS_AVAILABLE = True
except ImportError:
    CHAT_WIDGETS_AVAILABLE = False

    # Create a fallback Bubble implementation
    class Bubble(ttk.Frame):
        def __init__(self, parent, text, is_user=False):
            super().__init__(parent)
            bg_color = "#3D2A50" if not is_user else "#6A3EBD"
            self.label = ttk.Label(self, text=text, wraplength=400, background=bg_color, padding=10)
            self.label.pack(
                side="right" if is_user else "left",
                anchor="e" if is_user else "w",
                pady=5,
                padx=5,
            )


BACKENDS = [
    {
        "name": "Dolphin 34B AWQ",
        "hf_id": "TheBloke/dolphin-2.2-yi-34b-200k-AWQ",
        "template": "<|im_start|>system\n{system}\n<|im_end|>\n<|im_start|>user\n{prompt}\n<|im_end|>\n<|im_start|>assistant\n",
    },
]


class ChatTab(ttk.Frame):
    def __init__(self, master, out_q: queue.Queue):
        super().__init__(master, padding=10)
        self.out_q = out_q

        # Configure grid for responsive layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)  # Message area should expand

        # Check for required dependencies
        if not CHAT_DEPS_AVAILABLE:
            self._build_dependency_notice()
            return

        # Build interface components
        self._build_header()

        # Create a horizontal paned window for resizable chat layout
        self.h_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.h_paned.grid(row=1, column=0, sticky="nsew")

        # Main chat area container
        self.chat_container = ttk.Frame(self.h_paned)
        self.h_paned.add(self.chat_container, weight=75)

        # Sidebar for metrics and history
        self.sidebar = ttk.Frame(self.h_paned)
        self.h_paned.add(self.sidebar, weight=25)

        # Build chat canvas in the main container
        self._build_canvas()

        # Build sidebar content
        self._build_sidebar()

        # Build composer area
        self._build_composer()

        # State variables
        self.last_prompt: str | None = None
        self.streaming = False

        # Bind to resize event
        self.bind("<Configure>", self._on_resize)

    def _build_dependency_notice(self):
        """Build a notice about missing dependencies"""
        notice_frame = ttk.Frame(self, padding=20)
        notice_frame.grid(row=0, column=0, sticky="nsew")

        title = ttk.Label(
            notice_frame,
            text="Chat Functionality Unavailable",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(pady=(20, 10))

        msg = "The chat functionality requires additional dependencies that are not installed:"
        ttk.Label(notice_frame, text=msg).pack(pady=5)

        deps = ttk.Label(notice_frame, text="• requests\n• sseclient-py", justify="left")
        deps.pack(pady=5)

        install_msg = "You can install these dependencies with:"
        ttk.Label(notice_frame, text=install_msg).pack(pady=5)

        install_cmd = ttk.Label(
            notice_frame,
            text="pip install requests sseclient-py",
            font=("Courier New", 10),
            background="#241934",
            padding=10,
        )
        install_cmd.pack(pady=5)

        alt_msg = "Or run the dependency installer:"
        ttk.Label(notice_frame, text=alt_msg).pack(pady=5)

        alt_cmd = ttk.Label(
            notice_frame,
            text="python -m dualgpuopt --install-deps",
            font=("Courier New", 10),
            background="#241934",
            padding=10,
        )
        alt_cmd.pack(pady=5)

        # Add function availability info
        functions = ttk.Label(
            notice_frame,
            text="This tab will remain available but chat functionality will be disabled.",
        )
        functions.pack(pady=20)

    # ------------ UI parts -------------
    def _build_header(self):
        """Build the header area with controls"""
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.columnconfigure(3, weight=1)  # Let the space between model/temp and clear button expand

        # Model selector
        ttk.Label(top, text="Model").grid(row=0, column=0, sticky="w")
        self.model_var = tk.StringVar(value=BACKENDS[0]["name"])
        model_menu = ttk.OptionMenu(
            top,
            self.model_var,
            BACKENDS[0]["name"],
            *[b["name"] for b in BACKENDS],
        )
        model_menu.grid(row=0, column=1, padx=(5, 15), sticky="w")

        # Temperature control with label
        ttk.Label(top, text="Temp").grid(row=0, column=2, sticky="w")
        self.temp = tk.DoubleVar(value=0.7)
        temp_scale = ttk.Scale(
            top,
            variable=self.temp,
            from_=0.1,
            to=1.3,
            length=150,
            orient="horizontal",
        )
        temp_scale.grid(row=0, column=3, padx=(5, 10), sticky="ew")

        # Temperature value display
        temp_value = ttk.Label(top, text="0.7")
        temp_value.grid(row=0, column=4, padx=(0, 15), sticky="w")

        # Update temp value when slider moves
        def _update_temp_value(*args):
            temp_value.configure(text=f"{self.temp.get():.1f}")

        self.temp.trace_add("write", _update_temp_value)

        # Clear button
        clear_btn = ttk.Button(top, text="Clear Chat", command=self._clear)
        clear_btn.grid(row=0, column=5, sticky="e")

    def _build_canvas(self):
        """Build the scrollable message area"""
        # Create scrolled frame with autohide scrollbar
        sf = ScrolledFrame(self.chat_container, autohide=True)
        sf.grid(row=0, column=0, sticky="nsew")

        # Create message container frame
        self.msg_frame = ttk.Frame(sf)
        self.msg_frame.pack(fill="both", expand=True, padx=5)

        # Make message frame columns flexible
        self.msg_frame.columnconfigure(0, weight=1)

        # Store scrolled frame reference for autoscrolling
        self.sf = sf

    def _build_composer(self):
        """Build the message composer area"""
        bottom = ttk.Frame(self.chat_container)
        bottom.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        bottom.columnconfigure(0, weight=1)  # Text area should expand

        # Message input with larger height and placeholder
        self.entry = tk.Text(bottom, height=4, wrap="word")
        self.entry.grid(row=0, column=0, sticky="ew")

        # Set placeholder text and styling
        self.entry.insert("1.0", "Type your message here...")
        self.entry.configure(fg="gray")

        # Handle placeholder text
        def _on_entry_focus_in(event):
            if self.entry.get("1.0", "end-1c") == "Type your message here...":
                self.entry.delete("1.0", "end")
                self.entry.configure(fg="white")

        def _on_entry_focus_out(event):
            if not self.entry.get("1.0", "end-1c").strip():
                self.entry.delete("1.0", "end")
                self.entry.insert("1.0", "Type your message here...")
                self.entry.configure(fg="gray")

        self.entry.bind("<FocusIn>", _on_entry_focus_in)
        self.entry.bind("<FocusOut>", _on_entry_focus_out)

        # Add keyboard shortcuts
        self.entry.bind("<Control-Return>", self._on_send)
        self.entry.bind("<Command-Return>", self._on_send)  # Mac

        # Control buttons frame
        btn_frame = ttk.Frame(bottom)
        btn_frame.grid(row=0, column=1, sticky="ns", padx=(10, 0))

        # Send button
        send_btn = ttk.Button(btn_frame, text="Send ▷", command=self._on_send)
        send_btn.pack(fill="x", expand=True, pady=(0, 5))

        # Regenerate button
        regen_btn = ttk.Button(btn_frame, text="⟲ Regenerate", command=self._regen)
        regen_btn.pack(fill="x", expand=True)

        # Token rate meter below the composer
        meter_frame = ttk.Frame(self.chat_container)
        meter_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        meter_frame.columnconfigure(0, weight=1)  # Left space expands

        # Status indicators on the right
        try:
            if TTKBOOTSTRAP_AVAILABLE:
                self.meter = Meter(
                    meter_frame,
                    subtext="tok/s",
                    bootstyle="success",
                    amounttotal=100,
                    metersize=60,
                    stripethickness=10,
                )
                self.meter.pack(side="right")
            else:
                # Fallback for when ttkbootstrap is not available
                self.meter = None
                ttk.Label(meter_frame, text="tok/s").pack(side="right")

            # Add token count label
            self.token_label = ttk.Label(meter_frame, text="0 tokens")
            self.token_label.pack(side="right", padx=(0, 15))
        except Exception as e:
            logger.error(f"Could not create meter: {e}")
            self.meter = None
            self.token_label = ttk.Label(meter_frame, text="0 tokens")
            self.token_label.pack(side="right", padx=(0, 15))

    def _build_sidebar(self):
        """Build the sidebar with chat metrics and history"""
        # Create a styled frame for the sidebar
        sidebar_frame = ttk.LabelFrame(self.sidebar, text="Chat Metrics", padding=10)
        sidebar_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Add metrics display
        metrics_frame = ttk.Frame(sidebar_frame)
        metrics_frame.pack(fill="x", pady=5)

        # Token count display
        ttk.Label(metrics_frame, text="Total Tokens:").grid(row=0, column=0, sticky="w", pady=2)
        self.total_tokens_var = tk.StringVar(value="0")
        ttk.Label(metrics_frame, textvariable=self.total_tokens_var).grid(
            row=0,
            column=1,
            sticky="e",
            pady=2,
        )

        # Messages count
        ttk.Label(metrics_frame, text="Messages:").grid(row=1, column=0, sticky="w", pady=2)
        self.message_count_var = tk.StringVar(value="0")
        ttk.Label(metrics_frame, textvariable=self.message_count_var).grid(
            row=1,
            column=1,
            sticky="e",
            pady=2,
        )

        # Generation speed
        ttk.Label(metrics_frame, text="Speed:").grid(row=2, column=0, sticky="w", pady=2)
        self.speed_var = tk.StringVar(value="0 tok/s")
        ttk.Label(metrics_frame, textvariable=self.speed_var).grid(
            row=2,
            column=1,
            sticky="e",
            pady=2,
        )

        # History section
        history_frame = ttk.LabelFrame(sidebar_frame, text="History", padding=5)
        history_frame.pack(fill="both", expand=True, pady=10)

        # Listbox for chat history
        self.history_list = tk.Listbox(history_frame, height=10)
        self.history_list.pack(fill="both", expand=True)

        # Add some sample history items
        for i in range(1, 4):
            self.history_list.insert(tk.END, f"Chat {i}")

        # Bind double click to reload chat
        self.history_list.bind("<Double-1>", self._load_history)

        # Action buttons
        btn_frame = ttk.Frame(sidebar_frame)
        btn_frame.pack(fill="x", pady=5)

        # Export button
        ttk.Button(btn_frame, text="Export Chat", command=self._export_chat).pack(
            side="left",
            padx=2,
        )

        # Clear history button
        ttk.Button(btn_frame, text="Clear History", command=self._clear_history).pack(
            side="right",
            padx=2,
        )

    # ------------ actions --------------
    def _append(self, md: str, user=False):
        """
        Append a new message bubble to the chat

        Args:
        ----
            md: Markdown/HTML formatted message content
            user: True if this is a user message
        """
        # Create and add the bubble
        bubble = Bubble(self.msg_frame, md, user)
        bubble.pack(fill="x")

        # Update the UI
        self.msg_frame.update_idletasks()

        # Use the ScrolledFrame for proper scrolling to bottom
        self.after(10, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        """Scroll the message area to the bottom"""
        # Get the scrollable canvas from ScrolledFrame
        canvas = self.sf.canvas
        canvas.update_idletasks()
        canvas.yview_moveto(1.0)

        # Ensure the message is visible by forcing another update
        self.sf.update_idletasks()

    def _on_send(self, *_):
        # Check if chat dependencies are available
        if not CHAT_DEPS_AVAILABLE:
            self._show_dependency_error()
            return

        prompt = self.entry.get("1.0", "end").strip()
        if not prompt:
            return
        self.last_prompt = prompt
        self.entry.delete("1.0", "end")
        self._append(f"<b>You:</b> {prompt}", user=True)
        self._start_stream(prompt)

    def _show_dependency_error(self):
        """Show a message about missing dependencies"""
        self._append(
            "<b>System:</b> Chat functionality requires additional dependencies.",
            user=False,
        )
        self._append(
            "<b>System:</b> Please install 'requests' and 'sseclient-py' to enable chat.",
            user=False,
        )
        self._append(
            "<b>System:</b> Run: <code>pip install requests sseclient-py</code>",
            user=False,
        )

    def _regen(self):
        # Check if chat dependencies are available
        if not CHAT_DEPS_AVAILABLE:
            self._show_dependency_error()
            return

        if self.last_prompt:
            self._start_stream(self.last_prompt)

    def _start_stream(self, prompt: str):
        if self.streaming:
            return
        cfg = next(b for b in BACKENDS if b["name"] == self.model_var.get())
        msg = cfg["template"].format(prompt=prompt, system="You are a helpful assistant.")
        self.streaming = True
        if self.meter is not None:
            self.meter.configure(amountused=0)
        threading.Thread(target=self._worker, args=(cfg["hf_id"], msg), daemon=True).start()

    def _worker(self, model_id: str, msg: str):
        if not CHAT_DEPS_AVAILABLE:
            self.out_q.put(("chat_chunk", "<b>Error:</b> Chat dependencies not available"))
            self.out_q.put(("chat_end", ""))
            self.streaming = False
            return

        t0 = time.perf_counter()
        tok = 0
        try:
            # Get the engine from the pool, which will reuse if already loaded
            engine = EnginePool.get(model_id, quant="awq")

            # Stream from the engine directly, which handles backend communication
            for token in engine.stream(msg):
                self.out_q.put(("chat_chunk", token))
                tok += 1

            self.out_q.put(("chat_end", ""))
        except Exception as e:
            logger.error(f"Chat error: {e}")
            self.out_q.put(("chat_chunk", f"<br><i>Error: {e}</i>"))
        finally:
            self.streaming = False
            elapsed = max(time.perf_counter() - t0, 0.1)
            self.out_q.put(("tps", tok / elapsed))

    # --- exposed to main GUI poller ---
    def handle_queue(self, kind, val):
        """
        Handle messages from the queue

        Args:
        ----
            kind: Message type
            val: Message value
        """
        if kind == "chat_chunk":
            # Add the new chunk of text to the chat
            self._append(val)

            # Update token counter if we have a label
            if hasattr(self, "token_label") and self.token_label:
                # Extract current count and update
                try:
                    current_text = self.token_label.cget("text")
                    current_count = int(current_text.split()[0])
                    new_count = current_count + 1
                    self.token_label.configure(text=f"{new_count} tokens")

                    # Update sidebar metrics
                    if hasattr(self, "total_tokens_var"):
                        self.total_tokens_var.set(str(new_count))
                except (ValueError, IndexError):
                    # If parsing fails, reset counter
                    self.token_label.configure(text="1 tokens")
                    if hasattr(self, "total_tokens_var"):
                        self.total_tokens_var.set("1")

        elif kind == "chat_end":
            # Handle end of streaming
            # Update message count in sidebar
            if hasattr(self, "message_count_var"):
                try:
                    current = int(self.message_count_var.get())
                    self.message_count_var.set(str(current + 1))
                except ValueError:
                    self.message_count_var.set("1")

        elif kind == "tps" and self.meter is not None:
            # Update tokens per second meter
            self.meter.configure(amountused=min(val, 100))

            # Update speed in sidebar
            if hasattr(self, "speed_var"):
                self.speed_var.set(f"{int(val)} tok/s")

    def _clear(self):
        if hasattr(self, "msg_frame"):
            for w in self.msg_frame.winfo_children():
                w.destroy()

    def _load_history(self, event=None):
        """Load a previous chat from history"""
        # Get selected item
        if hasattr(self, "history_list") and self.history_list.curselection():
            idx = self.history_list.curselection()[0]
            selected = self.history_list.get(idx)
            # In a real implementation, this would load the chat
            # For now, just show a message
            self._append(f"<i>Loading {selected}...</i>")

    def _export_chat(self):
        """Export the current chat to a file"""
        # In a real implementation, this would save to a file
        # For now, just show a message
        self._append("<i>Chat exported to file...</i>")

    def _clear_history(self):
        """Clear the chat history"""
        if hasattr(self, "history_list"):
            self.history_list.delete(0, tk.END)

    # ------------ responsive layout --------------
    def _on_resize(self, event=None):
        """Handle window resize events"""
        # Update UI based on new size
        self.after(100, self._update_layout)

    def _update_layout(self):
        """Update layout based on current window size"""
        # Skip if this is the dependency notice version of the tab
        if not hasattr(self, "entry") or not hasattr(self, "h_paned"):
            return

        width = self.winfo_width()

        # Adjust text entry height based on window width
        if width < 600:
            self.entry.configure(height=2)  # Smaller height for narrow windows
        else:
            self.entry.configure(height=4)  # Taller for wider windows

        # Adjust horizontal pane position based on window width
        try:
            if width > 1200:
                # For wide windows, show more of the chat area
                self.h_paned.sashpos(0, int(width * 0.75))
            elif width > 800:
                # Medium width
                self.h_paned.sashpos(0, int(width * 0.7))
            else:
                # For narrow windows, minimize the sidebar
                self.h_paned.sashpos(0, int(width * 0.8))
        except (tk.TclError, AttributeError):
            # Handle case where sash may not be available yet
            pass
