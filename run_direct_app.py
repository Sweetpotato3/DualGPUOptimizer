#!/usr/bin/env python3
"""
Direct entry point for DualGPUOptimizer
Provides a simplified launch method that avoids complex module imports
"""
import sys
import logging
import tkinter as tk
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path("logs") / "direct_app.log"),
    ]
)

logger = logging.getLogger("DualGPUOpt.DirectLauncher")

# Try to import dependencies at the module level
try:
    import ttkbootstrap as ttk
    TTKBOOTSTRAP_AVAILABLE = True
    logger.info("ttkbootstrap available for import")
except ImportError:
    from tkinter import ttk
    TTKBOOTSTRAP_AVAILABLE = False
    logger.warning("ttkbootstrap not available - using standard ttk")

# Try to import GPU monitoring capabilities
try:
    from dualgpuopt.gpu.compat import is_mock_mode, set_mock_mode, generate_mock_gpus
    GPU_COMPAT_AVAILABLE = True
    logger.info("GPU compatibility layer available")
except ImportError:
    GPU_COMPAT_AVAILABLE = False
    logger.warning("GPU compatibility layer not available - using mock data")
    
    # Create minimal mock functions if not available
    def is_mock_mode():
        return True
        
    def set_mock_mode(enabled=True):
        pass
        
    def generate_mock_gpus(count=2):
        return [
            {"id": 0, "name": "Mock GPU 0", "mem_total": 24576, "mem_used": 8192, "util": 45},
            {"id": 1, "name": "Mock GPU 1", "mem_total": 12288, "mem_used": 10240, "util": 85}
        ]

def create_gpu_info_frame(parent):
    """Create a frame showing GPU information"""
    # Create a frame for GPU info
    frame = ttk.LabelFrame(parent, text="GPU Information")
    frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Enable mock mode for testing
    if GPU_COMPAT_AVAILABLE:
        set_mock_mode(True)
        logger.info("Mock GPU mode enabled")
    
    # Get mock GPU data
    gpus = generate_mock_gpus(2)
    
    # Display information for each GPU
    for i, gpu in enumerate(gpus):
        # GPU name and basic info
        ttk.Label(
            frame,
            text=f"GPU {i}: {gpu['name']}",
            font=("TkDefaultFont", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 0))
        
        # Memory usage
        mem_used_mb = gpu['mem_used']
        mem_total_mb = gpu['mem_total']
        mem_percent = int((mem_used_mb / mem_total_mb) * 100)
        
        ttk.Label(
            frame,
            text=f"Memory: {mem_used_mb}MB / {mem_total_mb}MB ({mem_percent}%)"
        ).pack(anchor="w", padx=20)
        
        # GPU utilization
        ttk.Label(
            frame,
            text=f"Utilization: {gpu['util']}%"
        ).pack(anchor="w", padx=20)
        
        # Add a separator between GPUs
        if i < len(gpus) - 1:
            ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=10, pady=10)
    
    # Add note about mock mode
    ttk.Label(
        frame,
        text="Running in mock GPU mode - data is simulated",
        font=("TkDefaultFont", 10, "italic")
    ).pack(anchor="w", padx=10, pady=10)
    
    return frame

def main():
    """Main entry point"""
    # Set up the root window
    root = tk.Tk()
    root.title("DualGPUOptimizer - Direct")
    root.geometry("1024x768")
    
    # Create main frame
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Header with app name
    ttk.Label(
        main_frame, 
        text="DualGPUOptimizer",
        font=("TkDefaultFont", 24)
    ).pack(pady=20)
    
    # Status message based on dependency availability
    if TTKBOOTSTRAP_AVAILABLE:
        status_text = "Enhanced UI Loaded Successfully"
        if GPU_COMPAT_AVAILABLE:
            status_text += " | GPU Monitoring Available"
    else:
        status_text = "Basic UI Mode (Enhanced UI not available)"
        if not GPU_COMPAT_AVAILABLE:
            status_text += " | GPU Monitoring Limited"
    
    ttk.Label(
        main_frame,
        text=status_text,
        font=("TkDefaultFont", 12)
    ).pack(pady=10)
    
    # Add the GPU info frame
    gpu_frame = create_gpu_info_frame(main_frame)
    
    # Add button frame at the bottom
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(side="bottom", fill="x", pady=20)
    
    # Add a styled button - handle bootstyle for ttkbootstrap
    if TTKBOOTSTRAP_AVAILABLE:
        ttk.Button(
            button_frame,
            text="Refresh GPU Info",
            bootstyle="success"
        ).pack(side="left", padx=10)
        
        ttk.Button(
            button_frame,
            text="Open Optimizer",
            bootstyle="info"
        ).pack(side="left", padx=10)
    else:
        ttk.Button(
            button_frame,
            text="Refresh GPU Info"
        ).pack(side="left", padx=10)
        
        ttk.Button(
            button_frame,
            text="Open Optimizer"
        ).pack(side="left", padx=10)
    
    # Run the application
    logger.info("Starting direct application")
    root.mainloop()

if __name__ == "__main__":
    # Ensure the logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Run the application
    main() 