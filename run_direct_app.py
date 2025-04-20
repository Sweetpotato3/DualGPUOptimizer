#!/usr/bin/env python3
"""
Direct entry point for DualGPUOptimizer
Provides a simplified launch method that avoids complex module imports
"""
import sys
import logging
import tkinter as tk
from pathlib import Path
import time
import threading

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

# Try to import telemetry system
try:
    from dualgpuopt.telemetry import get_telemetry_service, GPUMetrics
    TELEMETRY_AVAILABLE = True
    logger.info("Telemetry system available")
except ImportError:
    TELEMETRY_AVAILABLE = False
    logger.warning("Telemetry system not available - using basic mock data")

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

# Try to import the Dashboard component
try:
    from dualgpuopt.gui.dashboard import DashboardView
    DASHBOARD_AVAILABLE = True
    logger.info("Dashboard component available")
except ImportError:
    DASHBOARD_AVAILABLE = False
    logger.warning("Dashboard component not available - using basic monitoring")

class GPUInfoFrame(ttk.LabelFrame):
    """Frame showing GPU information with real-time updates"""
    
    def __init__(self, parent):
        """Initialize the GPU info frame"""
        super().__init__(parent, text="GPU Information")
        self.pack(fill="both", expand=True, padx=10, pady=10)
        
        # GPU frames dictionary - will hold widgets for each GPU
        self.gpu_frames = {}
        
        # Status label
        self.status_label = ttk.Label(
            self,
            text="Status: Initializing...",
            font=("TkDefaultFont", 10, "italic")
        )
        self.status_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Setup telemetry if available
        if TELEMETRY_AVAILABLE:
            self.telemetry = get_telemetry_service()
            self.telemetry.register_callback(self.update_metrics)
            
            # Start telemetry service
            try:
                self.telemetry.start()
                self.status_label.config(text="Status: Monitoring active - real-time data")
                logger.info("Telemetry service started")
            except Exception as e:
                logger.error(f"Failed to start telemetry: {e}")
                self.status_label.config(text="Status: Error starting monitoring")
                self._create_static_display()
        else:
            self.telemetry = None
            self.status_label.config(text="Status: Telemetry not available - using mock data")
            self._create_static_display()
    
    def _create_static_display(self):
        """Create a static display with mock GPU data"""
        if GPU_COMPAT_AVAILABLE:
            set_mock_mode(True)
            logger.info("Mock GPU mode enabled for static display")
        
        # Get mock GPU data
        gpus = generate_mock_gpus(2)
        
        # Display information for each GPU
        for i, gpu in enumerate(gpus):
            # Create frame for this GPU
            frame = ttk.Frame(self)
            frame.pack(fill="x", pady=5)
            self.gpu_frames[i] = frame
            
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
    
    def update_metrics(self, metrics):
        """Update the display with new GPU metrics
        
        Args:
            metrics: Dictionary of GPU ID to GPUMetrics objects
        """
        # Clear existing frames if the GPUs changed
        current_gpus = set(metrics.keys())
        if set(self.gpu_frames.keys()) != current_gpus:
            for frame in self.gpu_frames.values():
                frame.destroy()
            self.gpu_frames = {}
        
        # Update or create frames for each GPU
        for gpu_id, gpu_metrics in metrics.items():
            if gpu_id not in self.gpu_frames:
                # Create a new frame for this GPU
                frame = ttk.Frame(self)
                frame.pack(fill="x", pady=5)
                
                # GPU name label
                name_label = ttk.Label(
                    frame,
                    text=f"GPU {gpu_id}: {gpu_metrics.name}",
                    font=("TkDefaultFont", 14, "bold")
                )
                name_label.pack(anchor="w", padx=10, pady=(10, 0))
                
                # Memory usage
                mem_label = ttk.Label(frame)
                mem_label.pack(anchor="w", padx=20)
                
                # Utilization
                util_label = ttk.Label(frame)
                util_label.pack(anchor="w", padx=20)
                
                # Temperature
                temp_label = ttk.Label(frame)
                temp_label.pack(anchor="w", padx=20)
                
                # Power usage
                power_label = ttk.Label(frame)
                power_label.pack(anchor="w", padx=20)
                
                # Add separator if not the last GPU
                if gpu_id < max(metrics.keys()):
                    ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=10, pady=10)
                
                # Store widgets
                self.gpu_frames[gpu_id] = {
                    'frame': frame,
                    'name_label': name_label,
                    'mem_label': mem_label,
                    'util_label': util_label,
                    'temp_label': temp_label,
                    'power_label': power_label
                }
            
            # Update existing frame with new metrics
            widgets = self.gpu_frames[gpu_id]
            
            # Memory info with formatting
            mem_percent = gpu_metrics.memory_percent
            widgets['mem_label'].config(
                text=f"Memory: {gpu_metrics.memory_used}MB / {gpu_metrics.memory_total}MB ({mem_percent:.1f}%)"
            )
            
            # Utilization
            widgets['util_label'].config(
                text=f"Utilization: {gpu_metrics.utilization}%"
            )
            
            # Temperature with color coding
            if hasattr(gpu_metrics, 'temperature'):
                temp_text = f"Temperature: {gpu_metrics.temperature}°C"
                widgets['temp_label'].config(text=temp_text)
                
                # Color coding based on temperature
                if gpu_metrics.temperature >= 80:
                    widgets['temp_label'].config(foreground="red")
                elif gpu_metrics.temperature >= 70:
                    widgets['temp_label'].config(foreground="orange")
                else:
                    widgets['temp_label'].config(foreground="green")
            
            # Power usage
            if hasattr(gpu_metrics, 'power_usage'):
                power_text = f"Power: {gpu_metrics.power_usage:.1f}W / {gpu_metrics.power_limit:.1f}W"
                widgets['power_label'].config(text=power_text)
    
    def destroy(self):
        """Clean up resources when the frame is destroyed"""
        if TELEMETRY_AVAILABLE and self.telemetry:
            self.telemetry.stop()
            logger.info("Telemetry service stopped")
        super().destroy()

