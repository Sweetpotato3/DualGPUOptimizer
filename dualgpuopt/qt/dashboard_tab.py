import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QProgressBar, QFrame, QGridLayout, QSizePolicy,
                              QPushButton, QSpacerItem, QComboBox)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QFont, QIcon, QColor
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
import datetime
import collections

logger = logging.getLogger('DualGPUOptimizer')

# Define maximum history length for metrics
MAX_HISTORY_LENGTH = 60  # 60 data points (1 minute at 1s polling)

class GPUChart(QFrame):
    """Line chart showing historical GPU metrics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.metric_histories = {}
        self.current_metric = "memory"
        self.series = {}
        
    def setup_ui(self):
        # Set up chart frame styling
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            GPUChart {
                background-color: #241934;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # Header with title and metric selector
        header_layout = QHBoxLayout()
        
        # Chart title
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        
        self.title_label = QLabel("GPU History")
        self.title_label.setFont(title_font)
        header_layout.addWidget(self.title_label)
        
        # Spacer to push selector to right
        header_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Metric selector
        self.metric_selector = QComboBox()
        self.metric_selector.addItem("Memory Usage", "memory")
        self.metric_selector.addItem("GPU Utilization", "utilization")
        self.metric_selector.addItem("Temperature", "temperature")
        self.metric_selector.addItem("Power", "power")
        self.metric_selector.currentIndexChanged.connect(self.change_metric)
        header_layout.addWidget(self.metric_selector)
        
        main_layout.addLayout(header_layout)
        
        # Create the chart
        self.chart = QChart()
        self.chart.setTitle("")
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)
        
        # Configure chart appearance for dark theme
        self.chart.setBackgroundBrush(QColor("#241934"))
        self.chart.setTitleBrush(QColor("#FFFFFF"))
        self.chart.legend().setLabelBrush(QColor("#CCCCCC"))
        
        # Create axis
        self.axis_x = QValueAxis()
        self.axis_x.setRange(0, MAX_HISTORY_LENGTH)
        self.axis_x.setLabelFormat("%d")
        self.axis_x.setLabelsVisible(False)
        self.axis_x.setGridLineVisible(True)
        self.axis_x.setGridLineColor(QColor("#3D2A50"))
        self.axis_x.setLabelsColor(QColor("#CCCCCC"))
        
        self.axis_y = QValueAxis()
        self.axis_y.setRange(0, 100)
        self.axis_y.setLabelFormat("%.0f")
        self.axis_y.setGridLineVisible(True)
        self.axis_y.setGridLineColor(QColor("#3D2A50"))
        self.axis_y.setLabelsColor(QColor("#CCCCCC"))
        
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        
        # Create chart view
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(self.chart_view.RenderHint.Antialiasing)
        self.chart_view.setBackgroundBrush(QColor("#241934"))
        
        main_layout.addWidget(self.chart_view)
        
        # Initialize empty series for each GPU (we'll create series on first update)
        self.gpu_colors = [QColor("#8A54FD"), QColor("#4CAF50")]
        
    def init_series_for_gpus(self, gpu_count):
        """Initialize line series for each GPU"""
        # Clear any existing series
        self.chart.removeAllSeries()
        self.series = {}
        
        for gpu_id in range(gpu_count):
            # Create a new series for this GPU
            series = QLineSeries()
            series.setName(f"GPU {gpu_id}")
            series.setPen(self.gpu_colors[gpu_id % len(self.gpu_colors)])
            
            # Add to chart and connect to axes
            self.chart.addSeries(series)
            series.attachAxis(self.axis_x)
            series.attachAxis(self.axis_y)
            
            # Store in our series dict
            self.series[gpu_id] = series
            
            # Initialize history for this GPU if not exists
            if gpu_id not in self.metric_histories:
                self.metric_histories[gpu_id] = {
                    "memory": collections.deque(maxlen=MAX_HISTORY_LENGTH),
                    "utilization": collections.deque(maxlen=MAX_HISTORY_LENGTH),
                    "temperature": collections.deque(maxlen=MAX_HISTORY_LENGTH),
                    "power": collections.deque(maxlen=MAX_HISTORY_LENGTH)
                }
    
    def update_metrics(self, metrics_list):
        """Update chart with new metrics data"""
        # Initialize series if this is the first update
        if not self.series or len(self.series) != len(metrics_list):
            self.init_series_for_gpus(len(metrics_list))
        
        # Update metric histories
        for i, metrics in enumerate(metrics_list):
            if i in self.metric_histories:
                # Extract values based on current metric
                if self.current_metric == "memory" and "memory_total" in metrics and metrics["memory_total"] > 0:
                    value = (metrics.get("memory_used", 0) / metrics["memory_total"]) * 100
                    self.metric_histories[i]["memory"].append(value)
                elif self.current_metric == "utilization":
                    value = metrics.get("utilization", 0)
                    self.metric_histories[i]["utilization"].append(value)
                elif self.current_metric == "temperature":
                    value = metrics.get("temperature", 0)
                    self.metric_histories[i]["temperature"].append(value)
                elif self.current_metric == "power" and "power_limit" in metrics and metrics["power_limit"] > 0:
                    value = (metrics.get("power", 0) / metrics["power_limit"]) * 100
                    self.metric_histories[i]["power"].append(value)
        
        # Update chart
        self.refresh_chart()
    
    def refresh_chart(self):
        """Refresh the chart with current data"""
        # Get y-axis range based on metric
        if self.current_metric == "temperature":
            self.axis_y.setRange(0, 100)
            self.axis_y.setTitleText("Temperature (°C)")
        elif self.current_metric in ["memory", "utilization", "power"]:
            self.axis_y.setRange(0, 100)
            self.axis_y.setTitleText("Percentage (%)")
        
        # Update each series
        for gpu_id, series in self.series.items():
            # Skip if no history for this GPU
            if gpu_id not in self.metric_histories:
                continue
                
            # Get history for current metric
            history = self.metric_histories[gpu_id][self.current_metric]
            
            # Clear the series
            series.clear()
            
            # Add points
            for i, value in enumerate(history):
                series.append(i, value)
    
    def change_metric(self, index):
        """Change the displayed metric"""
        self.current_metric = self.metric_selector.currentData()
        self.refresh_chart()


class GPUCard(QFrame):
    """Individual GPU card widget showing metrics for a single GPU."""
    
    # Signal for reset memory button
    reset_clicked = Signal(int)  # GPU index
    
    def __init__(self, gpu_index, parent=None):
        super().__init__(parent)
        self.gpu_index = gpu_index
        self.setup_ui()
    
    def setup_ui(self):
        # Set up card styling with shadows
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            GPUCard {
                background-color: #372952;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # GPU title layout
        title_layout = QHBoxLayout()
        
        # Title with larger font
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        
        self.title_label = QLabel(f"GPU {self.gpu_index}")
        self.title_label.setFont(title_font)
        title_layout.addWidget(self.title_label)
        
        # Spacer to push reset button to right
        title_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Reset button
        self.reset_button = QPushButton("Reset Memory")
        self.reset_button.setToolTip("Reset GPU memory (requires PyTorch)")
        self.reset_button.clicked.connect(lambda: self.reset_clicked.emit(self.gpu_index))
        title_layout.addWidget(self.reset_button)
        
        main_layout.addLayout(title_layout)
        
        # Add GPU name label
        self.name_label = QLabel("Unknown GPU")
        self.name_label.setStyleSheet("color: #A0A0A0;")
        main_layout.addWidget(self.name_label)
        
        # Metrics grid
        metrics_layout = QGridLayout()
        metrics_layout.setColumnStretch(1, 1)  # Make progress bars expand
        metrics_layout.setVerticalSpacing(10)
        metrics_layout.setHorizontalSpacing(8)
        main_layout.addLayout(metrics_layout)
        
        # Memory
        metrics_layout.addWidget(QLabel("Memory:"), 0, 0)
        self.memory_bar = QProgressBar()
        self.memory_bar.setFixedHeight(16)
        self.memory_bar.setStyleSheet("""
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
        metrics_layout.addWidget(self.memory_bar, 0, 1)
        self.memory_label = QLabel("0MB / 0MB")
        metrics_layout.addWidget(self.memory_label, 0, 2)
        
        # Utilization
        metrics_layout.addWidget(QLabel("Utilization:"), 1, 0)
        self.util_bar = QProgressBar()
        self.util_bar.setFixedHeight(16)
        self.util_bar.setStyleSheet("""
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
        metrics_layout.addWidget(self.util_bar, 1, 1)
        self.util_label = QLabel("0%")
        metrics_layout.addWidget(self.util_label, 1, 2)
        
        # Temperature
        metrics_layout.addWidget(QLabel("Temperature:"), 2, 0)
        self.temp_bar = QProgressBar()
        self.temp_bar.setFixedHeight(16)
        self.temp_bar.setStyleSheet("""
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
        metrics_layout.addWidget(self.temp_bar, 2, 1)
        self.temp_label = QLabel("0°C")
        metrics_layout.addWidget(self.temp_label, 2, 2)
        
        # Power
        metrics_layout.addWidget(QLabel("Power:"), 3, 0)
        self.power_bar = QProgressBar()
        self.power_bar.setFixedHeight(16)
        self.power_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3D2A50;
                border-radius: 4px;
                background-color: #241934;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #F44336;
                border-radius: 3px;
            }
        """)
        metrics_layout.addWidget(self.power_bar, 3, 1)
        self.power_label = QLabel("0W / 0W")
        metrics_layout.addWidget(self.power_label, 3, 2)
        
        # Clock speeds
        metrics_layout.addWidget(QLabel("SM Clock:"), 4, 0)
        self.sm_clock_label = QLabel("0 MHz")
        metrics_layout.addWidget(self.sm_clock_label, 4, 1, 1, 2)
        
        metrics_layout.addWidget(QLabel("Memory Clock:"), 5, 0)
        self.mem_clock_label = QLabel("0 MHz")
        metrics_layout.addWidget(self.mem_clock_label, 5, 1, 1, 2)
    
    def update_metrics(self, metrics):
        """Update all GPU metrics with new data."""
        # Update title with GPU name if available
        if "name" in metrics and metrics["name"]:
            self.name_label.setText(metrics["name"])
        
        # Memory metrics
        mem_used = metrics.get("memory_used", 0)
        mem_total = metrics.get("memory_total", 1)
        self.memory_bar.setMaximum(mem_total)
        self.memory_bar.setValue(mem_used)
        self.memory_label.setText(f"{mem_used} MB / {mem_total} MB")
        
        # Set color based on memory usage percentage
        memory_percent = (mem_used / mem_total) * 100 if mem_total > 0 else 0
        if memory_percent > 90:
            self.memory_bar.setStyleSheet("""
                QProgressBar { border: 1px solid #3D2A50; border-radius: 4px; background-color: #241934; }
                QProgressBar::chunk { background-color: #F44336; border-radius: 3px; }
            """)
        elif memory_percent > 75:
            self.memory_bar.setStyleSheet("""
                QProgressBar { border: 1px solid #3D2A50; border-radius: 4px; background-color: #241934; }
                QProgressBar::chunk { background-color: #FF9800; border-radius: 3px; }
            """)
        else:
            self.memory_bar.setStyleSheet("""
                QProgressBar { border: 1px solid #3D2A50; border-radius: 4px; background-color: #241934; }
                QProgressBar::chunk { background-color: #8A54FD; border-radius: 3px; }
            """)
        
        # Utilization
        util = metrics.get("utilization", 0)
        self.util_bar.setMaximum(100)
        self.util_bar.setValue(util)
        self.util_label.setText(f"{util}%")
        
        # Temperature
        temp = metrics.get("temperature", 0)
        self.temp_bar.setMaximum(100)
        self.temp_bar.setValue(temp)
        self.temp_label.setText(f"{temp}°C")
        
        # Set color based on temperature
        if temp > 80:
            self.temp_bar.setStyleSheet("""
                QProgressBar { border: 1px solid #3D2A50; border-radius: 4px; background-color: #241934; }
                QProgressBar::chunk { background-color: #F44336; border-radius: 3px; }
            """)
        elif temp > 70:
            self.temp_bar.setStyleSheet("""
                QProgressBar { border: 1px solid #3D2A50; border-radius: 4px; background-color: #241934; }
                QProgressBar::chunk { background-color: #FF9800; border-radius: 3px; }
            """)
        else:
            self.temp_bar.setStyleSheet("""
                QProgressBar { border: 1px solid #3D2A50; border-radius: 4px; background-color: #241934; }
                QProgressBar::chunk { background-color: #4CAF50; border-radius: 3px; }
            """)
        
        # Power
        power = metrics.get("power", 0)
        power_limit = metrics.get("power_limit", 1)
        if power_limit > 0:
            self.power_bar.setMaximum(power_limit)
            self.power_bar.setValue(power)
            self.power_label.setText(f"{power}W / {power_limit}W")
            
            # Set color based on power percentage
            power_percent = (power / power_limit) * 100 if power_limit > 0 else 0
            if power_percent > 90:
                self.power_bar.setStyleSheet("""
                    QProgressBar { border: 1px solid #3D2A50; border-radius: 4px; background-color: #241934; }
                    QProgressBar::chunk { background-color: #F44336; border-radius: 3px; }
                """)
            elif power_percent > 75:
                self.power_bar.setStyleSheet("""
                    QProgressBar { border: 1px solid #3D2A50; border-radius: 4px; background-color: #241934; }
                    QProgressBar::chunk { background-color: #FF9800; border-radius: 3px; }
                """)
            else:
                self.power_bar.setStyleSheet("""
                    QProgressBar { border: 1px solid #3D2A50; border-radius: 4px; background-color: #241934; }
                    QProgressBar::chunk { background-color: #4CAF50; border-radius: 3px; }
                """)
        
        # Clock speeds
        clock_sm = metrics.get("clock_sm", 0)
        clock_mem = metrics.get("clock_mem", 0)
        self.sm_clock_label.setText(f"{clock_sm} MHz")
        self.mem_clock_label.setText(f"{clock_mem} MHz")


class DashboardTab(QWidget):
    """Dashboard tab showing GPU metrics."""
    
    def __init__(self, mock_mode=False):
        super().__init__()
        self.mock_mode = mock_mode
        self.logger = logging.getLogger('DualGPUOptimizer')
        self.logger.info("Initializing Dashboard tab")
        self.setup_ui()
    
    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel("GPU Dashboard")
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
        desc_label = QLabel("Real-time GPU metrics and monitoring")
        desc_label.setStyleSheet("color: #A0A0A0;")
        main_layout.addWidget(desc_label)
        
        # GPU cards layout - use horizontal layout for 2 cards
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(16)
        main_layout.addLayout(self.cards_layout)
        
        # Create GPU cards (for 2 GPUs as in the original app)
        self.gpu_cards = []
        for i in range(2):
            card = GPUCard(i, self)
            card.reset_clicked.connect(self.reset_gpu_memory)
            self.cards_layout.addWidget(card)
            self.gpu_cards.append(card)
            
        # Add historical metrics chart
        self.gpu_chart = GPUChart(self)
        main_layout.addWidget(self.gpu_chart)
        
        # Add spacer at the bottom
        main_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.logger.info("Dashboard UI setup complete")
    
    @Slot(list)
    def update_metrics(self, metrics_list):
        """Update GPU metrics for all cards."""
        for i, card in enumerate(self.gpu_cards):
            if i < len(metrics_list):
                card.update_metrics(metrics_list[i])
        
        # Update chart with new metrics
        self.gpu_chart.update_metrics(metrics_list)
    
    @Slot(int)
    def reset_gpu_memory(self, gpu_index):
        """Reset GPU memory."""
        self.logger.info(f"Attempting to reset memory for GPU {gpu_index}")
        
        try:
            import torch
            torch.cuda.empty_cache()
            if gpu_index < torch.cuda.device_count():
                with torch.cuda.device(gpu_index):
                    torch.cuda.empty_cache()
                    torch.cuda.reset_peak_memory_stats()
                self.logger.info(f"Reset memory for GPU {gpu_index}")
                return True
        except ImportError:
            self.logger.warning("PyTorch not available for memory reset")
        except Exception as e:
            self.logger.error(f"Error resetting GPU memory: {e}")
        
        return False 