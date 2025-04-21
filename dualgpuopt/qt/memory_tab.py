import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
import threading

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, 
    QPushButton, QSizePolicy, QSpacerItem, QComboBox, QTextEdit,
    QTabWidget, QCheckBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QFont, QColor

# Try to import matplotlib for visualization
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    
# Try to import numpy for data processing
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

logger = logging.getLogger('DualGPUOptimizer')

# Helper class to provide mock memory profiler if real one is not available
class MockMemoryProfiler:
    """Mock implementation of MemoryProfiler for testing"""
    
    def __init__(self):
        self._session_id = None
        self._is_profiling = False
        self._is_inference = False
        self._mock_data = {}
        self._start_time = None
    
    def start_profiling(self, session_id=None):
        """Start a mock profiling session"""
        self._session_id = session_id or f"mock_session_{int(time.time())}"
        self._is_profiling = True
        self._start_time = time.time()
        # Generate mock data for 2 GPUs
        self._mock_data = {
            0: [],
            1: []
        }
        return self._session_id
    
    def stop_profiling(self):
        """Stop the mock profiling session"""
        self._is_profiling = False
        return True
    
    def is_profiling_active(self):
        """Check if profiling is active"""
        return self._is_profiling
    
    def get_memory_timeline(self, gpu_id=None):
        """Get mock memory timeline data"""
        if not gpu_id:
            return self._mock_data
        
        # Generate some mock data if requested
        current_time = time.time()
        elapsed = current_time - self._start_time if self._start_time else 0
        
        # Clear old data
        if gpu_id in self._mock_data:
            self._mock_data[gpu_id] = []
        
        # Generate 60 data points with a sine wave pattern
        for i in range(60):
            point_time = current_time - (60 - i) * 0.5
            # Create a sine wave that increases over time
            if gpu_id == 0:
                # First GPU has higher usage with some spikes
                base = 4000 + (elapsed / 10) * 100  # Base increases slowly
                sine = 500 * np.sin(i / 5.0)  # Sine wave
                spike = 800 if i % 20 == 0 else 0  # Occasional spike
                mem_value = base + sine + spike
            else:
                # Second GPU has lower, steadier usage
                base = 2000 + (elapsed / 20) * 50
                sine = 300 * np.sin(i / 7.0)
                mem_value = base + sine
            
            self._mock_data.setdefault(gpu_id, []).append((point_time, mem_value))
        
        return self._mock_data.get(gpu_id, [])
    
    def start_inference(self, context=None):
        """Start mock inference tracking"""
        self._is_inference = True
        return True
    
    def end_inference(self, token_count=0, context=None):
        """End mock inference tracking"""
        self._is_inference = False
        return True
    
    def get_session_stats(self):
        """Get mock session statistics"""
        return {
            "session_id": self._session_id,
            "duration": time.time() - self._start_time if self._start_time else 0,
            "inference_count": 5,
            "token_count": 1024,
            "peak_memory": {0: 8192, 1: 4096},
            "avg_memory": {0: 6144, 1: 3072},
            "potential_leaks": [{"gpu_id": 0, "severity": "medium", "growth_rate": 0.05}],
            "allocation_spikes": [{"gpu_id": 1, "severity": "low", "size_mb": 512}]
        }
    
    def get_memory_events(self):
        """Get mock memory events"""
        return [
            {"timestamp": time.time() - 50, "type": "SESSION_START", "gpu_id": -1, "description": "Started profiling session"},
            {"timestamp": time.time() - 40, "type": "INFERENCE_START", "gpu_id": -1, "description": "Started inference #1"},
            {"timestamp": time.time() - 35, "type": "MEMORY_ALLOCATION", "gpu_id": 0, "description": "Allocated 512MB"},
            {"timestamp": time.time() - 30, "type": "INFERENCE_END", "gpu_id": -1, "description": "Ended inference #1"},
            {"timestamp": time.time() - 20, "type": "INFERENCE_START", "gpu_id": -1, "description": "Started inference #2"},
            {"timestamp": time.time() - 15, "type": "MEMORY_SPIKE", "gpu_id": 1, "description": "Memory spike detected: 1024MB"},
            {"timestamp": time.time() - 10, "type": "INFERENCE_END", "gpu_id": -1, "description": "Ended inference #2"}
        ]
    
    def export_timeline(self, filepath, format="csv"):
        """Mock export of timeline data"""
        return True


