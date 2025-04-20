from __future__ import annotations
import queue, threading, time, requests, sseclient
import ttkbootstrap as ttk
import tkinter as tk
from ttkbootstrap.widgets import Meter
from ttkbootstrap.scrolled import ScrolledFrame
from dualgpuopt.ui.chat_widgets import Bubble

BACKENDS = [
    {"name": "Dolphin 34B AWQ", "hf_id": "TheBloke/dolphin-2.2-yi-34b-200k-AWQ",
     "template": "<|im_start|>system\n{system}\n<|im_end|>\n<|im_start|>user\n{prompt}\n<|im_end|>\n<|im_start|>assistant\n"},
]

class ChatTab(ttk.Frame):
    def __init__(self, master, out_q: queue.Queue):
        super().__init__(master, padding=10)
        self.out_q = out_q
        
        # Configure grid for responsive layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)  # Message area should expand
        
        # Build interface components
        self._build_header()
        self._build_canvas()
        self._build_composer()
        
        # State variables
        self.last_prompt: str | None = None
        self.streaming = False
        
        # Bind to resize event
        self.bind("<Configure>", self._on_resize)

    # ------------ UI parts -------------
    def _build_header(self):
        """Build the header area with controls"""
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.columnconfigure(3, weight=1)  # Let the space between model/temp and clear button expand
        
        # Model selector
        ttk.Label(top, text="Model").grid(row=0, column=0, sticky="w")
        self.model_var = tk.StringVar(value=BACKENDS[0]["name"])
        model_menu = ttk.OptionMenu(top, self.model_var, BACKENDS[0]["name"],
                       *[b["name"] for b in BACKENDS])
        model_menu.grid(row=0, column=1, padx=(5, 15), sticky="w")
        
        # Temperature control with label
        ttk.Label(top, text="Temp").grid(row=0, column=2, sticky="w")
        self.temp = tk.DoubleVar(value=.7)
        temp_scale = ttk.Scale(top, variable=self.temp, from_=0.1, to=1.3, length=150,
                  orient="horizontal")
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
        sf = ScrolledFrame(self, autohide=True)
        sf.grid(row=1, column=0, sticky="nsew")
        
        # Create message container frame
        self.msg_frame = ttk.Frame(sf)
        self.msg_frame.pack(fill="both", expand=True, padx=5)
        
        # Make message frame columns flexible
        self.msg_frame.columnconfigure(0, weight=1)
        
        # Store scrolled frame reference for autoscrolling
        self.sf = sf

    def _build_composer(self):
        """Build the message composer area"""
        bottom = ttk.Frame(self)
        bottom.grid(row=2, column=0, sticky="ew", pady=(10, 0))
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
        meter_frame = ttk.Frame(self)
        meter_frame.grid(row=3, column=0, sticky="ew", pady=(5, 0))
        meter_frame.columnconfigure(0, weight=1)  # Left space expands
        
        # Status indicators on the right
        try:
            self.meter = Meter(meter_frame, subtext="tok/s", bootstyle="success", 
                              amounttotal=100, metersize=60, stripethickness=10)
            self.meter.pack(side="right")
            
            # Add token count label
            self.token_label = ttk.Label(meter_frame, text="0 tokens")
            self.token_label.pack(side="right", padx=(0, 15))
        except Exception as e:
            print(f"Could not create meter: {e}")
            self.meter = None
            self.token_label = ttk.Label(meter_frame, text="0 tokens")
            self.token_label.pack(side="right", padx=(0, 15))

    # ------------ actions --------------
    def _append(self, md: str, user=False):
        """Append a new message bubble to the chat
        
        Args:
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
        prompt = self.entry.get("1.0", "end").strip()
        if not prompt: return
        self.last_prompt = prompt
        self.entry.delete("1.0", "end")
        self._append(f"<b>You:</b> {prompt}", user=True)
        self._start_stream(prompt)

    def _regen(self):
        if self.last_prompt: self._start_stream(self.last_prompt)

    def _start_stream(self, prompt: str):
        if self.streaming: return
        cfg = next(b for b in BACKENDS if b["name"] == self.model_var.get())
        msg = cfg["template"].format(prompt=prompt, system="You are a helpful assistant.")
        self.streaming = True
        if self.meter is not None:
            self.meter.amountused = 0
        threading.Thread(target=self._worker,
                         args=(cfg["hf_id"], msg), daemon=True).start()

    def _worker(self, model_id: str, msg: str):
        t0 = time.perf_counter()
        tok = 0
        try:
            resp = requests.post("http://127.0.0.1:8000/v1/chat/completions",
                                 json={"model": model_id,
                                       "stream": True,
                                       "quantization": "awq",
                                       "messages":[{"role":"user","content": msg}]},
                                 stream=True, timeout=90)
            buff = ""
            for ev in sseclient.SSEClient(resp):
                delta = ev.data and ev.data["choices"][0]["delta"].get("content","")
                if delta:
                    buff += delta; tok += 1
                    self.out_q.put(("chat_chunk", delta))
            self.out_q.put(("chat_end", ""))
        except Exception as e:
            self.out_q.put(("chat_chunk", f"<br><i>Error: {e}</i>"))
        finally:
            self.streaming = False
            elapsed = max(time.perf_counter() - t0, .1)
            self.out_q.put(("tps", tok/elapsed))

    # --- exposed to main GUI poller ---
    def handle_queue(self, kind, val):
        """Handle messages from the queue
        
        Args:
            kind: Message type
            val: Message value
        """
        if kind == "chat_chunk": 
            # Add the new chunk of text to the chat
            self._append(val)
            
            # Update token counter if we have a label
            if hasattr(self, 'token_label') and self.token_label:
                # Extract current count and update
                try:
                    current_text = self.token_label.cget("text")
                    current_count = int(current_text.split()[0])
                    self.token_label.configure(text=f"{current_count + 1} tokens")
                except (ValueError, IndexError):
                    # If parsing fails, reset counter
                    self.token_label.configure(text="1 tokens")
                    
        elif kind == "chat_end":
            # Handle end of streaming
            pass
            
        elif kind == "tps" and self.meter is not None: 
            # Update tokens per second meter
            self.meter.configure(amountused=min(val, 100))

    def _clear(self):
        for w in self.msg_frame.winfo_children(): w.destroy()

    # ------------ responsive layout --------------
    def _on_resize(self, event=None):
        """Handle window resize events"""
        # Update UI based on new size
        self.after(100, self._update_layout)
    
    def _update_layout(self):
        """Update layout based on current window size"""
        width = self.winfo_width()
        
        # Adjust text entry height based on window width
        if width < 600:
            self.entry.configure(height=2)  # Smaller height for narrow windows
        else:
            self.entry.configure(height=4)  # Taller for wider windows 