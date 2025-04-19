"""
Main application module for DualGPUOptimizer
Provides the primary entry point for the GUI application
"""
import tkinter as tk
from tkinter import ttk
import threading
import time

def run():
    """Main entry point for the application"""
    root = tk.Tk()
    root.title("DualGPUOptimizer")
    root.geometry("800x600")
    
    # Set up the main frame
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Header with status
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill=tk.X, pady=(0, 10))
    
    title_label = ttk.Label(header_frame, text="Dual GPU Optimizer", font=("Arial", 16, "bold"))
    title_label.pack(side=tk.LEFT)
    
    status_label = ttk.Label(header_frame, text="Status: Ready", foreground="green")
    status_label.pack(side=tk.RIGHT)
    
    # GPU Info section
    info_frame = ttk.LabelFrame(main_frame, text="GPU Information", padding="10")
    info_frame.pack(fill=tk.X, pady=(0, 10))
    
    # Import torch here to avoid issues if it's not available
    try:
        import torch
        
        # GPU detection
        if torch.cuda.is_available():
            cuda_info = f"CUDA: {torch.version.cuda} (Available)"
            device_count = torch.cuda.device_count()
            
            for i in range(device_count):
                gpu_label = ttk.Label(
                    info_frame, 
                    text=f"GPU {i}: {torch.cuda.get_device_name(i)}",
                    font=("Arial", 12)
                )
                gpu_label.pack(anchor=tk.W, pady=(0, 5))
                
                # Create progress bars for utilization
                util_frame = ttk.Frame(info_frame)
                util_frame.pack(fill=tk.X, pady=(0, 10))
                
                ttk.Label(util_frame, text="Utilization:").pack(side=tk.LEFT, padx=(0, 10))
                
                util_bar = ttk.Progressbar(util_frame, length=300)
                util_bar.pack(side=tk.LEFT)
                util_bar["value"] = 0
                
                # Simulate changing utilization in background thread
                def update_utilization(bar):
                    import random
                    while True:
                        util = random.randint(0, 100)
                        bar["value"] = util
                        time.sleep(1)
                
                threading.Thread(target=update_utilization, args=(util_bar,), daemon=True).start()
        else:
            ttk.Label(info_frame, text="No CUDA-capable GPU detected", foreground="red").pack()
    except ImportError:
        ttk.Label(info_frame, text="PyTorch not installed", foreground="red").pack()
    
    # Actions section
    actions_frame = ttk.LabelFrame(main_frame, text="Actions", padding="10")
    actions_frame.pack(fill=tk.X, pady=(0, 10))
    
    # Add some buttons
    ttk.Button(actions_frame, text="Optimize GPU Split").pack(side=tk.LEFT, padx=(0, 10))
    ttk.Button(actions_frame, text="Launch Model").pack(side=tk.LEFT, padx=(0, 10))
    ttk.Button(actions_frame, text="Settings").pack(side=tk.LEFT)
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    run() 