def create_monitoring_component(parent):
    """Create the appropriate monitoring component based on available dependencies
    
    Args:
        parent: Parent widget
        
    Returns:
        The created monitoring component
    """
    if DASHBOARD_AVAILABLE:
        # Use the full dashboard if available
        logger.info("Using comprehensive dashboard view")
        return DashboardView(parent)
    else:
        # Fall back to the basic GPU info frame
        logger.info("Using basic GPU info frame")
        return GPUInfoFrame(parent)

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
    status_components = []
    
    if TTKBOOTSTRAP_AVAILABLE:
        status_components.append("Enhanced UI Loaded")
    else:
        status_components.append("Basic UI Mode")
    
    if DASHBOARD_AVAILABLE:
        status_components.append("Full Dashboard Active")
    elif TELEMETRY_AVAILABLE:
        status_components.append("Real-time Telemetry Active")
    elif GPU_COMPAT_AVAILABLE:
        status_components.append("GPU Compatibility Available")
    else:
        status_components.append("Limited GPU Monitoring")
    
    status_text = " | ".join(status_components)
    
    ttk.Label(
        main_frame,
        text=status_text,
        font=("TkDefaultFont", 12)
    ).pack(pady=10)
    
    # Add the monitoring component - either full dashboard or basic info frame
    monitoring_component = create_monitoring_component(main_frame)
    monitoring_component.pack(fill="both", expand=True)
    
    # Add button frame at the bottom
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(side="bottom", fill="x", pady=20)
    
    # Add styled buttons - handle bootstyle for ttkbootstrap
    if TTKBOOTSTRAP_AVAILABLE:
        # Exit button
        ttk.Button(
            button_frame,
            text="Exit",
            bootstyle="danger",
            command=root.destroy
        ).pack(side="right", padx=10)
        
        # If not using the full dashboard, keep the optimizer button
        if not DASHBOARD_AVAILABLE:
            ttk.Button(
                button_frame,
                text="Open Optimizer",
                bootstyle="info"
            ).pack(side="left", padx=10)
    else:
        # Plain ttk buttons
        ttk.Button(
            button_frame,
            text="Exit",
            command=root.destroy
        ).pack(side="right", padx=10)
        
        if not DASHBOARD_AVAILABLE:
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