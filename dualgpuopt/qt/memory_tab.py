import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
import threading
import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, 
    QPushButton, QSizePolicy, QSpacerItem, QComboBox, QTextEdit,
    QTabWidget, QCheckBox, QFileDialog, QInputDialog, QLineEdit, QProgressBar
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
        self.zoom_active = False
        self.zoom_start = None
        self.zoom_end = None
        self.filtered_data = {}
        self.markers = []
        self.show_markers = True
    
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
        
        # GPU selection and controls layout
        controls_layout = QHBoxLayout()
        
        # Add checkboxes for GPU selection
        self.gpu0_checkbox = QCheckBox("GPU 0")
        self.gpu0_checkbox.setChecked(True)
        self.gpu0_checkbox.toggled.connect(lambda checked: self.toggle_gpu(0, checked))
        
        self.gpu1_checkbox = QCheckBox("GPU 1")
        self.gpu1_checkbox.setChecked(True)
        self.gpu1_checkbox.toggled.connect(lambda checked: self.toggle_gpu(1, checked))
        
        controls_layout.addWidget(self.gpu0_checkbox)
        controls_layout.addWidget(self.gpu1_checkbox)
        
        # Markers toggle
        self.markers_checkbox = QCheckBox("Show Markers")
        self.markers_checkbox.setChecked(True)
        self.markers_checkbox.toggled.connect(self.toggle_markers)
        controls_layout.addWidget(self.markers_checkbox)
        
        controls_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Add zoom control buttons
        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.reset_zoom_button = QPushButton("Reset")
        self.reset_zoom_button.clicked.connect(self.reset_zoom)
        
        controls_layout.addWidget(self.zoom_in_button)
        controls_layout.addWidget(self.zoom_out_button)
        controls_layout.addWidget(self.reset_zoom_button)
        
        # Export button
        self.export_button = QPushButton("Export Data")
        self.export_button.clicked.connect(self.export_data)
        controls_layout.addWidget(self.export_button)
        
        self.layout.addLayout(controls_layout)
        
        # Add filter control
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Data", "all")
        self.filter_combo.addItem("Last 5 Minutes", 300)
        self.filter_combo.addItem("Last 1 Minute", 60)
        self.filter_combo.addItem("Last 30 Seconds", 30)
        self.filter_combo.currentIndexChanged.connect(self.apply_filter)
        
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Add marker button
        self.add_marker_button = QPushButton("Add Marker")
        self.add_marker_button.clicked.connect(self.add_marker)
        filter_layout.addWidget(self.add_marker_button)
        
        self.layout.addLayout(filter_layout)
        
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
            
            # Connect mouse events for interactive zooming
            self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
            self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
            self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
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
    
    def toggle_markers(self, show):
        """Toggle visibility of markers in the chart"""
        self.show_markers = show
        self.update_chart()
    
    def update_data(self, timeline_data):
        """Update chart with new timeline data"""
        self.timeline_data = timeline_data
        # Initialize filtered data with the complete dataset
        self.filtered_data = self.timeline_data.copy()
        self.update_chart()
    
    def apply_filter(self):
        """Apply time filter to the data"""
        filter_value = self.filter_combo.currentData()
        
        if filter_value == "all":
            # Show all data
            self.filtered_data = self.timeline_data.copy()
        else:
            # Filter by time (last N seconds)
            filter_seconds = int(filter_value)
            current_time = time.time()
            cut_off = current_time - filter_seconds
            
            self.filtered_data = {}
            for gpu_id, data in self.timeline_data.items():
                self.filtered_data[gpu_id] = [point for point in data if point[0] >= cut_off]
        
        self.update_chart()
    
    def update_chart(self):
        """Redraw the chart with current data"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        # Clear the axes
        self.axes.clear()
        
        # Draw each visible GPU's data
        for gpu_id, visible in self.show_gpu.items():
            if not visible or gpu_id not in self.filtered_data:
                continue
                
            data = self.filtered_data[gpu_id]
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
        
        # Add markers if enabled
        if self.show_markers and self.markers:
            for marker in self.markers:
                # Find relative position for marker
                if marker['time'] >= min([point[0] for gpu_data in self.filtered_data.values() for point in gpu_data], default=0):
                    rel_time = marker['time'] - min([point[0] for gpu_data in self.filtered_data.values() for point in gpu_data], default=0)
                    # Draw vertical line for marker
                    self.axes.axvline(x=rel_time, color=marker['color'], linestyle='--', alpha=0.7)
                    # Add label
                    ymin, ymax = self.axes.get_ylim()
                    text_y = ymax * 0.95
                    self.axes.text(rel_time, text_y, marker['label'], color=marker['color'], 
                                  rotation=90, verticalalignment='top', weight='bold')
        
        # Apply zoom if active
        if self.zoom_active and self.zoom_start is not None and self.zoom_end is not None:
            self.axes.set_xlim(self.zoom_start, self.zoom_end)
        
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
    
    def zoom_in(self):
        """Zoom in on the current view"""
        if not MATPLOTLIB_AVAILABLE or not self.axes:
            return
            
        xlim = self.axes.get_xlim()
        center = sum(xlim) / 2
        width = xlim[1] - xlim[0]
        new_width = width * 0.6  # Zoom in by reducing width to 60%
        
        self.zoom_active = True
        self.zoom_start = center - new_width/2
        self.zoom_end = center + new_width/2
        self.update_chart()
    
    def zoom_out(self):
        """Zoom out from the current view"""
        if not MATPLOTLIB_AVAILABLE or not self.axes:
            return
            
        xlim = self.axes.get_xlim()
        center = sum(xlim) / 2
        width = xlim[1] - xlim[0]
        new_width = width * 1.6  # Zoom out by increasing width to 160%
        
        self.zoom_active = True
        self.zoom_start = center - new_width/2
        self.zoom_end = center + new_width/2
        self.update_chart()
    
    def reset_zoom(self):
        """Reset zoom to show all data"""
        self.zoom_active = False
        self.zoom_start = None
        self.zoom_end = None
        self.update_chart()
    
    def on_mouse_press(self, event):
        """Handle mouse press for interactive zoom"""
        if not event.inaxes:
            return
        
        # Start zoom selection
        self.zoom_rect_start = (event.xdata, event.ydata)
    
    def on_mouse_move(self, event):
        """Handle mouse movement for interactive zoom"""
        pass  # This will be used for drawing zoom rectangle in future enhancement
    
    def on_mouse_release(self, event):
        """Handle mouse release for interactive zoom"""
        if not event.inaxes or not hasattr(self, 'zoom_rect_start'):
            return
        
        # Complete zoom selection
        zoom_rect_end = (event.xdata, event.ydata)
        
        # Check if it's a valid zoom area (some minimum width)
        if abs(zoom_rect_end[0] - self.zoom_rect_start[0]) > 1.0:
            self.zoom_active = True
            self.zoom_start = min(self.zoom_rect_start[0], zoom_rect_end[0])
            self.zoom_end = max(self.zoom_rect_start[0], zoom_rect_end[0])
            self.update_chart()
        
        # Clear the temp stored values
        delattr(self, 'zoom_rect_start')
    
    def add_marker(self):
        """Add a marker at the current time"""
        # Generate marker with current time
        current_time = time.time()
        
        # Create marker label dialog
        marker_label, ok = QInputDialog.getText(self, "Add Timeline Marker", 
                                               "Enter marker label:", 
                                               QLineEdit.Normal, 
                                               f"Marker {len(self.markers) + 1}")
        
        if ok and marker_label:
            # Add the marker
            marker = {
                'time': current_time,
                'label': marker_label,
                'color': '#FF9800',  # Orange
                'description': f"Manual marker added at {datetime.datetime.now().strftime('%H:%M:%S')}"
            }
            
            self.markers.append(marker)
            logger.info(f"Added timeline marker: {marker_label}")
            
            # Update chart to show new marker
            self.update_chart()
    
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
                    for gpu_id, data in self.filtered_data.items():
                        for point in data:
                            if len(point) >= 2:
                                timestamp = point[0]
                                memory_mb = point[1]
                                f.write(f"{timestamp},{gpu_id},{memory_mb}\n")
                
                logger.info(f"Exported memory timeline to {file_name}")
            except Exception as e:
                logger.error(f"Error exporting timeline data: {e}")
                
    def export_chart_image(self):
        """Export chart as image"""
        if not MATPLOTLIB_AVAILABLE:
            logger.error("Matplotlib not available for image export")
            return
            
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Export Chart Image", "", "PNG Files (*.png);;PDF Files (*.pdf);;All Files (*)",
            options=options
        )
        
        if file_name:
            try:
                self.figure.savefig(file_name, facecolor=self.figure.get_facecolor())
                logger.info(f"Exported chart image to {file_name}")
            except Exception as e:
                logger.error(f"Error exporting chart image: {e}")


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
        self.stats = {}
        self.patterns = []
    
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
        
        # Create tab widget for different analysis views
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3D2A50;
                background-color: #2D1E40;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #241934;
                color: #FFFFFF;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3D2A50;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.tab_widget)
        
        # Create Overview Tab
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        
        # Add title
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        
        title_label = QLabel("Memory Analysis")
        title_label.setFont(title_font)
        overview_layout.addWidget(title_label)
        
        # Session info grid
        info_grid = QGridLayout()
        info_grid.setColumnStretch(1, 1)
        overview_layout.addLayout(info_grid)
        
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
        
        # Memory efficiency
        info_grid.addWidget(QLabel("Mem Efficiency:"), 4, 0)
        self.efficiency_label = QLabel("N/A")
        info_grid.addWidget(self.efficiency_label, 4, 1)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #3D2A50;")
        overview_layout.addWidget(separator)
        
        # Analysis Title
        analysis_title = QLabel("Memory Issues")
        analysis_title.setFont(title_font)
        overview_layout.addWidget(analysis_title)
        
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
        overview_layout.addWidget(self.analysis_text)
        
        # Add to tab widget
        self.tab_widget.addTab(overview_widget, "Overview")
        
        # Create Pattern Analysis Tab
        pattern_widget = QWidget()
        pattern_layout = QVBoxLayout(pattern_widget)
        
        # Pattern analysis title
        pattern_title = QLabel("Memory Pattern Analysis")
        pattern_title.setFont(title_font)
        pattern_layout.addWidget(pattern_title)
        
        # Pattern description
        pattern_desc = QLabel("Detected memory usage patterns and anomalies")
        pattern_desc.setStyleSheet("color: #A0A0A0;")
        pattern_layout.addWidget(pattern_desc)
        
        # Pattern list
        self.pattern_list = QTextEdit()
        self.pattern_list.setReadOnly(True)
        self.pattern_list.setStyleSheet("""
            QTextEdit {
                background-color: #241934;
                color: #FFFFFF;
                border-radius: 4px;
                border: 1px solid #3D2A50;
                padding: 8px;
            }
        """)
        pattern_layout.addWidget(self.pattern_list)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.analyze_button = QPushButton("Run Deep Analysis")
        self.analyze_button.clicked.connect(self.run_deep_analysis)
        action_layout.addWidget(self.analyze_button)
        
        self.clear_button = QPushButton("Clear Analysis")
        self.clear_button.clicked.connect(self.clear_analysis)
        action_layout.addWidget(self.clear_button)
        
        pattern_layout.addLayout(action_layout)
        
        # Add to tab widget
        self.tab_widget.addTab(pattern_widget, "Pattern Analysis")
        
        # Create GPU Comparison Tab
        comparison_widget = QWidget()
        comparison_layout = QVBoxLayout(comparison_widget)
        
        # Comparison title
        comparison_title = QLabel("GPU Memory Comparison")
        comparison_title.setFont(title_font)
        comparison_layout.addWidget(comparison_title)
        
        # Statistics grid for GPU comparison
        gpu_grid = QGridLayout()
        gpu_grid.setColumnStretch(1, 1)
        gpu_grid.setColumnStretch(2, 1)
        
        # Headers
        gpu_grid.addWidget(QLabel("Metric"), 0, 0)
        gpu_grid.addWidget(QLabel("GPU 0"), 0, 1)
        gpu_grid.addWidget(QLabel("GPU 1"), 0, 2)
        
        # Peak memory
        gpu_grid.addWidget(QLabel("Peak Memory:"), 1, 0)
        self.peak_gpu0 = QLabel("0 MB")
        self.peak_gpu1 = QLabel("0 MB")
        gpu_grid.addWidget(self.peak_gpu0, 1, 1)
        gpu_grid.addWidget(self.peak_gpu1, 1, 2)
        
        # Average memory
        gpu_grid.addWidget(QLabel("Avg Memory:"), 2, 0)
        self.avg_gpu0 = QLabel("0 MB")
        self.avg_gpu1 = QLabel("0 MB")
        gpu_grid.addWidget(self.avg_gpu0, 2, 1)
        gpu_grid.addWidget(self.avg_gpu1, 2, 2)
        
        # Growth rate
        gpu_grid.addWidget(QLabel("Growth Rate:"), 3, 0)
        self.growth_gpu0 = QLabel("0 MB/min")
        self.growth_gpu1 = QLabel("0 MB/min")
        gpu_grid.addWidget(self.growth_gpu0, 3, 1)
        gpu_grid.addWidget(self.growth_gpu1, 3, 2)
        
        # Spike count
        gpu_grid.addWidget(QLabel("Spike Count:"), 4, 0)
        self.spikes_gpu0 = QLabel("0")
        self.spikes_gpu1 = QLabel("0")
        gpu_grid.addWidget(self.spikes_gpu0, 4, 1)
        gpu_grid.addWidget(self.spikes_gpu1, 4, 2)
        
        comparison_layout.addLayout(gpu_grid)
        
        # Usage efficiency visualization
        vis_frame = QFrame()
        vis_frame.setFrameShape(QFrame.StyledPanel)
        vis_frame.setStyleSheet("background-color: #241934; border-radius: 4px; padding: 12px;")
        vis_layout = QVBoxLayout(vis_frame)
        
        vis_title = QLabel("Memory Utilization Efficiency")
        vis_title.setFont(title_font)
        vis_layout.addWidget(vis_title)
        
        # GPU 0 efficiency
        vis_layout.addWidget(QLabel("GPU 0 Efficiency:"))
        self.eff_bar0 = QProgressBar()
        self.eff_bar0.setFixedHeight(16)
        self.eff_bar0.setRange(0, 100)
        self.eff_bar0.setValue(0)
        self.eff_bar0.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3D2A50;
                border-radius: 4px;
                background-color: #241934;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #8A54FD;
                border-radius: 3px;
            }
        """)
        vis_layout.addWidget(self.eff_bar0)
        
        # GPU 1 efficiency
        vis_layout.addWidget(QLabel("GPU 1 Efficiency:"))
        self.eff_bar1 = QProgressBar()
        self.eff_bar1.setFixedHeight(16)
        self.eff_bar1.setRange(0, 100)
        self.eff_bar1.setValue(0)
        self.eff_bar1.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3D2A50;
                border-radius: 4px;
                background-color: #241934;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        vis_layout.addWidget(self.eff_bar1)
        
        comparison_layout.addWidget(vis_frame)
        
        # Add to tab widget
        self.tab_widget.addTab(comparison_widget, "GPU Comparison")
    
    def update_stats(self, stats):
        """Update memory statistics panel"""
        if not stats:
            return
            
        # Store stats for later analysis
        self.stats = stats
            
        # Update session info
        self.session_id_label.setText(stats.get("session_id", "None"))
        
        # Format duration
        duration = stats.get("duration", 0)
        duration_text = f"{duration:.1f}s" if duration < 60 else f"{duration/60:.1f}m"
        self.duration_label.setText(duration_text)
        
        # Update counts
        self.inference_label.setText(str(stats.get("inference_count", 0)))
        self.token_label.setText(str(stats.get("token_count", 0)))
        
        # Memory efficiency calculation
        token_count = stats.get("token_count", 0)
        total_peak_memory = sum(stats.get("peak_memory", {0: 0, 1: 0}).values())
        if token_count > 0 and total_peak_memory > 0:
            efficiency = token_count / (total_peak_memory / 1024)  # tokens per GB
            self.efficiency_label.setText(f"{efficiency:.2f} tokens/GB")
        else:
            self.efficiency_label.setText("N/A")
        
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
        
        # Update GPU comparison tab
        peak_memory = stats.get("peak_memory", {})
        self.peak_gpu0.setText(f"{peak_memory.get(0, 0)} MB")
        self.peak_gpu1.setText(f"{peak_memory.get(1, 0)} MB")
        
        avg_memory = stats.get("avg_memory", {})
        self.avg_gpu0.setText(f"{avg_memory.get(0, 0)} MB")
        self.avg_gpu1.setText(f"{avg_memory.get(1, 0)} MB")
        
        # Update growth rates
        for leak in leaks:
            if leak.get("gpu_id") == 0:
                self.growth_gpu0.setText(f"{leak.get('growth_rate', 0)*100:.2f}%/min")
            elif leak.get("gpu_id") == 1:
                self.growth_gpu1.setText(f"{leak.get('growth_rate', 0)*100:.2f}%/min")
        
        # Count spikes per GPU
        spike_count = {0: 0, 1: 0}
        for spike in spikes:
            gpu_id = spike.get("gpu_id", 0)
            spike_count[gpu_id] = spike_count.get(gpu_id, 0) + 1
        
        self.spikes_gpu0.setText(str(spike_count.get(0, 0)))
        self.spikes_gpu1.setText(str(spike_count.get(1, 0)))
        
        # Update efficiency bars
        # Simple efficiency metric: lower is better (less memory per token)
        if token_count > 0:
            if peak_memory.get(0, 0) > 0:
                eff0 = min(100, (token_count / peak_memory.get(0, 1)) * 10)  # Scale for visual effect
                self.eff_bar0.setValue(int(eff0))
            
            if peak_memory.get(1, 0) > 0:
                eff1 = min(100, (token_count / peak_memory.get(1, 1)) * 10)  # Scale for visual effect
                self.eff_bar1.setValue(int(eff1))
    
    def run_deep_analysis(self):
        """Run deeper analysis on memory patterns"""
        if not self.stats:
            logger.warning("No memory stats available for deep analysis")
            return
        
        try:
            # Clear previous analysis
            self.pattern_list.clear()
            self.patterns = []
            
            # Get peak memory values
            peak_memory = self.stats.get("peak_memory", {})
            avg_memory = self.stats.get("avg_memory", {})
            duration = self.stats.get("duration", 0)
            inference_count = self.stats.get("inference_count", 0)
            
            # Analyze memory usage patterns
            self.pattern_list.insertHtml("<b>Memory Usage Pattern Analysis:</b><br><br>")
            
            # Check imbalance between GPUs
            if 0 in peak_memory and 1 in peak_memory and peak_memory[0] > 0 and peak_memory[1] > 0:
                ratio = peak_memory[0] / peak_memory[1]
                if ratio > 2 or ratio < 0.5:
                    # Significant imbalance
                    self.patterns.append({
                        "type": "imbalance",
                        "description": f"GPU memory usage is imbalanced (ratio: {ratio:.2f})",
                        "severity": "high" if (ratio > 3 or ratio < 0.33) else "medium",
                        "recommendation": "Consider redistributing model layers or using tensor parallelism"
                    })
                    
                    color = "#F44336" if ratio > 3 or ratio < 0.33 else "#FF9800"
                    html = f"<p style='margin-bottom: 10px;'><span style='color: {color};'>Memory Imbalance:</span> " \
                           f"GPU memory usage ratio is {ratio:.2f}x between GPUs<br>" \
                           f"<span style='color: #A0A0A0; margin-left: 15px;'>Recommendation: Adjust layer distribution</span></p>"
                    self.pattern_list.insertHtml(html)
            
            # Check for steady growth pattern
            leaks = self.stats.get("potential_leaks", [])
            if leaks:
                for leak in leaks:
                    gpu_id = leak.get("gpu_id", 0)
                    growth_rate = leak.get("growth_rate", 0)
                    severity = leak.get("severity", "medium")
                    
                    self.patterns.append({
                        "type": "growth",
                        "gpu_id": gpu_id,
                        "growth_rate": growth_rate,
                        "severity": severity,
                        "description": f"Steady memory growth detected on GPU {gpu_id}",
                        "recommendation": "Look for resource leaks in model implementation"
                    })
                    
                    color = "#F44336" if severity == "high" else "#FF9800"
                    html = f"<p style='margin-bottom: 10px;'><span style='color: {color};'>Memory Growth:</span> " \
                           f"GPU {gpu_id} shows sustained growth of {growth_rate*100:.2f}%/min<br>" \
                           f"<span style='color: #A0A0A0; margin-left: 15px;'>Recommendation: Check for resource leaks</span></p>"
                    self.pattern_list.insertHtml(html)
            
            # Check for inefficient memory usage
            if inference_count > 0:
                for gpu_id in [0, 1]:
                    if gpu_id in peak_memory and peak_memory[gpu_id] > 0:
                        mb_per_inference = peak_memory[gpu_id] / inference_count
                        if mb_per_inference > 5000:  # Arbitrary threshold for demonstration
                            self.patterns.append({
                                "type": "inefficiency",
                                "gpu_id": gpu_id,
                                "mb_per_inference": mb_per_inference,
                                "severity": "medium",
                                "description": f"High memory usage per inference on GPU {gpu_id}",
                                "recommendation": "Consider quantization or efficient attention mechanisms"
                            })
                            
                            html = f"<p style='margin-bottom: 10px;'><span style='color: #FF9800;'>Memory Inefficiency:</span> " \
                                   f"GPU {gpu_id} uses {mb_per_inference:.1f} MB per inference<br>" \
                                   f"<span style='color: #A0A0A0; margin-left: 15px;'>Recommendation: Consider quantization</span></p>"
                            self.pattern_list.insertHtml(html)
            
            # Check for memory fragmentation signs
            spikes = self.stats.get("allocation_spikes", [])
            if spikes:
                spike_count = {0: 0, 1: 0}
                for spike in spikes:
                    gpu_id = spike.get("gpu_id", 0)
                    spike_count[gpu_id] = spike_count.get(gpu_id, 0) + 1
                
                for gpu_id, count in spike_count.items():
                    if count >= 3:  # Multiple spikes might indicate fragmentation
                        self.patterns.append({
                            "type": "fragmentation",
                            "gpu_id": gpu_id,
                            "spike_count": count,
                            "severity": "medium" if count >= 5 else "low",
                            "description": f"Possible memory fragmentation on GPU {gpu_id}",
                            "recommendation": "Consider implementing memory defragmentation"
                        })
                        
                        color = "#FF9800" if count >= 5 else "#FFC107"
                        html = f"<p style='margin-bottom: 10px;'><span style='color: {color};'>Possible Fragmentation:</span> " \
                               f"GPU {gpu_id} had {count} memory spikes during session<br>" \
                               f"<span style='color: #A0A0A0; margin-left: 15px;'>Recommendation: Implement defragmentation</span></p>"
                        self.pattern_list.insertHtml(html)
            
            # If no patterns found
            if not self.patterns:
                self.pattern_list.insertHtml(
                    "<p style='color: #4CAF50; text-align: center;'>No significant memory patterns detected</p>"
                )
            
            # Add summary and recommendations
            if self.patterns:
                self.pattern_list.insertHtml("<br><b>Summary Recommendations:</b><br>")
                
                # Group recommendations by severity
                high_severity = [p for p in self.patterns if p.get("severity") == "high"]
                med_severity = [p for p in self.patterns if p.get("severity") == "medium"]
                
                if high_severity:
                    self.pattern_list.insertHtml("<p style='color: #F44336;'>High Priority:</p><ul>")
                    for pattern in high_severity:
                        self.pattern_list.insertHtml(f"<li>{pattern.get('recommendation')}</li>")
                    self.pattern_list.insertHtml("</ul>")
                
                if med_severity:
                    self.pattern_list.insertHtml("<p style='color: #FF9800;'>Medium Priority:</p><ul>")
                    for pattern in med_severity:
                        self.pattern_list.insertHtml(f"<li>{pattern.get('recommendation')}</li>")
                    self.pattern_list.insertHtml("</ul>")
            
            logger.info(f"Completed deep pattern analysis: {len(self.patterns)} patterns found")
            
            # Switch to pattern analysis tab
            self.tab_widget.setCurrentIndex(1)
            
        except Exception as e:
            logger.error(f"Error in memory pattern analysis: {e}")
            self.pattern_list.clear()
            self.pattern_list.insertHtml(f"<p style='color: #F44336;'>Error during analysis: {str(e)}</p>")
    
    def clear_analysis(self):
        """Clear pattern analysis results"""
        self.pattern_list.clear()
        self.patterns = []
        logger.info("Cleared memory pattern analysis")


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