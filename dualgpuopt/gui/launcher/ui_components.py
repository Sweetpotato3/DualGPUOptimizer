"""
UI components for the launcher module.

This module contains UI components for the launcher tab.
"""
from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk, filedialog
import os
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

# Try to import ttkbootstrap components
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    TTKBOOTSTRAP_AVAILABLE = True
except ImportError:
    import tkinter.ttk as ttk
    TTKBOOTSTRAP_AVAILABLE = False

from dualgpuopt.gpu_info import GPU
from dualgpuopt.services.event_service import event_bus


class LauncherTab(ttk.Frame):
    """Tab for launching models with optimized parameters."""

    def __init__(self, parent: ttk.Frame, gpus: List[GPU] = None) -> None:
        """
        Initialize the launcher tab.

        Args:
            parent: Parent frame
            gpus: List of GPU objects
        """
        super().__init__(parent)
        self.parent = parent
        self.gpus = gpus or []
        self.logger = logging.getLogger("dualgpuopt.gui.launcher.tab")

        # Set padding
        self.PAD = 10

        # Configure grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Model selection frame
        self.rowconfigure(1, weight=0)  # Framework selection frame
        self.rowconfigure(2, weight=1)  # Parameters frame
        self.rowconfigure(3, weight=0)  # Execution frame

        # Initialize UI components
        self._init_ui()

        # Register event handlers
        self._register_event_handlers()

    def _register_event_handlers(self) -> None:
        """Register event handlers."""
        event_bus.subscribe("gpu_list_updated", self._handle_gpu_update)
        event_bus.subscribe("process_exited", self._handle_process_exit)

    def _handle_gpu_update(self, data: Dict[str, Any]) -> None:
        """
        Handle GPU list updates.

        Args:
            data: Event data containing updated GPU list
        """
        if "gpus" in data:
            self.gpus = data["gpus"]
            self.logger.debug(f"Updated GPU list in launcher tab: {len(self.gpus)} GPUs")
            # Update UI based on new GPU list
            self._update_gpu_display()

    def _handle_process_exit(self, data: Dict[str, Any]) -> None:
        """
        Handle process exit events.

        Args:
            data: Event data containing process exit information
        """
        process_id = data.get("process_id", "")
        return_code = data.get("return_code", -1)

        self.logger.info(f"Process {process_id} exited with code {return_code}")

        # Update UI based on process exit
        self._update_process_status(process_id, return_code)

    def _init_ui(self) -> None:
        """Initialize UI components."""
        # Create model selection frame
        self._init_model_selection()

        # Create framework selection frame
        self._init_framework_selection()

        # Create parameters frame
        self._init_parameters_frame()

        # Create execution frame
        self._init_execution_frame()

    def _init_model_selection(self) -> None:
        """Initialize model selection components."""
        model_frame = ttk.LabelFrame(self, text="Model Selection", padding=self.PAD)
        model_frame.grid(row=0, column=0, sticky="ew", padx=self.PAD, pady=self.PAD)
        model_frame.columnconfigure(1, weight=1)

        # Model path
        ttk.Label(model_frame, text="Model path:").grid(row=0, column=0, sticky="w", padx=self.PAD, pady=5)

        # Frame for path entry and browse button
        path_frame = ttk.Frame(model_frame)
        path_frame.grid(row=0, column=1, sticky="ew", padx=self.PAD, pady=5)
        path_frame.columnconfigure(0, weight=1)

        # Model path entry
        self.model_path_var = tk.StringVar()
        self.model_path_entry = ttk.Entry(path_frame, textvariable=self.model_path_var)
        self.model_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Browse button
        browse_button = ttk.Button(path_frame, text="Browse", command=self._browse_model)
        browse_button.grid(row=0, column=1)

        # Model presets
        ttk.Label(model_frame, text="Model preset:").grid(row=1, column=0, sticky="w", padx=self.PAD, pady=5)

        self.model_preset_var = tk.StringVar()
        preset_values = ["Custom", "Llama-2-7B", "Llama-2-13B", "Llama-2-70B", "Mistral-7B"]
        self.model_preset_combo = ttk.Combobox(
            model_frame,
            textvariable=self.model_preset_var,
            values=preset_values,
            state="readonly"
        )
        self.model_preset_combo.current(0)
        self.model_preset_combo.grid(row=1, column=1, sticky="w", padx=self.PAD, pady=5)
        self.model_preset_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)

    def _init_framework_selection(self) -> None:
        """Initialize framework selection components."""
        framework_frame = ttk.LabelFrame(self, text="Framework", padding=self.PAD)
        framework_frame.grid(row=1, column=0, sticky="ew", padx=self.PAD, pady=self.PAD)

        # Framework selection
        self.framework_var = tk.StringVar(value="llama.cpp")

        llama_radio = ttk.Radiobutton(
            framework_frame,
            text="llama.cpp",
            variable=self.framework_var,
            value="llama.cpp",
            command=self._on_framework_changed
        )
        llama_radio.grid(row=0, column=0, padx=self.PAD, pady=5, sticky="w")

        vllm_radio = ttk.Radiobutton(
            framework_frame,
            text="vLLM",
            variable=self.framework_var,
            value="vllm",
            command=self._on_framework_changed
        )
        vllm_radio.grid(row=0, column=1, padx=self.PAD, pady=5, sticky="w")

    def _init_parameters_frame(self) -> None:
        """Initialize parameters components."""
        params_frame = ttk.LabelFrame(self, text="Parameters", padding=self.PAD)
        params_frame.grid(row=2, column=0, sticky="nsew", padx=self.PAD, pady=self.PAD)
        params_frame.columnconfigure(1, weight=1)

        # Container for framework-specific parameter frames
        self.params_container = ttk.Frame(params_frame)
        self.params_container.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.params_container.columnconfigure(0, weight=1)

        # Create parameter frames for each framework
        self.llama_params_frame = self._create_llama_params_frame(self.params_container)
        self.vllm_params_frame = self._create_vllm_params_frame(self.params_container)

        # Show initial frame based on selected framework
        self._on_framework_changed()

    def _create_llama_params_frame(self, parent: ttk.Frame) -> ttk.Frame:
        """
        Create parameters frame for llama.cpp.

        Args:
            parent: Parent frame

        Returns:
            Parameters frame
        """
        frame = ttk.Frame(parent)
        frame.columnconfigure(1, weight=1)

        # Context size
        ttk.Label(frame, text="Context size:").grid(row=0, column=0, sticky="w", padx=self.PAD, pady=5)
        self.ctx_size_var = tk.IntVar(value=2048)
        ctx_size_entry = ttk.Entry(frame, textvariable=self.ctx_size_var, width=10)
        ctx_size_entry.grid(row=0, column=1, sticky="w", padx=self.PAD, pady=5)

        # Batch size
        ttk.Label(frame, text="Batch size:").grid(row=1, column=0, sticky="w", padx=self.PAD, pady=5)
        self.batch_size_var = tk.IntVar(value=1)
        batch_size_entry = ttk.Entry(frame, textvariable=self.batch_size_var, width=10)
        batch_size_entry.grid(row=1, column=1, sticky="w", padx=self.PAD, pady=5)

        # Threads
        ttk.Label(frame, text="Threads:").grid(row=2, column=0, sticky="w", padx=self.PAD, pady=5)
        self.threads_var = tk.IntVar(value=4)
        threads_entry = ttk.Entry(frame, textvariable=self.threads_var, width=10)
        threads_entry.grid(row=2, column=1, sticky="w", padx=self.PAD, pady=5)

        # GPU Split
        ttk.Label(frame, text="GPU Split:").grid(row=3, column=0, sticky="w", padx=self.PAD, pady=5)
        self.gpu_split_var = tk.StringVar(value="auto")

        gpu_split_frame = ttk.Frame(frame)
        gpu_split_frame.grid(row=3, column=1, sticky="w", padx=self.PAD, pady=5)

        gpu_split_entry = ttk.Entry(gpu_split_frame, textvariable=self.gpu_split_var, width=10)
        gpu_split_entry.pack(side="left", padx=(0, 5))

        ttk.Button(gpu_split_frame, text="Optimize", command=self._optimize_gpu_split).pack(side="left")

        return frame

    def _create_vllm_params_frame(self, parent: ttk.Frame) -> ttk.Frame:
        """
        Create parameters frame for vLLM.

        Args:
            parent: Parent frame

        Returns:
            Parameters frame
        """
        frame = ttk.Frame(parent)
        frame.columnconfigure(1, weight=1)

        # Tensor parallel size
        ttk.Label(frame, text="Tensor parallel size:").grid(row=0, column=0, sticky="w", padx=self.PAD, pady=5)

        tp_frame = ttk.Frame(frame)
        tp_frame.grid(row=0, column=1, sticky="w", padx=self.PAD, pady=5)

        self.tp_size_var = tk.StringVar(value="auto")
        tp_size_entry = ttk.Entry(tp_frame, textvariable=self.tp_size_var, width=10)
        tp_size_entry.pack(side="left", padx=(0, 5))

        ttk.Label(tp_frame, text=f"(Max: {len(self.gpus)})").pack(side="left")

        # Max memory
        ttk.Label(frame, text="Max memory:").grid(row=1, column=0, sticky="w", padx=self.PAD, pady=5)
        self.max_memory_var = tk.StringVar(value="auto")
        max_memory_entry = ttk.Entry(frame, textvariable=self.max_memory_var, width=10)
        max_memory_entry.grid(row=1, column=1, sticky="w", padx=self.PAD, pady=5)

        # Max model length
        ttk.Label(frame, text="Max model length:").grid(row=2, column=0, sticky="w", padx=self.PAD, pady=5)
        self.max_model_len_var = tk.IntVar(value=8192)
        max_model_len_entry = ttk.Entry(frame, textvariable=self.max_model_len_var, width=10)
        max_model_len_entry.grid(row=2, column=1, sticky="w", padx=self.PAD, pady=5)

        return frame

    def _init_execution_frame(self) -> None:
        """Initialize execution components."""
        exec_frame = ttk.Frame(self, padding=self.PAD)
        exec_frame.grid(row=3, column=0, sticky="ew", padx=self.PAD, pady=self.PAD)
        exec_frame.columnconfigure(0, weight=1)

        # Command preview
        preview_frame = ttk.LabelFrame(exec_frame, text="Command preview", padding=self.PAD)
        preview_frame.grid(row=0, column=0, sticky="ew", pady=(0, self.PAD))
        preview_frame.columnconfigure(0, weight=1)

        self.command_preview = tk.Text(preview_frame, height=3, wrap="word")
        self.command_preview.grid(row=0, column=0, sticky="ew")

        # Status frame
        status_frame = ttk.Frame(exec_frame)
        status_frame.grid(row=1, column=0, sticky="ew")
        status_frame.columnconfigure(0, weight=1)

        # Status message
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=0, sticky="w", padx=self.PAD)

        # Buttons
        buttons_frame = ttk.Frame(status_frame)
        buttons_frame.grid(row=0, column=1, sticky="e")

        # Save configuration button
        save_config_button = ttk.Button(buttons_frame, text="Save Config", command=self._save_config)
        save_config_button.grid(row=0, column=0, padx=5)

        # Generate command button
        generate_button = ttk.Button(buttons_frame, text="Generate Command", command=self._generate_command)
        generate_button.grid(row=0, column=1, padx=5)

        # Launch button
        self.launch_button = ttk.Button(buttons_frame, text="Launch", command=self._launch_model)
        self.launch_button.grid(row=0, column=2, padx=5)

    def _browse_model(self) -> None:
        """Browse for model file."""
        model_file = filedialog.askopenfilename(
            title="Select Model File",
            filetypes=[
                ("Model files", "*.bin *.gguf *.pt *.ggml *.safetensors"),
                ("All files", "*.*")
            ]
        )

        if model_file:
            self.model_path_var.set(model_file)
            self.logger.info(f"Selected model file: {model_file}")

    def _on_preset_selected(self, event=None) -> None:
        """Handle model preset selection."""
        preset = self.model_preset_var.get()
        self.logger.debug(f"Selected preset: {preset}")

        # Update parameters based on preset
        if preset == "Llama-2-7B":
            self.ctx_size_var.set(4096)
        elif preset == "Llama-2-13B":
            self.ctx_size_var.set(4096)
        elif preset == "Llama-2-70B":
            self.ctx_size_var.set(4096)
        elif preset == "Mistral-7B":
            self.ctx_size_var.set(8192)

    def _on_framework_changed(self, event=None) -> None:
        """Handle framework selection change."""
        framework = self.framework_var.get()
        self.logger.debug(f"Selected framework: {framework}")

        # Show appropriate parameter frame
        if framework == "llama.cpp":
            self.llama_params_frame.grid(row=0, column=0, sticky="nsew")
            self.vllm_params_frame.grid_forget()
        else:
            self.vllm_params_frame.grid(row=0, column=0, sticky="nsew")
            self.llama_params_frame.grid_forget()

    def _optimize_gpu_split(self) -> None:
        """Optimize GPU split based on available GPUs."""
        if not self.gpus:
            self.status_var.set("No GPUs available for optimization")
            return

        # Call optimizer to calculate optimal split
        from dualgpuopt.optimizer import calculate_gpu_split

        splits = calculate_gpu_split(self.gpus)
        split_str = ",".join([f"{int(s*100)}" for s in splits])

        self.gpu_split_var.set(split_str)
        self.status_var.set(f"Optimized GPU split: {split_str}")

    def _update_gpu_display(self) -> None:
        """Update UI based on available GPUs."""
        # Update tensor parallel size max label
        if hasattr(self, 'tp_size_var'):
            for widget in self.vllm_params_frame.winfo_children():
                if isinstance(widget, ttk.Frame) and widget.grid_info()['row'] == 0:
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Label):
                            child.config(text=f"(Max: {len(self.gpus)})")
                            break

    def _generate_command(self) -> None:
        """Generate command for launching model."""
        framework = self.framework_var.get()
        model_path = self.model_path_var.get()

        if not model_path:
            self.status_var.set("Model path cannot be empty")
            return

        # Generate command based on framework
        command = ""
        if framework == "llama.cpp":
            ctx_size = self.ctx_size_var.get()
            gpu_split = self.gpu_split_var.get()
            batch_size = self.batch_size_var.get()
            threads = self.threads_var.get()

            command = (
                f"./main -m {model_path} "
                f"--ctx-size {ctx_size} "
                f"--gpu-split {gpu_split} "
                f"--batch-size {batch_size} "
                f"--threads {threads}"
            )
        else:  # vllm
            tp_size = self.tp_size_var.get()
            if tp_size == "auto":
                tp_size = len(self.gpus)

            max_model_len = self.max_model_len_var.get()

            command = (
                f"python -m vllm.entrypoints.openai.api_server "
                f"--model {model_path} "
                f"--tensor-parallel-size {tp_size} "
                f"--max-model-len {max_model_len}"
            )

        # Update command preview
        self.command_preview.delete("1.0", tk.END)
        self.command_preview.insert("1.0", command)

        self.status_var.set("Command generated")

    def _save_config(self) -> None:
        """Save current configuration."""
        # This is a placeholder for the actual implementation
        self.status_var.set("Configuration saved")

    def _launch_model(self) -> None:
        """Launch model with current configuration."""
        # This is a placeholder for the actual implementation
        self.status_var.set("Launching model...")

    def _update_process_status(self, process_id: str, return_code: int) -> None:
        """
        Update UI based on process status.

        Args:
            process_id: ID of the process
            return_code: Process return code
        """
        if return_code == 0:
            self.status_var.set(f"Process {process_id} completed successfully")
        else:
            self.status_var.set(f"Process {process_id} exited with code {return_code}")