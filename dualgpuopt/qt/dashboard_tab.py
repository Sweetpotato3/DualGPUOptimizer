"""
Dashboard tab for DualGPUOptimizer Qt implementation.
Provides real-time GPU metrics and monitoring.
"""
import logging
from typing import Dict, List, Optional, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QLabel, QProgressBar, QPushButton, QGridLayout
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

# Import telemetry
from dualgpuopt.telemetry import get_telemetry_service, GPUMetrics

logger = logging.getLogger('DualGPUOptimizer.Dashboard')

class GPUMetricsWidget(QWidget):
    """Widget to display GPU metrics for a single GPU"""
    
    def __init__(self, gpu_index: int, parent: Optional[QWidget] = None):
        """Initialize the GPU metrics widget
        
        Args:
            gpu_index: GPU index (0-based)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.gpu_index = gpu_index
        
        # Initialize UI components
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # GPU name and info
        self.name_label = QLabel(f"GPU {self.gpu_index}")
        font = self.name_label.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        self.name_label.setFont(font)
        layout.addWidget(self.name_label)
        
        # Grid layout for metrics
        metrics_layout = QGridLayout()
        metrics_layout.setColumnStretch(1, 1)  # Make progress bars stretch
        metrics_layout.setHorizontalSpacing(10)
        metrics_layout.setVerticalSpacing(5)
        
        # Utilization
        metrics_layout.addWidget(QLabel("Utilization:"), 0, 0)
        self.util_bar = QProgressBar()
        self.util_bar.setRange(0, 100)
        self.util_bar.setValue(0)
        metrics_layout.addWidget(self.util_bar, 0, 1)
        
        # Memory
        metrics_layout.addWidget(QLabel("Memory:"), 1, 0)
        self.memory_bar = QProgressBar()
        self.memory_bar.setRange(0, 100)
        self.memory_bar.setValue(0)
        metrics_layout.addWidget(self.memory_bar, 1, 1)
        
        # Temperature
        metrics_layout.addWidget(QLabel("Temperature:"), 2, 0)
        self.temp_bar = QProgressBar()
        self.temp_bar.setRange(0, 100)
        self.temp_bar.setValue(0)
        metrics_layout.addWidget(self.temp_bar, 2, 1)
        
        # Power
        metrics_layout.addWidget(QLabel("Power:"), 3, 0)
        self.power_bar = QProgressBar()
        self.power_bar.setRange(0, 100)
        self.power_bar.setValue(0)
        metrics_layout.addWidget(self.power_bar, 3, 1)
        
        layout.addLayout(metrics_layout)
        
        # Values display
        self.values_label = QLabel("Memory: 0/0 MB | Clocks: 0/0 MHz | PCIe: 0/0 MB/s")
        self.values_label.setWordWrap(True)
        layout.addWidget(self.values_label)
    
    def update_metrics(self, metrics: GPUMetrics):
        """Update the widget with new metrics
        
        Args:
            metrics: GPU metrics
        """
        # Update name
        self.name_label.setText(metrics.name)
        
        # Update progress bars
        self.util_bar.setValue(metrics.utilization)
        self._update_bar_color(self.util_bar, metrics.utilization, 50, 90)
        
        memory_percent = metrics.memory_percent
        self.memory_bar.setValue(int(memory_percent))
        self._update_bar_color(self.memory_bar, memory_percent, 75, 90)
        
        self.temp_bar.setValue(metrics.temperature)
        self._update_bar_color(self.temp_bar, metrics.temperature, 70, 85)
        
        power_percent = metrics.power_percent
        self.power_bar.setValue(int(power_percent))
        self._update_bar_color(self.power_bar, power_percent, 80, 95)
        
        # Update values
        values_text = (
            f"Memory: {metrics.memory_used}/{metrics.memory_total} MB ({memory_percent:.1f}%)\n"
            f"Clocks: {metrics.clock_sm}/{metrics.clock_memory} MHz\n"
            f"PCIe: TX {metrics.pcie_tx/1024:.1f} MB/s, RX {metrics.pcie_rx/1024:.1f} MB/s"
        )
        self.values_label.setText(values_text)
    
    def _update_bar_color(self, bar: QProgressBar, value: float, warning_threshold: float, critical_threshold: float):
        """Update progress bar color based on value thresholds
        
        Args:
            bar: Progress bar to update
            value: Current value
            warning_threshold: Threshold for warning color
            critical_threshold: Threshold for critical color
        """
        # Set color based on value
        if value < warning_threshold:
            # Normal - blue
            bar.setStyleSheet("QProgressBar::chunk { background-color: #4C8BF5; }")
        elif value < critical_threshold:
            # Warning - orange
            bar.setStyleSheet("QProgressBar::chunk { background-color: #FF9500; }")
        else:
            # Critical - red
            bar.setStyleSheet("QProgressBar::chunk { background-color: #F15532; }")

class DashboardTab(QWidget):
    """Dashboard tab for GPU monitoring"""
    
    def __init__(self, mock_mode: bool = False, parent: Optional[QWidget] = None):
        """Initialize the dashboard tab
        
        Args:
            mock_mode: Whether to use mock GPU data
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.mock_mode = mock_mode
        self.gpu_widgets = []
        
        # Setup the UI
        self._setup_ui()
        
        # Start the telemetry service
        self._init_telemetry()
        
        # Setup update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_metrics)
        self.update_timer.start(1000)  # Update every second
    
    def _setup_ui(self):
        """Set up the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("GPU Dashboard")
        title_font = title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 2)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # GPU metrics group
        self.metrics_group = QGroupBox("GPU Metrics")
        self.metrics_layout = QHBoxLayout(self.metrics_group)
        main_layout.addWidget(self.metrics_group)
        
        # Actions group
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        # Reset memory button
        reset_memory_button = QPushButton("Reset GPU Memory")
        reset_memory_button.clicked.connect(self._reset_gpu_memory)
        actions_layout.addWidget(reset_memory_button)
        
        main_layout.addWidget(actions_group)
        
        # Status label
        self.status_label = QLabel("Initializing telemetry service...")
        main_layout.addWidget(self.status_label)
        
        # Add stretch to push everything to the top
        main_layout.addStretch(1)
    
    def _init_telemetry(self):
        """Initialize telemetry service"""
        try:
            # Get telemetry service
            self.telemetry_service = get_telemetry_service()
            
            # Start service (creates a background thread)
            self.telemetry_service.start()
            
            # Get initial metrics to determine GPU count
            metrics = self.telemetry_service.get_metrics()
            self._create_gpu_widgets(len(metrics))
            
            # Register callback for updates
            self.telemetry_service.register_callback(self._telemetry_callback)
            
            self.status_label.setText("Telemetry service running")
            logger.info("Telemetry service initialized")
        except Exception as e:
            self.status_label.setText(f"Error initializing telemetry: {e}")
            logger.error(f"Failed to initialize telemetry: {e}")
    
    def _create_gpu_widgets(self, gpu_count: int):
        """Create widgets for each GPU
        
        Args:
            gpu_count: Number of GPUs
        """
        # Clear existing widgets
        self.gpu_widgets = []
        
        # Create a widget for each GPU
        for i in range(gpu_count):
            widget = GPUMetricsWidget(i)
            self.metrics_layout.addWidget(widget)
            self.gpu_widgets.append(widget)
        
        self.status_label.setText(f"Monitoring {gpu_count} GPUs")
    
    def _telemetry_callback(self, metrics: Dict[int, GPUMetrics]):
        """Callback for telemetry updates
        
        Args:
            metrics: Dictionary of GPU metrics
        """
        # Check if we need to create GPU widgets
        if not self.gpu_widgets and metrics:
            self._create_gpu_widgets(len(metrics))
        
        # Update each GPU widget
        for gpu_id, gpu_metrics in metrics.items():
            if gpu_id < len(self.gpu_widgets):
                self.gpu_widgets[gpu_id].update_metrics(gpu_metrics)
    
    def _update_metrics(self):
        """Update metrics from telemetry service"""
        if hasattr(self, 'telemetry_service'):
            metrics = self.telemetry_service.get_metrics()
            self._telemetry_callback(metrics)
    
    def _reset_gpu_memory(self):
        """Reset GPU memory"""
        try:
            import torch
            torch.cuda.empty_cache()
            self.status_label.setText("GPU memory reset successful")
            logger.info("GPU memory reset successful")
        except ImportError:
            self.status_label.setText("PyTorch not available for memory reset")
            logger.warning("PyTorch not available for memory reset")
        except Exception as e:
            self.status_label.setText(f"Failed to reset GPU memory: {e}")
            logger.error(f"Failed to reset GPU memory: {e}")
    
    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        # Update metrics when tab is shown
        self._update_metrics()
    
    def hideEvent(self, event):
        """Handle hide event"""
        super().hideEvent(event)
        # Stop timer when tab is hidden to save resources
        self.update_timer.stop()
    
    def closeEvent(self, event):
        """Handle close event"""
        # Stop telemetry service if it's running
        if hasattr(self, 'telemetry_service'):
            self.telemetry_service.unregister_callback(self._telemetry_callback)
        
        # Stop timer
        if self.update_timer.isActive():
            self.update_timer.stop()
        
        super().closeEvent(event) 