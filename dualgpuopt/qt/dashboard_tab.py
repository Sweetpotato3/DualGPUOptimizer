import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QProgressBar, QFrame, QGridLayout, QSizePolicy,
                              QPushButton, QSpacerItem)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QFont, QIcon, QColor

logger = logging.getLogger('DualGPUOptimizer')

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
        
        # Add spacer at the bottom
        main_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.logger.info("Dashboard UI setup complete")
    
    @Slot(list)
    def update_metrics(self, metrics_list):
        """Update GPU metrics for all cards."""
        for i, card in enumerate(self.gpu_cards):
            if i < len(metrics_list):
                card.update_metrics(metrics_list[i])
    
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