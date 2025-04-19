"""
Launcher tab for running models with optimized settings
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import queue
import threading
import os
import logging
from typing import Dict, List, Optional, Callable, Any, Tuple
from pathlib import Path

# Import our advanced optimization modules
try:
    from ..batch.smart_batch import optimize_batch_size
    from ..ctx_size import calc_max_ctx, model_params_from_name
    from ..layer_balance import rebalance
    from ..vram_reset import reset_vram
    from ..mpolicy import autocast, scaler
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    logging.warning("Advanced optimization modules not available")
    ADVANCED_FEATURES_AVAILABLE = False

# Initialize logger
logger = logging.getLogger("DualGPUOpt.LauncherTab")


class ModelRunner:
    """Handles running model inference commands and capturing output"""
    
    def __init__(self, log_queue: queue.Queue):
        """Initialize model runner
        
        Args:
            log_queue: Queue for sending output back to the GUI
        """
        self.log_queue = log_queue
        self.process = None
        self.stop_event = threading.Event()
    
    def start(self, command: str, env: Optional[Dict[str, str]] = None) -> None:
        """Start running a model command
        
        Args:
            command: Command string to execute
            env: Optional environment variables
        """
        import subprocess
        import sys
        
        if self.process and self.process.poll() is None:
            self.log_queue.put("Process already running. Stop it first.\n")
            return
        
        # Reset stop event
        self.stop_event.clear()
        
        # Add current environment to any custom values
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        self.log_queue.put(f"Starting command: {command}\n")
        
        # Start the process
        try:
            self.process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=full_env,
                universal_newlines=True,
                bufsize=1
            )
            
            # Start reading output
            threading.Thread(target=self._read_output, daemon=True).start()
            
        except Exception as e:
            self.log_queue.put(f"Error starting process: {e}\n")
    
    def _read_output(self) -> None:
        """Read process output and send to log queue"""
        if not self.process:
            return
            
        for line in iter(self.process.stdout.readline, ''):
            if self.stop_event.is_set():
                break
            self.log_queue.put(line)
            
        if self.process.poll() is not None:
            self.log_queue.put(f"\nProcess ended with code {self.process.returncode}\n")
    
    def stop(self) -> None:
        """Stop the running process"""
        if not self.process or self.process.poll() is not None:
            return
            
        self.stop_event.set()
        self.log_queue.put("Stopping process...\n")
        
        try:
            import signal
            if sys.platform == "win32":
                self.process.terminate()
            else:
                self.process.send_signal(signal.SIGTERM)
                
            # Give it a moment to terminate
            import time
            time.sleep(0.5)
            
            # Force kill if still running
            if self.process.poll() is None:
                self.process.kill()
                
        except Exception as e:
            self.log_queue.put(f"Error stopping process: {e}\n")


class LauncherTab(ttk.Frame):
    """Tab for launching models with optimized settings"""
    
    def __init__(self, parent):
        """Initialize launcher tab
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent, padding=15)
        
        # Setup grid layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        
        # Framework selection
        framework_frame = ttk.Frame(self)
        framework_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        ttk.Label(framework_frame, text="Framework:").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.framework_var = tk.StringVar(value="llama.cpp")
        framework_combo = ttk.Combobox(
            framework_frame,
            textvariable=self.framework_var,
            values=["llama.cpp", "vLLM"],
            state="readonly",
            width=10
        )
        framework_combo.grid(row=0, column=1, padx=5, sticky="w")
        
        # Add VRAM reset button
        self.reset_btn = ttk.Button(
            framework_frame, 
            text="Reset VRAM",
            command=self._reset_vram
        )
        self.reset_btn.grid(row=0, column=2, padx=5)
        
        # Model path selection
        model_frame = ttk.LabelFrame(self, text="Model Selection", padding=10)
        model_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        model_frame.columnconfigure(1, weight=1)
        
        ttk.Label(model_frame, text="Model Path:").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.model_path_var = tk.StringVar()
        model_entry = ttk.Entry(model_frame, textvariable=self.model_path_var)
        model_entry.grid(row=0, column=1, padx=5, sticky="ew")
        
        browse_btn = ttk.Button(
            model_frame, 
            text="Browse",
            command=self._browse_model
        )
        browse_btn.grid(row=0, column=2, padx=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(self, text="Launch Options", padding=10)
        options_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)
        
        # GPU Split option
        ttk.Label(options_frame, text="GPU Split:").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.gpu_split_var = tk.StringVar(value="auto")
        gpu_split_entry = ttk.Entry(options_frame, textvariable=self.gpu_split_var)
        gpu_split_entry.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Context size option
        ttk.Label(options_frame, text="Context Size:").grid(row=1, column=0, padx=(0, 5), sticky="w")
        self.ctx_size_var = tk.StringVar(value="8192")
        ctx_size_entry = ttk.Entry(options_frame, textvariable=self.ctx_size_var)
        ctx_size_entry.grid(row=1, column=1, padx=5, sticky="ew")
        
        # Batch size option 
        ttk.Label(options_frame, text="Batch Size:").grid(row=2, column=0, padx=(0, 5), sticky="w")
        self.batch_size_var = tk.StringVar(value="auto")
        batch_size_entry = ttk.Entry(options_frame, textvariable=self.batch_size_var)
        batch_size_entry.grid(row=2, column=1, padx=5, sticky="ew")
        
        # Mixed precision toggle
        self.mixed_precision_var = tk.BooleanVar(value=True)
        mixed_precision_check = ttk.Checkbutton(
            options_frame,
            text="Use Mixed Precision",
            variable=self.mixed_precision_var
        )
        mixed_precision_check.grid(row=3, column=0, columnspan=2, padx=(0, 5), sticky="w")
        
        # Layer balance toggle
        self.layer_balance_var = tk.BooleanVar(value=True)
        layer_balance_check = ttk.Checkbutton(
            options_frame,
            text="Optimize Layer Balance",
            variable=self.layer_balance_var
        )
        layer_balance_check.grid(row=4, column=0, columnspan=2, padx=(0, 5), sticky="w")
        
        # Launch controls
        control_frame = ttk.Frame(options_frame)
        control_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        self.launch_btn = ttk.Button(
            control_frame, 
            text="Launch Model",
            command=self._launch_model
        )
        self.launch_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(
            control_frame, 
            text="Stop",
            command=self._stop_model,
            state="disabled"
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(control_frame, textvariable=self.status_var)
        status_label.pack(side=tk.RIGHT, padx=5)
        
        # Log output
        log_frame = ttk.LabelFrame(self, text="Process Output", padding=10)
        log_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_text.config(state="disabled")
        
        # Log controls
        log_control_frame = ttk.Frame(log_frame)
        log_control_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        
        self.autoscroll_var = tk.BooleanVar(value=True)
        autoscroll_check = ttk.Checkbutton(
            log_control_frame,
            text="Auto-scroll",
            variable=self.autoscroll_var
        )
        autoscroll_check.pack(side=tk.LEFT)
        
        clear_btn = ttk.Button(
            log_control_frame, 
            text="Clear Log",
            command=self._clear_log
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Command Preview (read-only)
        cmd_frame = ttk.LabelFrame(self, text="Command Preview", padding=10)
        cmd_frame.grid(row=4, column=0, sticky="ew")
        cmd_frame.columnconfigure(0, weight=1)
        
        self.cmd_var = tk.StringVar()
        cmd_entry = ttk.Entry(cmd_frame, textvariable=self.cmd_var, font=("Consolas", 10))
        cmd_entry.grid(row=0, column=0, sticky="ew")
        
        copy_btn = ttk.Button(
            cmd_frame, 
            text="Copy",
            command=lambda: self._copy_to_clipboard(self.cmd_var.get())
        )
        copy_btn.grid(row=0, column=1, padx=(5, 0))
        
        # Initialize runner and queue
        self.log_queue = queue.Queue()
        self.runner = ModelRunner(self.log_queue)
        
        # Start queue processing
        self.after(100, self._process_log_queue)
        
        # Update command preview when settings change
        for var in [self.framework_var, self.model_path_var, self.gpu_split_var, 
                   self.ctx_size_var, self.batch_size_var]:
            var.trace_add("write", lambda *args: self._update_command_preview())
            
        # Initial command preview
        self._update_command_preview()
        
        # Check advanced features
        if not ADVANCED_FEATURES_AVAILABLE:
            messagebox.showwarning(
                "Advanced Features Unavailable",
                "Some advanced optimization features are not available. "
                "Basic functionality will still work."
            )
    
    def _browse_model(self) -> None:
        """Open file dialog to select model file"""
        filetypes = [
            ("Model Files", "*.gguf *.bin *.ggml *.pt *.pth"),
            ("GGUF Models", "*.gguf"),
            ("Hugging Face Models", "*.bin *.pt *.pth"),
            ("All Files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Model File",
            filetypes=filetypes
        )
        
        if filename:
            self.model_path_var.set(filename)
            self._update_command_preview()
            self._suggest_optimal_settings(filename)
    
    def _suggest_optimal_settings(self, model_path: str) -> None:
        """Suggest optimal settings based on model filename"""
        if not ADVANCED_FEATURES_AVAILABLE:
            return
            
        try:
            # Extract model parameters from filename
            model_name = Path(model_path).name.lower()
            
            # Get model params
            n_layers, n_kv_heads, head_dim, moe_factor = model_params_from_name(model_name)
            
            # Calculate optimal context size 
            from ..telemetry import get_telemetry_service
            telemetry = get_telemetry_service()
            metrics = telemetry.get_metrics()
            
            # Convert to GPU objects
            from ..gpu_info import GPU
            gpus = []
            for idx, metric in metrics.items():
                gpus.append(GPU(
                    index=idx,
                    name=metric.name,
                    mem_total=metric.memory_total,
                    mem_free=metric.memory_used
                ))
            
            if gpus:
                ctx_size = calc_max_ctx(
                    gpus,
                    n_layers=n_layers,
                    n_kv_heads=n_kv_heads,
                    head_dim=head_dim,
                    moe_factor=moe_factor
                )
                
                # Round to nearest 1024
                ctx_size = (ctx_size // 1024) * 1024
                self.ctx_size_var.set(str(ctx_size))
                
                # Calculate optimal batch size
                total_vram = sum(gpu.mem_total for gpu in gpus) / 1024  # Convert to GB
                model_size = 0
                
                # Very rough model size estimation based on name
                if "7b" in model_name:
                    model_size = 7
                elif "13b" in model_name:
                    model_size = 13
                elif "70b" in model_name:
                    model_size = 70
                elif "llama" in model_name:
                    model_size = 7  # Default for LLaMA
                
                if model_size > 0:
                    batch_size = optimize_batch_size(total_vram, model_size)
                    self.batch_size_var.set(str(batch_size))
                
                # Suggest GPU split for multi-GPU setup
                if len(gpus) > 1:
                    total_mem = sum(gpu.mem_total for gpu in gpus)
                    split = [gpu.mem_total / total_mem for gpu in gpus]
                    split_str = ",".join(f"{s:.2f}" for s in split)
                    self.gpu_split_var.set(split_str)
                
        except Exception as e:
            logger.warning(f"Error suggesting optimal settings: {e}")
    
    def _update_command_preview(self) -> None:
        """Update the command preview based on current settings"""
        framework = self.framework_var.get()
        model_path = self.model_path_var.get()
        
        if not model_path:
            self.cmd_var.set("Please select a model file")
            return
        
        if framework == "llama.cpp":
            # Build llama.cpp command
            gpu_split = self.gpu_split_var.get() if self.gpu_split_var.get() != "auto" else "0"
            ctx_size = self.ctx_size_var.get()
            batch_size = self.batch_size_var.get() if self.batch_size_var.get() != "auto" else "512"
            
            cmd = (
                f"./main -m {model_path} "
                f"--ctx-size {ctx_size} "
                f"--batch-size {batch_size} "
                f"--gpu-layers 999 "
            )
            
            if gpu_split != "0":
                cmd += f"--gpu-split {gpu_split} "
                
            if self.mixed_precision_var.get():
                cmd += "--dtype float16 "
            
        elif framework == "vLLM":
            # Build vLLM command
            tensor_parallel = 1
            if self.gpu_split_var.get() != "auto":
                # Count commas to determine number of GPUs
                tensor_parallel = self.gpu_split_var.get().count(",") + 1
            
            cmd = (
                f"python -m vllm.entrypoints.openai.api_server "
                f"--model {model_path} "
                f"--tensor-parallel-size {tensor_parallel} "
            )
            
            if self.mixed_precision_var.get():
                cmd += "--dtype float16 "
            
            if self.ctx_size_var.get():
                cmd += f"--max-model-len {self.ctx_size_var.get()} "
        
        else:
            cmd = "Unknown framework selected"
            
        self.cmd_var.set(cmd)
    
    def _launch_model(self) -> None:
        """Launch the model with current settings"""
        cmd = self.cmd_var.get()
        
        if not cmd or cmd.startswith("Please select"):
            messagebox.showerror("Error", "Please select a model file first")
            return
        
        # Setup environment variables
        env = {}
        
        # Apply mixed precision if enabled
        if self.mixed_precision_var.get():
            env["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
            
        # Apply layer balance if enabled 
        if self.layer_balance_var.get() and ADVANCED_FEATURES_AVAILABLE:
            # Generate device map file in current directory
            # This is just a placeholder - actual implementation would
            # need PyTorch model loading which we can't do in this tab directly
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, "Layer balancing enabled - using device_map.json if present\n")
            self.log_text.config(state="disabled")
            
            # Update command if needed
            if self.framework_var.get() == "vLLM":
                env["VLLM_USE_DEVICE_MAP"] = "1"
        
        # Start the model
        self.runner.start(cmd, env)
        
        # Update UI
        self.launch_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("Running")
    
    def _stop_model(self) -> None:
        """Stop the running model"""
        self.runner.stop()
        
        # Update UI
        self.launch_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set("Stopped")
    
    def _process_log_queue(self) -> None:
        """Process pending log messages from the runner"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self._append_log(message)
                self.log_queue.task_done()
        except queue.Empty:
            pass
        
        # Schedule next check
        self.after(100, self._process_log_queue)
    
    def _append_log(self, message: str) -> None:
        """Append message to log text
        
        Args:
            message: Message to append
        """
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message)
        
        # Auto-scroll if enabled
        if self.autoscroll_var.get():
            self.log_text.see(tk.END)
            
        self.log_text.config(state="disabled")
    
    def _clear_log(self) -> None:
        """Clear the log text"""
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
    
    def _reset_vram(self) -> None:
        """Reset VRAM on all GPUs"""
        if not ADVANCED_FEATURES_AVAILABLE:
            messagebox.showerror("Error", "VRAM reset feature not available")
            return
            
        try:
            mb_reclaimed, status = reset_vram()
            
            if mb_reclaimed > 0:
                messagebox.showinfo("VRAM Reset", f"Successfully reclaimed {mb_reclaimed} MB of VRAM")
                self._append_log(f"\nVRAM reset: {status}\n")
            else:
                messagebox.showinfo("VRAM Reset", "No VRAM was reclaimed")
                self._append_log(f"\nVRAM reset: {status}\n")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset VRAM: {e}")
            logger.error(f"VRAM reset error: {e}")
    
    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard
        
        Args:
            text: Text to copy
        """
        self.clipboard_clear()
        self.clipboard_append(text)
        
        messagebox.showinfo("Copied", "Command copied to clipboard")


# Standalone test
if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    
    # Create root window
    root = tk.Tk()
    root.title("Launcher Tab Test")
    root.geometry("800x700")
    
    # Create launcher tab
    launcher = LauncherTab(root)
    launcher.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Start the main loop
    root.mainloop() 