#!/usr/bin/env python3
"""
Direct entry point for DualGPUOptimizer
Provides a simplified launch method that avoids complex module imports
"""
import logging
import tkinter as tk
from pathlib import Path
import time
import dataclasses
from typing import List

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

# Event system implementation
@dataclasses.dataclass
class Event:
    """Base class for all events"""
    timestamp: float = dataclasses.field(default_factory=time.time)
    source: str = "direct_app"

@dataclasses.dataclass
class GPUEvent(Event):
    """Base class for GPU-related events"""
    gpu_id: int = 0

@dataclasses.dataclass
class GPUMetricsEvent(GPUEvent):
    """Event for GPU metrics updates"""
    name: str = ""
    utilization: float = 0.0
    memory_used: int = 0
    memory_total: int = 0
    temperature: float = 0.0
    power_usage: float = 0.0
    power_limit: float = 0.0
    fan_speed: int = 0
    clock_sm: int = 0
    clock_memory: int = 0
    pcie_tx: int = 0
    pcie_rx: int = 0

@dataclasses.dataclass
class OptimizerEvent(Event):
    """Base class for optimizer-related events"""

@dataclasses.dataclass
class ModelSelectedEvent(OptimizerEvent):
    """Event fired when a model is selected"""
    model_name: str = ""
    context_length: int = 0
    hidden_size: int = 0
    num_layers: int = 0
    num_heads: int = 0
    kv_heads: int = 0

@dataclasses.dataclass
class SplitCalculatedEvent(OptimizerEvent):
    """Event fired when a split is calculated"""
    tensor_parallel_size: int = 0
    gpu_split: List[float] = dataclasses.field(default_factory=list)
    context_length: int = 0
    command_llama: str = ""
    command_vllm: str = ""