class MemoryChart(QFrame):
    """Memory timeline chart using matplotlib"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.timeline_data = {0: [], 1: []}
        self.gpu_colors = ['#8A54FD', '#4CAF50']  # Purple, Green
        self.show_gpu = {0: True, 1: True}  # Which GPUs to display
    
    def setup_ui(self):
        # Set up frame
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            MemoryChart {
                background-color: #372952;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        
        # Add title
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        
        title_label = QLabel("Memory Usage Timeline")
        title_label.setFont(title_font)
        self.layout.addWidget(title_label)
        
        # GPU selection layout
        self.gpu_selection = QHBoxLayout()
        
        # Add checkboxes for GPU selection
        self.gpu0_checkbox = QCheckBox("GPU 0")
        self.gpu0_checkbox.setChecked(True)
        self.gpu0_checkbox.toggled.connect(lambda checked: self.toggle_gpu(0, checked))
        
        self.gpu1_checkbox = QCheckBox("GPU 1")
        self.gpu1_checkbox.setChecked(True)
        self.gpu1_checkbox.toggled.connect(lambda checked: self.toggle_gpu(1, checked))
        
        self.gpu_selection.addWidget(self.gpu0_checkbox)
        self.gpu_selection.addWidget(self.gpu1_checkbox)
        self.gpu_selection.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Export button
        self.export_button = QPushButton("Export Data")
        self.export_button.clicked.connect(self.export_data)
        self.gpu_selection.addWidget(self.export_button)
        
        self.layout.addLayout(self.gpu_selection)
        
        if MATPLOTLIB_AVAILABLE:
            # Create matplotlib figure
            self.figure = Figure(figsize=(5, 4), dpi=100, facecolor='#372952')
            self.canvas = FigureCanvas(self.figure)
            self.canvas.setStyleSheet("background-color: transparent;")
            self.axes = self.figure.add_subplot(111)
            self.axes.set_facecolor('#2D1E40')
            
            # Style the plot
            self.axes.tick_params(colors='#FFFFFF')
            self.axes.spines['bottom'].set_color('#FFFFFF')
            self.axes.spines['top'].set_color('#FFFFFF')
            self.axes.spines['right'].set_color('#FFFFFF')
            self.axes.spines['left'].set_color('#FFFFFF')
            
            # Labels
            self.axes.set_xlabel('Time (s)', color='#FFFFFF')
            self.axes.set_ylabel('Memory Usage (MB)', color='#FFFFFF')
            self.axes.grid(True, linestyle='--', alpha=0.3)
            
            # Add to layout
            self.layout.addWidget(self.canvas)
        else:
            # Fallback message if matplotlib is not available
            fallback = QLabel("Matplotlib not available. Install it for memory visualization.")
            fallback.setAlignment(Qt.AlignCenter)
            fallback.setStyleSheet("padding: 20px;")
            self.layout.addWidget(fallback)
    
    def toggle_gpu(self, gpu_id, show):
        """Toggle visibility of a GPU in the chart"""
        self.show_gpu[gpu_id] = show
        self.update_chart()
    
    def update_data(self, timeline_data):
        """Update chart with new timeline data"""
        self.timeline_data = timeline_data
        self.update_chart()
    
    def update_chart(self):
        """Redraw the chart with current data"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        # Clear the axes
        self.axes.clear()
        
        # Draw each visible GPU's data
        for gpu_id, visible in self.show_gpu.items():
            if not visible or gpu_id not in self.timeline_data:
                continue
                
            data = self.timeline_data[gpu_id]
            if not data:
                continue
                
            # Extract time and memory values, converting to relative time
            if data and len(data[0]) >= 2:
                times = [point[0] for point in data]
                # Convert to relative time in seconds from start
                if times:
                    start_time = min(times)
                    rel_times = [t - start_time for t in times]
                    memory_values = [point[1] for point in data]  # MB values
                    
                    # Plot the data
                    self.axes.plot(rel_times, memory_values, 
                                  label=f'GPU {gpu_id}',
                                  color=self.gpu_colors[gpu_id % len(self.gpu_colors)])
        
        # Set labels and legend
        self.axes.set_xlabel('Time (s)', color='#FFFFFF')
        self.axes.set_ylabel('Memory Usage (MB)', color='#FFFFFF')
        self.axes.grid(True, linestyle='--', alpha=0.3)
        self.axes.legend(facecolor='#2D1E40', labelcolor='#FFFFFF')
        
        # Style the axes
        self.axes.tick_params(colors='#FFFFFF')
        self.axes.spines['bottom'].set_color('#FFFFFF')
        self.axes.spines['top'].set_color('#FFFFFF')
        self.axes.spines['right'].set_color('#FFFFFF')
        self.axes.spines['left'].set_color('#FFFFFF')
        
        # Draw the canvas
        self.figure.tight_layout()
        self.canvas.draw()
    
    def export_data(self):
        """Export timeline data to CSV file"""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Export Memory Timeline", "", "CSV Files (*.csv);;All Files (*)",
            options=options
        )
        
        if file_name:
            try:
                with open(file_name, 'w') as f:
                    # Write header
                    f.write("timestamp,gpu_id,memory_mb\n")
                    
                    # Write data for each GPU
                    for gpu_id, data in self.timeline_data.items():
                        for point in data:
                            if len(point) >= 2:
                                timestamp = point[0]
                                memory_mb = point[1]
                                f.write(f"{timestamp},{gpu_id},{memory_mb}\n")
                
                logger.info(f"Exported memory timeline to {file_name}")
            except Exception as e:
                logger.error(f"Error exporting timeline data: {e}")


