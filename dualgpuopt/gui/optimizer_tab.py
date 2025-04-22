"""
Optimizer tab for GPU memory allocation and tensor splitting
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk

from ..integration import get_optimizer_integration
from ..optimizer import ModelParameters, SplitConfiguration, get_optimizer

# Initialize logger
logger = logging.getLogger("DualGPUOpt.OptimizerTab")

# Common LLM model presets
MODEL_PRESETS = {
    "Llama-2 7B": ModelParameters(
        name="Llama-2 7B",
        context_length=4096,
        hidden_size=4096,
        num_layers=32,
        num_heads=32,
        kv_heads=32,
    ),
    "Llama-2 13B": ModelParameters(
        name="Llama-2 13B",
        context_length=4096,
        hidden_size=5120,
        num_layers=40,
        num_heads=40,
        kv_heads=40,
    ),
    "Llama-2 70B": ModelParameters(
        name="Llama-2 70B",
        context_length=4096,
        hidden_size=8192,
        num_layers=80,
        num_heads=64,
        kv_heads=8,
    ),
    "Mistral 7B": ModelParameters(
        name="Mistral 7B",
        context_length=8192,
        hidden_size=4096,
        num_layers=32,
        num_heads=32,
        kv_heads=8,
    ),
    "Mixtral 8x7B": ModelParameters(
        name="Mixtral 8x7B",
        context_length=8192,
        hidden_size=4096,
        num_layers=32,
        num_heads=32,
        kv_heads=8,
    ),
    "Phi-2": ModelParameters(
        name="Phi-2", context_length=2048, hidden_size=2560, num_layers=32, num_heads=32
    ),
    "Custom": None,  # Placeholder for custom model
}


class OptimizerTab(ttk.Frame):
    """Tab for GPU memory optimization settings"""

    def __init__(self, parent):
        """Initialize optimizer tab

        Args:
            parent: Parent widget
        """
        super().__init__(parent, padding=15)

        # Initialize optimizer
        self.optimizer = get_optimizer()
        self.integration = get_optimizer_integration()

        # Setup the grid layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)  # Results section expands

        # Title section
        title_frame = ttk.Frame(self)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        ttk.Label(title_frame, text="GPU Split Optimizer", font=("Arial", 16, "bold")).pack(
            side=tk.LEFT
        )

        # GPU Information section - use TLabelframe style
        gpu_frame = ttk.LabelFrame(self, text="GPU Information", padding=10, style="TLabelframe")
        gpu_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        self.gpu_info_text = tk.Text(
            gpu_frame,
            height=4,
            width=60,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#241934",
            fg="#FFFFFF",
        )
        self.gpu_info_text.pack(fill=tk.BOTH, expand=True)
        self.gpu_info_text.config(state=tk.DISABLED)

        # Model selection section - use TLabelframe style
        model_frame = ttk.LabelFrame(
            self, text="Model Configuration", padding=10, style="TLabelframe"
        )
        model_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))

        model_frame.columnconfigure(1, weight=1)

        # Model preset dropdown
        ttk.Label(model_frame, text="Model:", style="Inner.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=5
        )

        self.model_var = tk.StringVar(value=list(MODEL_PRESETS.keys())[0])
        model_dropdown = ttk.Combobox(
            model_frame,
            textvariable=self.model_var,
            values=list(MODEL_PRESETS.keys()),
            state="readonly",
            width=30,
        )
        model_dropdown.grid(row=0, column=1, sticky="ew", pady=5)
        model_dropdown.bind("<<ComboboxSelected>>", self._on_model_selected)

        # Context length entry
        ttk.Label(model_frame, text="Context Length:", style="Inner.TLabel").grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=5
        )

        self.context_var = tk.StringVar(
            value=str(MODEL_PRESETS[self.model_var.get()].context_length)
        )
        context_entry = ttk.Entry(model_frame, textvariable=self.context_var, width=10)
        context_entry.grid(row=1, column=1, sticky="w", pady=5)

        # Add custom model parameters (visible only when Custom is selected) - use Inner.TFrame style
        self.custom_frame = ttk.Frame(model_frame, style="Inner.TFrame")
        self.custom_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.custom_frame.columnconfigure(1, weight=1)
        self.custom_frame.columnconfigure(3, weight=1)

        # Hidden size
        ttk.Label(self.custom_frame, text="Hidden Size:", style="Inner.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.hidden_var = tk.StringVar(value="4096")
        hidden_entry = ttk.Entry(self.custom_frame, textvariable=self.hidden_var, width=10)
        hidden_entry.grid(row=0, column=1, sticky="w", pady=5)

        # Layers
        ttk.Label(self.custom_frame, text="Layers:", style="Inner.TLabel").grid(
            row=0, column=2, sticky="w", padx=(20, 10), pady=5
        )
        self.layers_var = tk.StringVar(value="32")
        layers_entry = ttk.Entry(self.custom_frame, textvariable=self.layers_var, width=10)
        layers_entry.grid(row=0, column=3, sticky="w", pady=5)

        # Heads
        ttk.Label(self.custom_frame, text="Attention Heads:", style="Inner.TLabel").grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.heads_var = tk.StringVar(value="32")
        heads_entry = ttk.Entry(self.custom_frame, textvariable=self.heads_var, width=10)
        heads_entry.grid(row=1, column=1, sticky="w", pady=5)

        # KV Heads
        ttk.Label(self.custom_frame, text="KV Heads:", style="Inner.TLabel").grid(
            row=1, column=2, sticky="w", padx=(20, 10), pady=5
        )
        self.kv_heads_var = tk.StringVar(value="32")
        kv_heads_entry = ttk.Entry(self.custom_frame, textvariable=self.kv_heads_var, width=10)
        kv_heads_entry.grid(row=1, column=3, sticky="w", pady=5)

        # Initially hide custom parameters
        self.custom_frame.grid_remove()

        # Calculate button
        button_frame = ttk.Frame(model_frame, style="Inner.TFrame")
        button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(15, 0))

        ttk.Button(
            button_frame, text="Calculate Optimal Split", command=self._calculate_split
        ).pack(side=tk.RIGHT)

        # Results section - use TLabelframe style
        results_frame = ttk.LabelFrame(
            self, text="Optimization Results", padding=10, style="TLabelframe"
        )
        results_frame.grid(row=3, column=0, sticky="nsew")

        self.results_text = tk.Text(
            results_frame,
            height=10,
            width=60,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#241934",
            fg="#FFFFFF",
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.results_text.config(state=tk.DISABLED)

        # Command line section - use TLabelframe style
        cmd_frame = ttk.LabelFrame(self, text="Command Arguments", padding=10, style="TLabelframe")
        cmd_frame.grid(row=4, column=0, sticky="ew", pady=(15, 0))

        # Framework tabs
        cmd_notebook = ttk.Notebook(cmd_frame)
        cmd_notebook.pack(fill=tk.BOTH, expand=True)

        # llama.cpp tab - use Inner.TFrame style
        llama_frame = ttk.Frame(cmd_notebook, padding=10, style="Inner.TFrame")
        cmd_notebook.add(llama_frame, text="llama.cpp")

        self.llama_cmd_var = tk.StringVar(value="")
        llama_entry = ttk.Entry(llama_frame, textvariable=self.llama_cmd_var, font=("Consolas", 10))
        llama_entry.pack(fill=tk.X, expand=True, pady=(0, 10))

        ttk.Button(
            llama_frame,
            text="Copy to Clipboard",
            command=lambda: self._copy_to_clipboard(self.llama_cmd_var.get()),
        ).pack(side=tk.RIGHT)

        # vLLM tab - use Inner.TFrame style
        vllm_frame = ttk.Frame(cmd_notebook, padding=10, style="Inner.TFrame")
        cmd_notebook.add(vllm_frame, text="vLLM")

        self.vllm_cmd_var = tk.StringVar(value="")
        vllm_entry = ttk.Entry(vllm_frame, textvariable=self.vllm_cmd_var, font=("Consolas", 10))
        vllm_entry.pack(fill=tk.X, expand=True, pady=(0, 10))

        ttk.Button(
            vllm_frame,
            text="Copy to Clipboard",
            command=lambda: self._copy_to_clipboard(self.vllm_cmd_var.get()),
        ).pack(side=tk.RIGHT)

        # Initialize with GPU information
        self._update_gpu_info()

    def _on_model_selected(self, event):
        """Handle model selection change"""
        model_name = self.model_var.get()

        if model_name == "Custom":
            # Show custom model parameters
            self.custom_frame.grid()
        else:
            # Hide custom parameters and update context length
            self.custom_frame.grid_remove()
            model = MODEL_PRESETS[model_name]
            self.context_var.set(str(model.context_length))

    def _update_gpu_info(self):
        """Update the GPU information display"""
        try:
            gpu_info = self.optimizer.get_gpu_info()

            # Enable text widget for update
            self.gpu_info_text.config(state=tk.NORMAL)
            self.gpu_info_text.delete(1.0, tk.END)

            for gpu in gpu_info:
                self.gpu_info_text.insert(tk.END, f"GPU {gpu.gpu_id}: {gpu.name}\n")
                self.gpu_info_text.insert(
                    tk.END,
                    f"  Memory: {gpu.formatted_available} available of {gpu.formatted_total}\n",
                )

            # Disable for read-only
            self.gpu_info_text.config(state=tk.DISABLED)

        except Exception as e:
            logger.error(f"Error updating GPU info: {e}")
            messagebox.showerror("Error", f"Failed to get GPU information: {e}")

    def _get_model_parameters(self) -> ModelParameters:
        """Get the current model parameters from UI"""
        model_name = self.model_var.get()

        if model_name == "Custom":
            # Build from custom parameters
            try:
                return ModelParameters(
                    name="Custom Model",
                    context_length=int(self.context_var.get()),
                    hidden_size=int(self.hidden_var.get()),
                    num_layers=int(self.layers_var.get()),
                    num_heads=int(self.heads_var.get()),
                    kv_heads=int(self.kv_heads_var.get()),
                )
            except ValueError as err:
                raise ValueError("All model parameters must be valid integers") from err
        else:
            # Use preset but update context length
            model = MODEL_PRESETS[model_name]
            try:
                context_length = int(self.context_var.get())
                return ModelParameters(
                    name=model.name,
                    context_length=context_length,
                    hidden_size=model.hidden_size,
                    num_layers=model.num_layers,
                    num_heads=model.num_heads,
                    kv_heads=model.kv_heads,
                )
            except ValueError as err:
                raise ValueError("Context length must be a valid integer") from err

    def _calculate_split(self):
        """Calculate and display the optimal GPU split"""
        try:
            # Get current model parameters
            model = self._get_model_parameters()

            # Update GPU info before calculating
            self._update_gpu_info()

            # Get model path from integration (if available)
            model_path = self.integration.model_path

            # Calculate optimal split
            config = self.optimizer.optimize_gpu_split(model)

            # Display results
            self._display_results(model, config)

            # Get Engine instance from integration if possible
            try:
                from dualgpuopt.engine.backend import Engine

                Engine()

                # Update command arguments using Engine-appropriate parameters
                # These would be handled automatically by the Engine's load method
                llama_kwargs = {
                    "gpu_layers": -1,
                    "split_mode": 2,
                    "tensor_split": ",".join([f"{ratio:.2f}" for ratio in config.gpu_split]),
                    "ctx_size": config.recommended_context_length,
                }

                vllm_kwargs = {
                    "tensor_parallel_size": config.tensor_parallel_size,
                    "max_model_len": config.recommended_context_length,
                }

                # Generate command strings
                llama_cmd = f"--model {model_path if model_path else '<model_path>'} " + " ".join(
                    [f"--{k.replace('_', '-')} {v}" for k, v in llama_kwargs.items()]
                )

                vllm_cmd = f"--model {model_path if model_path else '<model_path>'} " + " ".join(
                    [f"--{k.replace('_', '-')} {v}" for k, v in vllm_kwargs.items()]
                )

            except ImportError:
                # Fall back to old method if Engine isn't available
                llama_cmd = self.optimizer.generate_llama_cpp_args(config, model_path)
                vllm_cmd = self.optimizer.generate_vllm_args(config, model_path)

            self.llama_cmd_var.set(llama_cmd)
            self.vllm_cmd_var.set(vllm_cmd)

            # Update integration with the commands
            self.integration.update_commands(llama_cmd, vllm_cmd)

        except Exception as e:
            logger.error(f"Error calculating split: {e}")
            messagebox.showerror("Error", f"Failed to calculate GPU split: {e}")

    def _display_results(self, model: ModelParameters, config: SplitConfiguration):
        """Display optimization results

        Args:
            model: Model parameters used
            config: Resulting split configuration
        """
        # Enable text widget for update
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)

        # Model info
        self.results_text.insert(tk.END, f"Model: {model.name}\n")
        self.results_text.insert(tk.END, "Parameters:\n")
        self.results_text.insert(tk.END, f"  - Hidden Size: {model.hidden_size}\n")
        self.results_text.insert(tk.END, f"  - Layers: {model.num_layers}\n")
        self.results_text.insert(tk.END, f"  - Attention Heads: {model.num_heads}\n")
        if model.kv_heads and model.kv_heads != model.num_heads:
            self.results_text.insert(tk.END, f"  - KV Heads: {model.kv_heads}\n")

        self.results_text.insert(tk.END, "\n")

        # Split configuration
        self.results_text.insert(tk.END, f"Tensor Parallel Size: {config.tensor_parallel_size}\n")
        self.results_text.insert(tk.END, f"GPU Split Ratio: {config.formatted_split}\n")
        self.results_text.insert(tk.END, f"Memory Per GPU: {config.formatted_memory}\n")
        self.results_text.insert(tk.END, "\n")

        # Context size
        self.results_text.insert(tk.END, f"Maximum Context: {config.max_context_length} tokens\n")
        self.results_text.insert(
            tk.END, f"Recommended Context: {config.recommended_context_length} tokens\n"
        )

        # Disable for read-only
        self.results_text.config(state=tk.DISABLED)

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard

        Args:
            text: Text to copy
        """
        self.clipboard_clear()
        self.clipboard_append(text)

        # Show temporary success message
        messagebox.showinfo("Copied", "Command copied to clipboard!")


# Test function to run the optimizer tab standalone
def run_optimizer_tab():
    """Run the optimizer tab as a standalone application"""
    root = tk.Tk()
    root.title("GPU Split Optimizer")
    root.geometry("800x800")

    # Set up the main frame
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Create optimizer tab
    optimizer_tab = OptimizerTab(main_frame)
    optimizer_tab.pack(fill=tk.BOTH, expand=True)

    # Start the main loop
    root.mainloop()


if __name__ == "__main__":
    run_optimizer_tab()