class EventBus:
    """Simple event bus implementation for component communication"""

    def __init__(self):
        """Initialize the event bus"""
        self._subscribers = {}
        self.logger = logging.getLogger("DualGPUOpt.EventBus")

    def subscribe(self, event_type, callback):
        """Subscribe to events of a specific type

        Args:
            event_type: Type of event to subscribe to (class)
            callback: Function to call when event is published
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            self.logger.debug(f"Subscribed to event type: {event_type.__name__}")

    def publish(self, event):
        """Publish an event to subscribers

        Args:
            event: Event instance to publish
        """
        for event_type, subscribers in self._subscribers.items():
            if isinstance(event, event_type):
                for callback in subscribers:
                    try:
                        callback(event)
                    except Exception as e:
                        self.logger.error(f"Error in event handler for {event_type.__name__}: {e}")

                self.logger.debug(f"Published event: {event_type.__name__} to {len(subscribers)} subscribers")

# Create a global event bus instance
event_bus = EventBus()

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
    from dualgpuopt.telemetry import get_telemetry_service
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

# Try to import the Optimizer component
try:
    from dualgpuopt.gui.optimizer_tab import OptimizerTab
    OPTIMIZER_AVAILABLE = True
    logger.info("Optimizer component available")
except ImportError:
    OPTIMIZER_AVAILABLE = False
    logger.warning("Optimizer component not available")

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
            self.telemetry.register_callback(self._on_telemetry_update)

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

            # Publish mock GPU metrics event
            event_bus.publish(GPUMetricsEvent(
                gpu_id=i,
                name=gpu['name'],
                utilization=gpu['util'],
                memory_used=gpu['mem_used'],
                memory_total=gpu['mem_total'],
                temperature=65,  # Mock temperature
                power_usage=150,  # Mock power
                power_limit=300,  # Mock power limit
            ))

    def _on_telemetry_update(self, metrics):
        """Handle telemetry update from the service

        Args:
            metrics: Dictionary of GPU ID to GPUMetrics objects
        """
        # Update display
        self.update_metrics(metrics)

        # Publish events through event bus
        for gpu_id, gpu_metrics in metrics.items():
            event_bus.publish(GPUMetricsEvent(
                gpu_id=gpu_id,
                name=gpu_metrics.name,
                utilization=gpu_metrics.utilization,
                memory_used=gpu_metrics.memory_used,
                memory_total=gpu_metrics.memory_total,
                temperature=gpu_metrics.temperature if hasattr(gpu_metrics, 'temperature') else 0,
                power_usage=gpu_metrics.power_usage if hasattr(gpu_metrics, 'power_usage') else 0,
                power_limit=gpu_metrics.power_limit if hasattr(gpu_metrics, 'power_limit') else 0,
                fan_speed=gpu_metrics.fan_speed if hasattr(gpu_metrics, 'fan_speed') else 0,
                clock_sm=gpu_metrics.clock_sm if hasattr(gpu_metrics, 'clock_sm') else 0,
                clock_memory=gpu_metrics.clock_memory if hasattr(gpu_metrics, 'clock_memory') else 0,
                pcie_tx=gpu_metrics.pcie_tx if hasattr(gpu_metrics, 'pcie_tx') else 0,
                pcie_rx=gpu_metrics.pcie_rx if hasattr(gpu_metrics, 'pcie_rx') else 0,
            ))

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

class EventDrivenDashboardWrapper(ttk.Frame):
    """Wrapper for the Dashboard view that connects it to the event system"""

    def __init__(self, parent):
        """Initialize the dashboard wrapper"""
        super().__init__(parent)
        self.pack(fill="both", expand=True)

        # Create the dashboard view
        self.dashboard = DashboardView(self)
        self.dashboard.pack(fill="both", expand=True)

        # Subscribe to GPU metrics events
        event_bus.subscribe(GPUMetricsEvent, self._on_gpu_metrics)

        logger.info("Dashboard wrapper initialized with event subscription")

    def _on_gpu_metrics(self, event):
        """Handle GPU metrics events"""
        # Convert to the format expected by the dashboard
        # The dashboard already has its own callbacks to the telemetry service,
        # so this is for demonstration purposes
        logger.debug(f"Dashboard received GPU metrics event for GPU {event.gpu_id}")

class BasicOptimizerFrame(ttk.LabelFrame):
    """Simple optimizer frame when the real optimizer is not available"""

    def __init__(self, parent):
        """Initialize the basic optimizer frame"""
        super().__init__(parent, text="GPU Split Optimizer")
        self.pack(fill="both", expand=True, padx=10, pady=10)

        # Create a simple UI with a message about the optimizer functionality
        ttk.Label(
            self,
            text="The GPU Split Optimizer functionality is not available.",
            font=("TkDefaultFont", 12)
        ).pack(pady=20)

        ttk.Label(
            self,
            text="This component would calculate optimal GPU split configurations\nfor running large language models across multiple GPUs.",
            justify="center"
        ).pack(pady=10)

        # Installation message
        install_frame = ttk.Frame(self)
        install_frame.pack(pady=20, fill="x")

        ttk.Label(
            install_frame,
            text="To enable this functionality, install the required dependencies:",
            font=("TkDefaultFont", 10, "italic")
        ).pack(anchor="w", padx=20)

        # Code frame with dependencies
        code_frame = ttk.Frame(self, relief="sunken", borderwidth=1)
        code_frame.pack(padx=30, pady=10, fill="x")

        dependencies = "pip install numpy pynvml"

        if not TTKBOOTSTRAP_AVAILABLE:
            dependencies += "\npip install ttkbootstrap"

        ttk.Label(
            code_frame,
            text=dependencies,
            font=("Courier", 10),
            justify="left"
        ).pack(padx=10, pady=10, anchor="w")

        # Sample GUI representation
        sample_frame = ttk.LabelFrame(self, text="Sample Split Configuration")
        sample_frame.pack(padx=20, pady=20, fill="x")

        ttk.Label(sample_frame, text="Tensor Parallel Size:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(sample_frame, text="2 GPUs").grid(row=0, column=1, sticky="w", padx=10, pady=5)

        ttk.Label(sample_frame, text="GPU Split Ratio:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(sample_frame, text="0.67, 0.33").grid(row=1, column=1, sticky="w", padx=10, pady=5)

        ttk.Label(sample_frame, text="Context Length:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(sample_frame, text="4096 tokens").grid(row=2, column=1, sticky="w", padx=10, pady=5)

        # Subscribe to GPU metrics events to demonstrate event listening
        event_bus.subscribe(GPUMetricsEvent, self._on_gpu_metrics)

    def _on_gpu_metrics(self, event):
        """Handle GPU metrics events"""
        # This is just for demonstration - would update UI based on metrics
        logger.debug(f"BasicOptimizerFrame received GPU metrics for GPU {event.gpu_id}")

class EventDrivenOptimizerWrapper(ttk.Frame):
    """Wrapper for the Optimizer tab that connects it to the event system"""

    def __init__(self, parent):
        """Initialize the optimizer wrapper"""
        super().__init__(parent)
        self.pack(fill="both", expand=True)

        # Create the optimizer tab
        self.optimizer = OptimizerTab(self)
        self.optimizer.pack(fill="both", expand=True)

        # Subscribe to relevant GPU events
        event_bus.subscribe(GPUMetricsEvent, self._on_gpu_metrics)

        # Monkey patch some methods to publish events
        self._patch_optimizer_methods()

        logger.info("Optimizer wrapper initialized with event subscription")

    def _on_gpu_metrics(self, event):
        """Handle GPU metrics events"""
        # Optimizer might use GPU metrics for calculations
        logger.debug(f"Optimizer received GPU metrics event for GPU {event.gpu_id}")

    def _patch_optimizer_methods(self):
        """Patch optimizer methods to publish events"""
        original_on_model_selected = self.optimizer._on_model_selected
        original_calculate_split = self.optimizer._calculate_split

        def on_model_selected_with_event(event):
            """Wrap the model selection method to publish events"""
            # Call original method
            original_on_model_selected(event)

            # Publish event
            model_name = self.optimizer.model_var.get()
            if model_name != "Custom":
                model = self.optimizer._get_model_parameters()
                event_bus.publish(ModelSelectedEvent(
                    model_name=model.name,
                    context_length=model.context_length,
                    hidden_size=model.hidden_size,
                    num_layers=model.num_layers,
                    num_heads=model.num_heads,
                    kv_heads=model.kv_heads if hasattr(model, 'kv_heads') else 0
                ))
                logger.info(f"Published ModelSelectedEvent for {model_name}")

        def calculate_split_with_event():
            """Wrap the split calculation method to publish events"""
            # Call original method
            original_calculate_split()

            # Extract data from optimizer
            try:
                llama_cmd = self.optimizer.llama_cmd_var.get()
                vllm_cmd = self.optimizer.vllm_cmd_var.get()

                # Publish event only if commands were generated
                if llama_cmd and vllm_cmd:
                    event_bus.publish(SplitCalculatedEvent(
                        tensor_parallel_size=2,  # Would extract from actual results
                        gpu_split=[0.6, 0.4],    # Would extract from actual results
                        context_length=self.optimizer._get_model_parameters().context_length,
                        command_llama=llama_cmd,
                        command_vllm=vllm_cmd
                    ))
                    logger.info("Published SplitCalculatedEvent")
            except Exception as e:
                logger.error(f"Error publishing SplitCalculatedEvent: {e}")

        # Replace the methods
        self.optimizer._on_model_selected = on_model_selected_with_event
        self.optimizer._calculate_split = calculate_split_with_event

def create_monitoring_component(parent):
    """Create the appropriate monitoring component based on available dependencies

    Args:
        parent: Parent widget

    Returns:
        The created monitoring component
    """
    if DASHBOARD_AVAILABLE:
        # Use the full dashboard if available, wrapped to connect to event system
        logger.info("Using comprehensive dashboard view with event system")
        return EventDrivenDashboardWrapper(parent)
    else:
        # Fall back to the basic GPU info frame
        logger.info("Using basic GPU info frame")
        return GPUInfoFrame(parent)

def create_optimizer_component(parent):
    """Create the appropriate optimizer component based on available dependencies

    Args:
        parent: Parent widget

    Returns:
        The created optimizer component
    """
    if OPTIMIZER_AVAILABLE:
        # Use the full optimizer if available, wrapped to connect to event system
        logger.info("Using comprehensive optimizer view with event system")
        return EventDrivenOptimizerWrapper(parent)
    else:
        # Fall back to the basic optimizer info frame
        logger.info("Using basic optimizer information frame")
        return BasicOptimizerFrame(parent)

class StatusBar(ttk.Frame):
    """Status bar for displaying application events"""

    def __init__(self, parent):
        """Initialize the status bar"""
        super().__init__(parent)
        self.pack(side="bottom", fill="x")

        # Create border
        self.config(relief="sunken", borderwidth=1)

        # Status message label
        self.status_label = ttk.Label(self, text="Ready", padding=(5, 2))
        self.status_label.pack(side="left")

        # Subscribe to events
        event_bus.subscribe(GPUMetricsEvent, self._on_gpu_metrics)
        event_bus.subscribe(ModelSelectedEvent, self._on_model_selected)
        event_bus.subscribe(SplitCalculatedEvent, self._on_split_calculated)

        # Store last update time
        self.last_update = 0

    def _on_gpu_metrics(self, event):
        """Handle GPU metrics events"""
        # Limit updates to once per second to avoid overwhelming the UI
        now = time.time()
        if now - self.last_update < 1.0:
            return

        self.last_update = now
        self.status_label.config(
            text=f"GPU {event.gpu_id} metrics: {event.utilization:.1f}% util, {event.memory_used}/{event.memory_total} MB"
        )

    def _on_model_selected(self, event):
        """Handle model selection events"""
        self.status_label.config(
            text=f"Model selected: {event.model_name}, {event.num_layers} layers, {event.hidden_size} hidden size"
        )

    def _on_split_calculated(self, event):
        """Handle split calculation events"""
        self.status_label.config(
            text=f"Split calculated: {event.tensor_parallel_size} GPUs, context length {event.context_length}"
        )

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

    if OPTIMIZER_AVAILABLE:
        status_components.append("Optimizer Available")

    status_components.append("Event System Active")

    status_text = " | ".join(status_components)

    ttk.Label(
        main_frame,
        text=status_text,
        font=("TkDefaultFont", 12)
    ).pack(pady=10)

    # Create notebook for tabs
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill="both", expand=True, padx=5, pady=5)

    # Create the monitoring tab
    monitoring_tab = ttk.Frame(notebook)
    notebook.add(monitoring_tab, text="GPU Dashboard")

    # Add the monitoring component to its tab
    monitoring_component = create_monitoring_component(monitoring_tab)
    monitoring_component.pack(fill="both", expand=True)

    # Create the optimizer tab
    optimizer_tab = ttk.Frame(notebook)
    notebook.add(optimizer_tab, text="Optimizer")

    # Add the optimizer component to its tab
    optimizer_component = create_optimizer_component(optimizer_tab)
    optimizer_component.pack(fill="both", expand=True)

    # Add a status bar at the bottom
    StatusBar(main_frame)

    # Add button frame at the bottom
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(side="bottom", fill="x", pady=10)

    # Add styled buttons - handle bootstyle for ttkbootstrap
    if TTKBOOTSTRAP_AVAILABLE:
        # Exit button
        ttk.Button(
            button_frame,
            text="Exit",
            bootstyle="danger",
            command=root.destroy
        ).pack(side="right", padx=10)
    else:
        # Plain ttk buttons
        ttk.Button(
            button_frame,
            text="Exit",
            command=root.destroy
        ).pack(side="right", padx=10)

    # Log event about application starting
    logger.info("Starting direct application with event system")
    event_bus.publish(Event(source="main", timestamp=time.time()))

    # Run the application
    root.mainloop()

if __name__ == "__main__":
    # Ensure the logs directory exists
    Path("logs").mkdir(exist_ok=True)

    # Run the application
    main()