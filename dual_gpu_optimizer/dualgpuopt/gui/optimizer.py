"""
GUI optimizer component for the DualGPUOptimizer application.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

import ttkbootstrap as ttkb

from dualgpuopt.gpu_info import probe_gpus, GPU
from dualgpuopt.optimizer import split_string, tensor_fractions
from dualgpuopt.services.state_service import state_service


class OptimizerWidget(ttk.Frame):
    """Widget for GPU optimization settings and recommendations."""

    def __init__(self, parent: tk.Widget) -> None:
        """Initialize the optimizer widget."""
        super().__init__(parent)

        self.gpus: list[GPU] = []
        self.split_var = tk.StringVar(value="")
        self.tensor_var = tk.StringVar(value="")

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the UI components."""
        # Main layout
        self.columnconfigure(0, weight=1)

        # GPU Detection section
        detect_frame = ttk.LabelFrame(self, text="GPU Detection", padding=10)
        detect_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.detect_btn = ttk.Button(
            detect_frame,
            text="Detect GPUs",
            command=self._detect_gpus,
            style="primary.TButton",
        )
        self.detect_btn.grid(row=0, column=0, padx=5, pady=5)

        self.gpu_info = ttk.Label(detect_frame, text="No GPUs detected yet")
        self.gpu_info.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        # Optimization results section
        results_frame = ttk.LabelFrame(self, text="Optimization Results", padding=10)
        results_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # Split string
        ttk.Label(results_frame, text="Recommended GPU Split:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )

        split_entry = ttk.Entry(
            results_frame, textvariable=self.split_var, width=40, state="readonly"
        )
        split_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Tensor fractions
        ttk.Label(results_frame, text="Tensor Parallel Fractions:").grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )

        tensor_entry = ttk.Entry(
            results_frame, textvariable=self.tensor_var, width=40, state="readonly"
        )
        tensor_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Action buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        ttk.Button(
            button_frame, text="Apply to Commands", command=self._apply_to_commands
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame, text="Save Configuration", command=self._save_config
        ).pack(side=tk.RIGHT, padx=5)

    def _detect_gpus(self) -> None:
        """Detect available GPUs and update the UI."""
        try:
            self.gpus = probe_gpus()

            if not self.gpus:
                self.gpu_info.config(text="No GPUs detected")
                return

            # Update GPU info text
            info_text = f"Detected {len(self.gpus)} GPUs:\n"
            for i, gpu in enumerate(self.gpus):
                info_text += f"GPU {i}: {gpu.name} - {gpu.mem_total} MiB total, {gpu.mem_free} MiB free\n"

            self.gpu_info.config(text=info_text)

            # Generate recommendations
            self._update_recommendations()

        except Exception as e:
            self.gpu_info.config(text=f"Error detecting GPUs: {str(e)}")

    def _update_recommendations(self) -> None:
        """Update the optimization recommendations."""
        if not self.gpus:
            return

        # Generate split string and tensor fractions
        split = split_string(self.gpus)
        fractions = tensor_fractions(self.gpus)

        # Update UI
        self.split_var.set(split)
        self.tensor_var.set(fractions)

    def _apply_to_commands(self) -> None:
        """Apply the optimization results to commands."""
        if not self.gpus:
            return

        # Save to state
        state_service.set("gpu_split", self.split_var.get())
        state_service.set("tensor_fractions", self.tensor_var.get())

        # TODO: Trigger event or update command view if implemented

    def _save_config(self) -> None:
        """Save the current configuration."""
        if not self.gpus:
            return

        # Save to state
        state_service.set("gpu_split", self.split_var.get())
        state_service.set("tensor_fractions", self.tensor_var.get())

        # Save state to disk
        state_service.save_state()


class OptimizerTab(ttk.Frame):
    """Notebook tab for GPU optimization settings."""

    def __init__(self, parent: tk.Widget, gpu_info_service: Any = None) -> None:
        """
        Initialize the optimizer tab.

        Args:
            parent: Parent widget
            gpu_info_service: Service for accessing GPU information
        """
        super().__init__(parent)

        # Store GPU info service
        self.gpu_info = gpu_info_service

        # Configure tab layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Create optimizer widget
        self.optimizer = OptimizerWidget(self)
        self.optimizer.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Advanced options frame
        advanced_frame = ttk.LabelFrame(self, text="Advanced Options", padding=10)
        advanced_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # Model configuration options
        model_frame = ttk.Frame(advanced_frame)
        model_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(model_frame, text="Model Path:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.model_path = ttk.Entry(model_frame, width=50)
        self.model_path.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(model_frame, text="Browse...", command=self._browse_model).grid(
            row=0, column=2, padx=5, pady=5
        )

        ttk.Label(model_frame, text="Context Size:").grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        self.context_size = ttk.Spinbox(
            model_frame, from_=1024, to=131072, increment=1024, width=10
        )
        self.context_size.set("65536")
        self.context_size.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Command generation options
        cmd_frame = ttk.Frame(advanced_frame)
        cmd_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(cmd_frame, text="Framework:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.framework = ttk.Combobox(
            cmd_frame, values=["llama.cpp", "vLLM", "Text Generation WebUI"], width=20
        )
        self.framework.current(0)
        self.framework.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Apply button
        ttk.Button(
            advanced_frame,
            text="Generate Commands",
            style="primary.TButton",
            command=self._generate_commands,
        ).pack(pady=10)

        # Command output
        self.cmd_output = ttkb.Text(advanced_frame, height=6, width=80, wrap=tk.WORD)
        self.cmd_output.pack(fill=tk.X, padx=5, pady=5)

        # Load saved state
        self._load_state()

    def _browse_model(self) -> None:
        """Open file dialog to browse for model path."""
        # This would use tkinter.filedialog in a real implementation
        pass

    def _generate_commands(self) -> None:
        """Generate framework-specific commands based on settings."""
        if not self.optimizer.gpus:
            self.cmd_output.delete(1.0, tk.END)
            self.cmd_output.insert(tk.END, "Please detect GPUs first")
            return

        framework = self.framework.get()
        model_path = self.model_path.get()
        context_size = self.context_size.get()

        if not model_path:
            self.cmd_output.delete(1.0, tk.END)
            self.cmd_output.insert(tk.END, "Please enter model path")
            return

        try:
            ctx = int(context_size)
        except ValueError:
            ctx = 65536

        # Generate command based on framework
        command = ""
        if framework == "llama.cpp":
            command = f"./main -m {model_path} -c {ctx} --gpu-split {self.optimizer.split_var.get()}"
        elif framework == "vLLM":
            command = f"python -m vllm.entrypoints.openai.api_server --model {model_path} --tensor-parallel-size 2"

        self.cmd_output.delete(1.0, tk.END)
        self.cmd_output.insert(tk.END, command)

    def _load_state(self) -> None:
        """Load settings from state service."""
        model_path = state_service.get("model_path", "")
        context_size = state_service.get("context_size", 65536)

        if model_path:
            self.model_path.delete(0, tk.END)
            self.model_path.insert(0, model_path)

        self.context_size.delete(0, tk.END)
        self.context_size.insert(0, str(context_size))