class EventLogView(QFrame):
    """Memory event log viewer"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        # Set up frame
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            EventLogView {
                background-color: #372952;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Add title
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        
        title_label = QLabel("Memory Events")
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Event log text area
        self.event_log = QTextEdit()
        self.event_log.setReadOnly(True)
        self.event_log.setStyleSheet("""
            QTextEdit {
                background-color: #241934;
                color: #FFFFFF;
                border-radius: 4px;
                border: 1px solid #3D2A50;
                padding: 8px;
            }
        """)
        layout.addWidget(self.event_log)
    
    def add_event(self, event):
        """Add a memory event to the log"""
        if not event:
            return
            
        timestamp = event.get("timestamp", time.time())
        event_type = event.get("type", "UNKNOWN")
        gpu_id = event.get("gpu_id", -1)
        description = event.get("description", "No description")
        
        # Format timestamp
        timestamp_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
        
        # Color based on event type
        color = "#FFFFFF"  # Default white
        if event_type == "MEMORY_LEAK":
            color = "#F44336"  # Red
        elif event_type == "MEMORY_SPIKE":
            color = "#FF9800"  # Orange
        elif event_type == "MEMORY_ALLOCATION":
            color = "#8A54FD"  # Purple
        elif event_type == "MEMORY_FREE":
            color = "#4CAF50"  # Green
        elif "INFERENCE" in event_type:
            color = "#2196F3"  # Blue
        
        # Format text with HTML
        gpu_text = f"GPU {gpu_id}" if gpu_id >= 0 else "All GPUs"
        html = f"<font color='#A0A0A0'>[{timestamp_str}]</font> " \
               f"<font color='{color}'><b>{event_type}</b></font> " \
               f"({gpu_text}): {description}<br>"
        
        # Add to log
        self.event_log.insertHtml(html)
        
        # Scroll to bottom
        scrollbar = self.event_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_events(self, events):
        """Update with a list of events"""
        # Clear current content
        self.event_log.clear()
        
        # Add each event
        for event in events:
            self.add_event(event)


class MemoryStatsPanel(QFrame):
    """Panel showing memory statistics and analysis"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        # Set up frame
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            MemoryStatsPanel {
                background-color: #372952;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Add title
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        
        title_label = QLabel("Memory Analysis")
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Session info grid
        info_grid = QGridLayout()
        info_grid.setColumnStretch(1, 1)
        layout.addLayout(info_grid)
        
        # Session ID
        info_grid.addWidget(QLabel("Session ID:"), 0, 0)
        self.session_id_label = QLabel("None")
        info_grid.addWidget(self.session_id_label, 0, 1)
        
        # Duration
        info_grid.addWidget(QLabel("Duration:"), 1, 0)
        self.duration_label = QLabel("0s")
        info_grid.addWidget(self.duration_label, 1, 1)
        
        # Inference count
        info_grid.addWidget(QLabel("Inferences:"), 2, 0)
        self.inference_label = QLabel("0")
        info_grid.addWidget(self.inference_label, 2, 1)
        
        # Token count
        info_grid.addWidget(QLabel("Total Tokens:"), 3, 0)
        self.token_label = QLabel("0")
        info_grid.addWidget(self.token_label, 3, 1)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #3D2A50;")
        layout.addWidget(separator)
        
        # Analysis Title
        analysis_title = QLabel("Memory Issues")
        analysis_title.setFont(title_font)
        layout.addWidget(analysis_title)
        
        # Analysis text
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setStyleSheet("""
            QTextEdit {
                background-color: #241934;
                color: #FFFFFF;
                border-radius: 4px;
                border: 1px solid #3D2A50;
                padding: 8px;
            }
        """)
        layout.addWidget(self.analysis_text)
    
    def update_stats(self, stats):
        """Update memory statistics panel"""
        if not stats:
            return
            
        # Update session info
        self.session_id_label.setText(stats.get("session_id", "None"))
        
        # Format duration
        duration = stats.get("duration", 0)
        duration_text = f"{duration:.1f}s" if duration < 60 else f"{duration/60:.1f}m"
        self.duration_label.setText(duration_text)
        
        # Update counts
        self.inference_label.setText(str(stats.get("inference_count", 0)))
        self.token_label.setText(str(stats.get("token_count", 0)))
        
        # Update analysis text
        self.analysis_text.clear()
        
        # Check for memory leaks
        leaks = stats.get("potential_leaks", [])
        if leaks:
            self.analysis_text.insertHtml("<b style='color: #F44336;'>Potential Memory Leaks:</b><br>")
            for leak in leaks:
                gpu_id = leak.get("gpu_id", 0)
                severity = leak.get("severity", "unknown")
                growth_rate = leak.get("growth_rate", 0)
                
                color = "#F44336" if severity == "high" else "#FF9800" if severity == "medium" else "#FFC107"
                html = f"<p style='margin-left: 12px;'>GPU {gpu_id}: <span style='color: {color};'>{severity}</span> " \
                       f"leak detected (growth: {growth_rate:.2%}/min)</p>"
                self.analysis_text.insertHtml(html)
        
        # Check for memory spikes
        spikes = stats.get("allocation_spikes", [])
        if spikes:
            self.analysis_text.insertHtml("<br><b style='color: #FF9800;'>Memory Allocation Spikes:</b><br>")
            for spike in spikes:
                gpu_id = spike.get("gpu_id", 0)
                severity = spike.get("severity", "unknown")
                size_mb = spike.get("size_mb", 0)
                
                color = "#F44336" if severity == "high" else "#FF9800" if severity == "medium" else "#FFC107"
                html = f"<p style='margin-left: 12px;'>GPU {gpu_id}: <span style='color: {color};'>{severity}</span> " \
                       f"spike detected ({size_mb} MB)</p>"
                self.analysis_text.insertHtml(html)
        
        # If no issues found
        if not leaks and not spikes:
            self.analysis_text.insertHtml(
                "<p style='color: #4CAF50; text-align: center;'>No memory issues detected</p>"
            )


class MemoryProfilerPanel(QWidget):
    """Control panel for memory profiler"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        
        title_label = QLabel("Memory Profiler Controls")
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Inactive")
        self.status_label.setStyleSheet("color: #A0A0A0;")
        status_layout.addWidget(self.status_label)
        status_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addLayout(status_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Profiling")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton:hover {
                background-color: #66BB6A;
            }
        """)
        
        self.stop_button = QPushButton("Stop Profiling")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
            }
            QPushButton:hover {
                background-color: #EF5350;
            }
        """)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)
        
        # Inference tracking
        inference_layout = QHBoxLayout()
        
        self.inference_start_button = QPushButton("Start Inference")
        self.inference_start_button.setEnabled(False)
        
        self.inference_end_button = QPushButton("End Inference")
        self.inference_end_button.setEnabled(False)
        
        inference_layout.addWidget(self.inference_start_button)
        inference_layout.addWidget(self.inference_end_button)
        layout.addLayout(inference_layout)
        
        # Token count for inference
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("Tokens:"))
        
        self.token_input = QComboBox()
        self.token_input.setEditable(True)
        self.token_input.addItems(["256", "512", "1024", "2048", "4096"])
        self.token_input.setCurrentText("1024")
        
        token_layout.addWidget(self.token_input)
        layout.addLayout(token_layout)
        
        # Set up button connections
        self.start_button.clicked.connect(self.on_start_profiling)
        self.stop_button.clicked.connect(self.on_stop_profiling)
        self.inference_start_button.clicked.connect(self.on_start_inference)
        self.inference_end_button.clicked.connect(self.on_end_inference)
    
    def on_start_profiling(self):
        """Start profiling button clicked"""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.inference_start_button.setEnabled(True)
        self.inference_end_button.setEnabled(False)
        self.status_label.setText("Active")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
    
    def on_stop_profiling(self):
        """Stop profiling button clicked"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.inference_start_button.setEnabled(False)
        self.inference_end_button.setEnabled(False)
        self.status_label.setText("Inactive")
        self.status_label.setStyleSheet("color: #A0A0A0;")
    
    def on_start_inference(self):
        """Start inference tracking button clicked"""
        self.inference_start_button.setEnabled(False)
        self.inference_end_button.setEnabled(True)
        self.status_label.setText("Inference Active")
        self.status_label.setStyleSheet("color: #2196F3; font-weight: bold;")
    
    def on_end_inference(self):
        """End inference tracking button clicked"""
        self.inference_start_button.setEnabled(True)
        self.inference_end_button.setEnabled(False)
        self.status_label.setText("Active")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")


