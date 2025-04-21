"""
Launcher tab for the DualGPUOptimizer GUI.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, scrolledtext
import queue
from typing import Dict, List, Optional, Callable, Any

from dualgpuopt.gpu_info import GPU
from dualgpuopt.runner import Runner


class LauncherTab(ttk.Frame):
    """Launcher tab that allows running models with optimized settings."""

    def __init__(self, parent: ttk.Frame, gpus: List[GPU]) -> None:
        """
        Initialize the launcher tab.

        Args:
            parent: Parent frame
            gpus: List of GPU objects
        """
        super().__init__(parent, padding=8)
        self.parent = parent
        self.gpus = gpus
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Launcher controls
        control_frame = ttk.Frame(self)
        control_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(0, 8))
        control_frame.columnconfigure(0, weight=0)

        # Framework selection
        ttk.Label(control_frame, text="Framework:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.framework_var = tk.StringVar(value="llama.cpp")
        framework_combo = ttk.Combobox(
            control_frame,
            textvariable=self.framework_var,
            values=["llama.cpp", "vLLM"],
            state="readonly",
            width=10
        )
        framework_combo.grid(row=0, column=1, sticky="w", padx=8)

        # Launch button
        self.launch_btn = ttk.Button(
            control_frame,
            text="Launch",
            command=self._start_runner
        )
        self.launch_btn.grid(row=0, column=2, padx=8)

        # Stop button
        self.stop_btn = ttk.Button(
            control_frame,
            text="Stop",
            command=self._stop_runner,
            state="disabled"
        )
        self.stop_btn.grid(row=0, column=3, padx=8)

        # Status indicator
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(control_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=4, padx=8)

        # Log output
        log_frame = ttk.LabelFrame(self, text="Process Output")
        log_frame.grid(row=1, column=0, sticky="news", padx=8, pady=(0, 8))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_text.grid(row=0, column=0, sticky="news", padx=8, pady=8)
        self.log_text.config(state="disabled")

        # Initialize runner
        self.runner = None

        # Auto-scroll control
        autoscroll_frame = ttk.Frame(log_frame)
        autoscroll_frame.grid(row=1, column=0, sticky="w", padx=8, pady=(0, 8))

        self.autoscroll_var = tk.BooleanVar(value=True)
        autoscroll_check = ttk.Checkbutton(
            autoscroll_frame,
            text="Auto-scroll",
            variable=self.autoscroll_var
        )
        autoscroll_check.grid(row=0, column=0, sticky="w")

        # Clear button
        clear_btn = ttk.Button(
            autoscroll_frame,
            text="Clear Log",
            command=self._clear_log
        )
        clear_btn.grid(row=0, column=1, padx=(8, 0))

    def _start_runner(self) -> None:
        """Start the selected model runner."""
        framework = self.framework_var.get()

        if self.runner is not None and self.runner.is_running():
            self.runner.terminate()
            self.runner = None

        # Setup logging queue
        log_queue = queue.Queue()

        # Create appropriate runner based on framework
        if framework == "llama.cpp":
            model_path = self.get_model_path()
            ctx = self.get_context_size()
            split = self.get_gpu_split()

            # Make sure we have all required inputs
            if not model_path:
                self._append_log("ERROR: No model path specified\n")
                return

            from dualgpuopt import optimizer
            cmd = optimizer.llama_command(model_path, ctx, split)

            # Create runner (needs to be implemented)
            self.runner = Runner(cmd, log_queue)

        elif framework == "vLLM":
            model_path = self.get_model_path()
            tp_size = len(self.gpus)

            # Make sure we have all required inputs
            if not model_path:
                self._append_log("ERROR: No model path specified\n")
                return

            from dualgpuopt import optimizer
            cmd = optimizer.vllm_command(model_path, tp_size)

            # Create runner
            self.runner = Runner(cmd, log_queue)

        # Start the process
        if self.runner:
            self.runner.start()
            self.launch_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.status_var.set("Running")

            # Start log polling
            self._poll_log(log_queue)

    def _stop_runner(self) -> None:
        """Stop the current runner."""
        if self.runner and self.runner.is_running():
            self.runner.terminate()
            self.status_var.set("Stopping...")
            self._append_log("Stopping process...\n")

        self.launch_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def _poll_log(self, log_queue: queue.Queue) -> None:
        """
        Poll the log queue for new output from the process.

        Args:
            log_queue: Queue containing log messages
        """
        try:
            # Process all available messages
            while not log_queue.empty():
                message = log_queue.get_nowait()
                self._append_log(message)
        except queue.Empty:
            pass

        # Check if process is still running
        if self.runner and self.runner.is_running():
            # Poll again after 100ms
            self.after(100, lambda: self._poll_log(log_queue))
        else:
            # Process has ended
            self.launch_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.status_var.set("Ready")
            self._append_log("\nProcess ended\n")

    def _append_log(self, text: str) -> None:
        """
        Append text to the log area.

        Args:
            text: Text to append
        """
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, text)

        # Auto-scroll if enabled
        if self.autoscroll_var.get():
            self.log_text.see(tk.END)

        self.log_text.config(state="disabled")

    def _clear_log(self) -> None:
        """Clear the log area."""
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

    def get_model_path(self) -> str:
        """
        Get the model path from the optimizer tab.

        Returns:
            Model path string
        """
        # This should be implemented to get the model path from the optimizer tab
        # For now, we'll try to access it from the parent's model_var
        try:
            parent_app = self.winfo_toplevel()
            if hasattr(parent_app, "model_var"):
                return parent_app.model_var.get()
        except Exception:
            pass
        return ""

    def get_context_size(self) -> int:
        """
        Get the context size from the optimizer tab.

        Returns:
            Context size integer
        """
        # This should be implemented to get the context size from the optimizer tab
        try:
            parent_app = self.winfo_toplevel()
            if hasattr(parent_app, "ctx_var"):
                return parent_app.ctx_var.get()
        except Exception:
            pass
        return 65536  # Default context size

    def get_gpu_split(self) -> str:
        """
        Get the GPU split string from the optimizer.

        Returns:
            GPU split string
        """
        from dualgpuopt import optimizer
        return optimizer.split_string(self.gpus)