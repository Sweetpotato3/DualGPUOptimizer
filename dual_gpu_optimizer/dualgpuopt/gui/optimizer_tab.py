"""
Optimizer tab for the DualGPUOptimizer GUI.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog
import json
import pathlib
from typing import Dict, List, Callable, Any, Optional

from dualgpuopt.gpu_info import GPU
from dualgpuopt import optimizer


class OptimizerTab(ttk.Frame):
    """Optimizer tab that generates optimization configs for GPUs."""
    
    def __init__(self, parent: ttk.Frame, gpus: List[GPU]) -> None:
        """
        Initialize the optimizer tab.
        
        Args:
            parent: Parent frame
            gpus: List of GPU objects
        """
        super().__init__(parent, padding=8)
        self.parent = parent
        self.gpus = gpus
        self.columnconfigure(0, weight=1)
        
        # Model path selection
        model_frame = ttk.LabelFrame(self, text="Model Selection")
        model_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(0, 8))
        model_frame.columnconfigure(1, weight=1)
        
        self.model_var = tk.StringVar()
        ttk.Label(model_frame, text="Model Path:").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        model_entry = ttk.Entry(model_frame, textvariable=self.model_var)
        model_entry.grid(row=0, column=1, sticky="ew", padx=8, pady=8)
        browse_btn = ttk.Button(model_frame, text="Browse", command=self._browse)
        browse_btn.grid(row=0, column=2, padx=8, pady=8)
        
        # Preset selection (for common models)
        presets_frame = ttk.Frame(model_frame)
        presets_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 8))
        presets_frame.columnconfigure(1, weight=1)
        
        ttk.Label(presets_frame, text="Preset:").grid(row=0, column=0, sticky="w")
        
        # Try to load presets
        self.presets = self._load_presets()
        preset_names = list(self.presets.keys()) if self.presets else ["No presets found"]
        
        self.preset_var = tk.StringVar()
        preset_combo = ttk.Combobox(
            presets_frame, 
            textvariable=self.preset_var,
            values=preset_names,
            state="readonly"
        )
        preset_combo.grid(row=0, column=1, sticky="ew", padx=8)
        preset_combo.bind("<<ComboboxSelected>>", self._preset_selected)
        
        # Context size selection
        param_frame = ttk.LabelFrame(self, text="Model Parameters")
        param_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        param_frame.columnconfigure(1, weight=1)
        
        self.ctx_var = tk.IntVar(value=65536)
        ttk.Label(param_frame, text="Context Size:").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        ctx_entry = ttk.Entry(param_frame, textvariable=self.ctx_var, width=10)
        ctx_entry.grid(row=0, column=1, sticky="w", padx=8, pady=8)
        
        # GPU info and split display
        gpu_frame = ttk.LabelFrame(self, text="Detected GPUs")
        gpu_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        gpu_frame.columnconfigure(1, weight=1)
        
        self.gpu_vars = []
        for i, gpu in enumerate(self.gpus):
            ttk.Label(
                gpu_frame, 
                text=f"GPU {gpu.index}: {gpu.name}"
            ).grid(row=i, column=0, sticky="w", padx=8, pady=4)
            
            mem_text = f"{gpu.mem_total_gb} GB total, {gpu.mem_free_gb} GB free"
            ttk.Label(
                gpu_frame, 
                text=mem_text
            ).grid(row=i, column=1, sticky="w", padx=8, pady=4)
        
        # Output configuration
        output_frame = ttk.LabelFrame(self, text="Optimization Results")
        output_frame.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 8))
        output_frame.columnconfigure(1, weight=1)
        
        # Split string output
        ttk.Label(output_frame, text="GPU Split:").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        self.split_var = tk.StringVar()
        split_entry = ttk.Entry(output_frame, textvariable=self.split_var, state="readonly")
        split_entry.grid(row=0, column=1, sticky="ew", padx=8, pady=8)
        split_copy = ttk.Button(output_frame, text="Copy", command=lambda: self._copy("split"))
        split_copy.grid(row=0, column=2, padx=8, pady=8)
        
        # llama.cpp command
        ttk.Label(output_frame, text="llama.cpp:").grid(row=1, column=0, sticky="w", padx=8, pady=8)
        self.llama_var = tk.StringVar()
        llama_entry = ttk.Entry(output_frame, textvariable=self.llama_var, state="readonly")
        llama_entry.grid(row=1, column=1, sticky="ew", padx=8, pady=8)
        llama_copy = ttk.Button(output_frame, text="Copy", command=lambda: self._copy("llama"))
        llama_copy.grid(row=1, column=2, padx=8, pady=8)
        
        # vLLM command
        ttk.Label(output_frame, text="vLLM:").grid(row=2, column=0, sticky="w", padx=8, pady=8)
        self.vllm_var = tk.StringVar()
        vllm_entry = ttk.Entry(output_frame, textvariable=self.vllm_var, state="readonly")
        vllm_entry.grid(row=2, column=1, sticky="ew", padx=8, pady=8)
        vllm_copy = ttk.Button(output_frame, text="Copy", command=lambda: self._copy("vllm"))
        vllm_copy.grid(row=2, column=2, padx=8, pady=8)
        
        # Env file generation
        env_frame = ttk.Frame(output_frame)
        env_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=8, pady=8)
        env_frame.columnconfigure(1, weight=1)
        
        ttk.Label(env_frame, text="Generate Env File:").grid(row=0, column=0, sticky="w")
        self.env_path_var = tk.StringVar(value=str(pathlib.Path.home() / ".env"))
        env_entry = ttk.Entry(env_frame, textvariable=self.env_path_var)
        env_entry.grid(row=0, column=1, sticky="ew", padx=8)
        env_btn = ttk.Button(env_frame, text="Save", command=self._save_env)
        env_btn.grid(row=0, column=2, padx=8)
        
        # Initialize output
        self._refresh_outputs()
    
    def _browse(self) -> None:
        """Open file dialog to select model path."""
        path = filedialog.askopenfilename(
            title="Select Model File",
            filetypes=[
                ("GGUF Models", "*.gguf"),
                ("GGML Models", "*.ggml"),
                ("Pytorch Models", "*.pt *.pth"),
                ("Bin Files", "*.bin"),
                ("All Files", "*.*")
            ]
        )
        if path:
            self.model_var.set(path)
            self._refresh_outputs()
    
    def _refresh_outputs(self) -> None:
        """Update output fields based on current settings."""
        # Generate split string
        split = optimizer.split_string(self.gpus)
        self.split_var.set(split)
        
        # Generate commands if model path is set
        model_path = self.model_var.get()
        ctx = self.ctx_var.get()
        
        if model_path:
            self.llama_var.set(optimizer.llama_command(model_path, ctx, split))
            self.vllm_var.set(optimizer.vllm_command(model_path, len(self.gpus)))
    
    def _copy(self, which: str) -> None:
        """
        Copy the selected value to clipboard.
        
        Args:
            which: Type of value to copy ('split', 'llama', or 'vllm')
        """
        value = ""
        if which == "split":
            value = self.split_var.get()
        elif which == "llama":
            value = self.llama_var.get()
        elif which == "vllm":
            value = self.vllm_var.get()
            
        if value:
            self.clipboard_clear()
            self.clipboard_append(value)
    
    def _save_env(self) -> None:
        """Generate and save environment variables file."""
        env_path = pathlib.Path(self.env_path_var.get())
        optimizer.make_env_file(self.gpus, env_path)
    
    def _preset_selected(self, *_) -> None:
        """Handle preset selection."""
        preset_name = self.preset_var.get()
        if preset_name in self.presets:
            preset_data = self.presets[preset_name]
            if "path" in preset_data:
                self.model_var.set(preset_data["path"])
            if "ctx" in preset_data:
                self.ctx_var.set(preset_data["ctx"])
            self._refresh_outputs()
    
    def _load_presets(self) -> Dict[str, Any]:
        """
        Load model presets from the presets directory.
        
        Returns:
            Dictionary of preset configurations
        """
        try:
            preset_path = pathlib.Path(__file__).parent.parent / "presets" / "mixtral.json"
            if preset_path.exists():
                return json.load(preset_path.open())
        except Exception:
            # If there's any error loading presets, return an empty dict
            pass
        return {} 