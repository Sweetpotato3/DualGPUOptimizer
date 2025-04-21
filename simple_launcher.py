"""
Ultra-simplified launcher for DualGPUOptimizer.
This script directly launches the mock GPU optimization without dependencies.
"""
import os
import sys
import pathlib
import tkinter as tk
from tkinter import ttk, filedialog
from dataclasses import dataclass
from typing import List

# Set environment variable for mock GPU mode
os.environ["DGPUOPT_MOCK_GPUS"] = "1"

# Create log directory
log_dir = pathlib.Path.home() / ".dualgpuopt" / "logs"
os.makedirs(log_dir, exist_ok=True)

@dataclass
class GPU:
    """GPU information container."""
    index: int
    name: str
    mem_total: int  # MiB
    mem_free: int   # MiB

    @property
    def mem_used(self) -> int:
        """Return used memory in MiB."""
        return self.mem_total - self.mem_free

    @property
    def mem_total_gb(self) -> int:
        """Return total memory in GB (rounded)."""
        return round(self.mem_total / 1024)


def get_mock_gpus() -> List[GPU]:
    """Create mock GPU objects for testing or demo purposes."""
    return [
        GPU(0, "NVIDIA GeForce RTX 3090", 24576, 20480),  # 24GB
        GPU(1, "NVIDIA GeForce RTX 3080", 10240, 8192),   # 10GB
    ]


def split_string(gpus: List[GPU]) -> str:
    """Create a GPU split string from GPU info."""
    return ",".join(str(g.mem_total_gb) for g in gpus)


def tensor_fractions(gpus: List[GPU]) -> list[float]:
    """Calculate tensor fractions for GPUs."""
    top = max(g.mem_total for g in gpus)
    return [round(g.mem_total / top, 3) for g in gpus]


def llama_command(model_path: str, ctx: int, split: str) -> str:
    """Generate a llama.cpp command line."""
    return (
        f"./main -m {model_path} "
        f"--gpu-split {split} --n-gpu-layers 999 --ctx-size {ctx}"
    )


def vllm_command(model_path: str, tp: int) -> str:
    """Generate a vLLM command line."""
    return (
        "python -m vllm.entrypoints.openai.api_server "
        f"--model {model_path} --dtype float16 "
        f"--tensor-parallel-size {tp} --gpu-memory-utilization 0.9"
    )


class DualGpuApp(ttk.Frame):
    """Simple DualGPUOptimizer application."""

    def __init__(self, master=None):
        ttk.Frame.__init__(self, master, padding=10)
        self.master = master

        # Mock GPUs
        self.gpus = get_mock_gpus()

        # Initialize UI
        self.model_var = tk.StringVar(value="llama-7b.gguf")
        self.ctx_var = tk.IntVar(value=65536)
        self.output_var = tk.StringVar()

        self.create_widgets()
        self.update_output()

    def create_widgets(self):
        """Create the UI widgets."""
        # Title
        title_label = ttk.Label(self, text="DualGPUOptimizer", font=("Segoe UI", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)

        # GPU Info
        gpu_frame = ttk.LabelFrame(self, text="Detected GPUs", padding=10)
        gpu_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        for i, gpu in enumerate(self.gpus):
            ttk.Label(gpu_frame, text=f"GPU {gpu.index}: {gpu.name}").grid(row=i, column=0, sticky="w")
            ttk.Label(gpu_frame, text=f"{gpu.mem_total_gb} GB").grid(row=i, column=1, sticky="e")

        # Model Input
        input_frame = ttk.LabelFrame(self, text="Model Settings", padding=10)
        input_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        ttk.Label(input_frame, text="Model Path:").grid(row=0, column=0, sticky="w")
        model_entry = ttk.Entry(input_frame, textvariable=self.model_var, width=30)
        model_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(input_frame, text="Context Size:").grid(row=1, column=0, sticky="w")
        ctx_entry = ttk.Entry(input_frame, textvariable=self.ctx_var, width=10)
        ctx_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        # Output
        output_frame = ttk.LabelFrame(self, text="Optimization Results", padding=10)
        output_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        output_frame.columnconfigure(0, weight=1)

        output_text = tk.Text(output_frame, wrap="word", height=10, width=60)
        output_text.grid(row=0, column=0, sticky="nsew")
        output_text.configure(state="normal")
        self.output_text = output_text

        # Buttons
        button_frame = ttk.Frame(self, padding=10)
        button_frame.grid(row=4, column=0, columnspan=2, pady=5)

        ttk.Button(button_frame, text="Generate Commands", command=self.update_output).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Browse", command=self.browse_model).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.master.destroy).grid(row=0, column=2, padx=5)

        # Configure grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

    def browse_model(self):
        """Browse for a model file."""
        filename = filedialog.askopenfilename(
            title="Select Model File",
            filetypes=[("GGUF Files", "*.gguf"), ("All Files", "*.*")]
        )
        if filename:
            self.model_var.set(filename)
            self.update_output()

    def update_output(self):
        """Update the output text with optimization results."""
        model_path = self.model_var.get()
        ctx_size = self.ctx_var.get()

        split = split_string(self.gpus)
        fractions = tensor_fractions(self.gpus)

        # Clear output
        self.output_text.delete(1.0, tk.END)

        # Add GPU info
        self.output_text.insert(tk.END, "GPU INFORMATION:\n")
        for i, gpu in enumerate(self.gpus):
            self.output_text.insert(tk.END, f"  GPU {gpu.index}: {gpu.name}\n")
            self.output_text.insert(tk.END, f"    Memory: {gpu.mem_total_gb} GB total, {gpu.mem_free//1024} GB free\n")

        # Add optimization info
        self.output_text.insert(tk.END, "\nOPTIMIZATION RESULTS:\n")
        self.output_text.insert(tk.END, f"  Recommended Split: {split}\n")
        self.output_text.insert(tk.END, f"  Tensor Fractions: {', '.join(str(f) for f in fractions)}\n")

        # Add commands
        self.output_text.insert(tk.END, "\nCOMMANDS:\n")
        self.output_text.insert(tk.END, f"  llama.cpp:\n    {llama_command(model_path, ctx_size, split)}\n\n")
        self.output_text.insert(tk.END, f"  vLLM:\n    {vllm_command(model_path, len(self.gpus))}\n")


def main():
    """Main function to run the app."""
    try:
        root = tk.Tk()
        root.title("DualGPUOptimizer")
        root.geometry("700x600")

        # Create app
        app = DualGpuApp(root)
        app.pack(fill="both", expand=True)

        # Run the app
        root.mainloop()
        return 0
    except Exception as e:
        print(f"Error: {e}")
        with open(log_dir / "simple_launcher.log", "w") as f:
            f.write(f"Error: {e}\n")
            import traceback
            f.write(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())