class MemoryProfilerTab(QWidget):
    """Memory profiler tab with visualization and controls"""
    
    def __init__(self, mock_mode=False):
        super().__init__()
        self.mock_mode = mock_mode
        self.logger = logging.getLogger('DualGPUOptimizer')
        self.logger.info("Initializing Memory Profiler tab")
        
        # Try to import the memory profiler
        try:
            from dualgpuopt.memory.profiler import MemoryProfiler
            self.profiler = MemoryProfiler()
            self.logger.info("Loaded memory profiler module")
        except ImportError:
            self.logger.warning("Memory profiler module not available, using mock implementation")
            self.profiler = MockMemoryProfiler()
        
        # Setup UI
        self.setup_ui()
        
        # Start update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_display)
        
        # Initialize state
        self.is_profiling = False
        self.is_inference = False
    
    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel("Memory Profiler")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        # Spacer
        header_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Mock mode indicator if enabled
        if self.mock_mode:
            mock_label = QLabel("MOCK MODE")
            mock_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            header_layout.addWidget(mock_label)
        
        main_layout.addLayout(header_layout)
        
        # Description label
        desc_label = QLabel("Monitor and analyze GPU memory usage patterns")
        desc_label.setStyleSheet("color: #A0A0A0;")
        main_layout.addWidget(desc_label)
        
        # Split into left and right panels
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        
        # Left panel with chart and stats
        left_panel = QVBoxLayout()
        
        # Memory chart
        self.memory_chart = MemoryChart()
        left_panel.addWidget(self.memory_chart)
        
        # Stats panel
        self.stats_panel = MemoryStatsPanel()
        left_panel.addWidget(self.stats_panel)
        
        # Add left panel to content
        content_layout.addLayout(left_panel, 7)  # 70% width
        
        # Right panel with controls and event log
        right_panel = QVBoxLayout()
        
        # Control panel
        self.control_panel = MemoryProfilerPanel()
        right_panel.addWidget(self.control_panel)
        
        # Event log
        self.event_log = EventLogView()
        right_panel.addWidget(self.event_log)
        
        # Add right panel to content
        content_layout.addLayout(right_panel, 3)  # 30% width
        
        # Add content layout to main layout
        main_layout.addLayout(content_layout)
        
        # Set up control connections
        self.control_panel.start_button.clicked.connect(self.start_profiling)
        self.control_panel.stop_button.clicked.connect(self.stop_profiling)
        self.control_panel.inference_start_button.clicked.connect(self.start_inference)
        self.control_panel.inference_end_button.clicked.connect(self.end_inference)
    
    def start_profiling(self):
        """Start memory profiling session"""
        if self.is_profiling:
            return
            
        self.logger.info("Starting memory profiling session")
        try:
            session_id = self.profiler.start_profiling()
            self.is_profiling = True
            
            # Update UI
            self.control_panel.on_start_profiling()
            
            # Start update timer
            self.update_timer.start(1000)  # Update every second
            
            self.logger.info(f"Memory profiling started with session: {session_id}")
        except Exception as e:
            self.logger.error(f"Failed to start memory profiling: {e}")
    
    def stop_profiling(self):
        """Stop memory profiling session"""
        if not self.is_profiling:
            return
            
        self.logger.info("Stopping memory profiling session")
        try:
            self.profiler.stop_profiling()
            self.is_profiling = False
            self.is_inference = False
            
            # Update UI
            self.control_panel.on_stop_profiling()
            
            # Stop update timer
            self.update_timer.stop()
            
            self.logger.info("Memory profiling stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop memory profiling: {e}")
    
    def start_inference(self):
        """Start inference tracking"""
        if not self.is_profiling or self.is_inference:
            return
            
        self.logger.info("Starting inference tracking")
        try:
            context = {"source": "MemoryProfilerTab"}
            success = self.profiler.start_inference(context)
            
            if success:
                self.is_inference = True
                self.control_panel.on_start_inference()
                self.logger.info("Inference tracking started")
            else:
                self.logger.warning("Failed to start inference tracking")
        except Exception as e:
            self.logger.error(f"Error starting inference tracking: {e}")
    
    def end_inference(self):
        """End inference tracking"""
        if not self.is_profiling or not self.is_inference:
            return
            
        self.logger.info("Ending inference tracking")
        try:
            # Get token count from input
            try:
                token_count = int(self.control_panel.token_input.currentText())
            except ValueError:
                token_count = 1024  # Default
            
            context = {"source": "MemoryProfilerTab"}
            success = self.profiler.end_inference(token_count, context)
            
            if success:
                self.is_inference = False
                self.control_panel.on_end_inference()
                self.logger.info(f"Inference tracking ended with {token_count} tokens")
            else:
                self.logger.warning("Failed to end inference tracking")
        except Exception as e:
            self.logger.error(f"Error ending inference tracking: {e}")
    
    def update_display(self):
        """Update all display components with current data"""
        if not self.is_profiling:
            return
            
        try:
            # Get timeline data for chart
            timeline_data = {}
            for gpu_id in range(2):  # Assuming max 2 GPUs for simplicity
                timeline_data[gpu_id] = self.profiler.get_memory_timeline(gpu_id)
            
            # Update memory chart
            self.memory_chart.update_data(timeline_data)
            
            # Get session stats
            stats = self.profiler.get_session_stats()
            self.stats_panel.update_stats(stats)
            
            # Get memory events
            events = self.profiler.get_memory_events()
            self.event_log.update_events(events)
        
        except Exception as e:
            self.logger.error(f"Error updating memory display: {e}")
    
    def closeEvent(self, event):
        """Handle tab close event"""
        # Stop profiling if active
        if self.is_profiling:
            self.stop_profiling()
        
        # Stop the update timer
        if self.update_timer and self.update_timer.isActive():
            self.update_timer.stop() 