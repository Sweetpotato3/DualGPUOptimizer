"""
Launcher tab for DualGPUOptimizer Qt implementation.
Provides an interface for launching and managing model execution.
"""
import logging
import os
from typing import Dict, List, Optional, Tuple, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QLineEdit, QTextEdit, QGroupBox, QFormLayout,
    QCheckBox, QTabWidget, QSplitter, QFileDialog, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt, QProcess, QTimer, Signal, Slot, QSize
from PySide6.QtGui import QTextCursor, QFont, QIcon
from PySide6.QtWidgets import QApplication

from dualgpuopt.gui.launcher.launch_controller import LaunchController
from dualgpuopt.gui.launcher.parameter_resolver import ParameterResolver
from dualgpuopt.gui.launcher.model_validation import ModelValidator
from dualgpuopt.gui.launcher.process_monitor import ProcessMonitor

logger = logging.getLogger('DualGPUOptimizer.Launcher')

class ProcessCard(QWidget):
    """Widget displaying a running process with controls and log output."""
    
    terminate_signal = Signal(int)  # Signal to notify launcher of termination
    
    def __init__(self, process_id: int, command: str, parent=None):
        super().__init__(parent)
        self.process_id = process_id
        self.command = command
        self.process = QProcess()
        self.is_running = False
        
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        
        # Process title
        self.title_label = QLabel(f"Process #{self.process_id}")
        font = self.title_label.font()
        font.setPointSize(12)
        font.setBold(True)
        self.title_label.setFont(font)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Status label
        self.status_label = QLabel("Stopped")
        self.status_label.setStyleSheet("color: #FF5555;")
        header_layout.addWidget(self.status_label)
        
        # Control buttons
        self.start_button = QPushButton("Start")
        self.start_button.setIcon(QIcon.fromTheme("media-playback-start"))
        self.start_button.setMaximumWidth(80)
        header_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setIcon(QIcon.fromTheme("media-playback-stop"))
        self.stop_button.setMaximumWidth(80)
        self.stop_button.setEnabled(False)
        header_layout.addWidget(self.stop_button)
        
        layout.addLayout(header_layout)
        
        # Command display
        command_box = QGroupBox("Command")
        command_layout = QVBoxLayout(command_box)
        self.command_display = QTextEdit()
        self.command_display.setReadOnly(True)
        self.command_display.setMaximumHeight(60)
        self.command_display.setText(self.command)
        command_layout.addWidget(self.command_display)
        layout.addWidget(command_box)
        
        # Process output
        output_box = QGroupBox("Output")
        output_layout = QVBoxLayout(output_box)
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        font = QFont("Courier New", 9)
        self.output_display.setFont(font)
        self.output_display.setStyleSheet("background-color: #1A1A1A; color: #CCCCCC;")
        output_layout.addWidget(self.output_display)
        layout.addWidget(output_box)
        
        # Ensure output box takes most of the vertical space
        layout.setStretchFactor(output_box, 3)
    
    def _connect_signals(self):
        """Connect UI signals to slots."""
        self.start_button.clicked.connect(self.start_process)
        self.stop_button.clicked.connect(self.stop_process)
        
        # Connect process signals
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.stateChanged.connect(self.handle_state_change)
        self.process.finished.connect(self.handle_finished)
    
    def start_process(self):
        """Start the process using the provided command."""
        try:
            self.output_display.clear()
            self.output_display.append(f"Starting process: {self.command}\n")
            self.process.start("cmd.exe", ["/c", self.command])
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.is_running = True
            self.status_label.setText("Running")
            self.status_label.setStyleSheet("color: #55FF55;")
        except Exception as e:
            logger.error(f"Failed to start process: {e}")
            self.output_display.append(f"Error starting process: {str(e)}")
    
    def stop_process(self):
        """Stop the running process."""
        if self.is_running:
            self.process.terminate()
            # Give it some time to terminate gracefully
            QTimer.singleShot(3000, self.force_kill)
    
    def force_kill(self):
        """Force kill the process if it didn't terminate gracefully."""
        if self.is_running and self.process.state() != QProcess.NotRunning:
            self.process.kill()
    
    def handle_stdout(self):
        """Handle standard output from the process."""
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        self.output_display.append(data)
        self.output_display.moveCursor(QTextCursor.End)
    
    def handle_stderr(self):
        """Handle standard error from the process."""
        data = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
        self.output_display.append(f"<span style='color:#FF5555;'>{data}</span>")
        self.output_display.moveCursor(QTextCursor.End)
    
    def handle_state_change(self, state):
        """Handle process state changes."""
        if state == QProcess.NotRunning:
            self.is_running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText("Stopped")
            self.status_label.setStyleSheet("color: #FF5555;")
        else:
            self.is_running = True
    
    def handle_finished(self, exit_code, exit_status):
        """Handle process finish event."""
        status_text = f"Finished (code: {exit_code})"
        if exit_status != QProcess.NormalExit:
            status_text = "Crashed"
        
        self.output_display.append(f"\nProcess {status_text}")
        self.is_running = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Stopped")
        self.status_label.setStyleSheet("color: #FF5555;")
        
        # Notify launcher that this process has terminated
        self.terminate_signal.emit(self.process_id)

class LauncherTab(QWidget):
    """Launcher tab for model execution"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the launcher tab
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Model Launcher")
        title_font = title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 2)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Launch and manage model execution")
        main_layout.addWidget(desc_label)
        
        # Model configuration group
        config_group = QGroupBox("Model Configuration")
        config_layout = QFormLayout(config_group)
        
        # Model path/name
        self.model_path = QLineEdit()
        self.model_path.setPlaceholderText("Enter model path or name...")
        config_layout.addRow("Model:", self.model_path)
        
        # Framework
        self.framework_combo = QComboBox()
        self.framework_combo.addItems(["llama.cpp", "vLLM"])
        config_layout.addRow("Framework:", self.framework_combo)
        
        # Command input
        config_layout.addRow("Command:", QLabel(""))
        self.command_text = QTextEdit()
        self.command_text.setPlaceholderText("Enter command to run...")
        self.command_text.setMinimumHeight(100)
        config_layout.addRow("", self.command_text)
        
        # Launch button
        self.launch_btn = QPushButton("Launch Model")
        self.launch_btn.clicked.connect(self._launch_model)
        config_layout.addRow("", self.launch_btn)
        
        main_layout.addWidget(config_group)
        
        # Output group
        output_group = QGroupBox("Process Output")
        output_layout = QVBoxLayout(output_group)
        
        # Process output text
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Process output will appear here...")
        output_layout.addWidget(self.output_text)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.stop_btn = QPushButton("Stop Process")
        self.stop_btn.clicked.connect(self._stop_process)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        self.clear_btn = QPushButton("Clear Output")
        self.clear_btn.clicked.connect(self._clear_output)
        control_layout.addWidget(self.clear_btn)
        
        output_layout.addLayout(control_layout)
        
        main_layout.addWidget(output_group)
        
        # Status label
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
        # Stretch to push everything to the top
        main_layout.addStretch(1)
    
    def _launch_model(self):
        """Launch the model process"""
        # Get command
        command = self.command_text.toPlainText().strip()
        
        if not command:
            self.status_label.setText("Error: No command specified")
            return
        
        # Display in output
        self.output_text.append(f"Running command: {command}\n")
        self.output_text.append("Mock process started...\n")
        
        # Update UI state
        self.stop_btn.setEnabled(True)
        self.launch_btn.setEnabled(False)
        self.status_label.setText("Process running")
    
    def _stop_process(self):
        """Stop the running process"""
        self.output_text.append("\nProcess stopped.\n")
        
        # Update UI state
        self.stop_btn.setEnabled(False)
        self.launch_btn.setEnabled(True)
        self.status_label.setText("Process stopped")
    
    def _clear_output(self):
        """Clear the output text"""
        self.output_text.clear()
    
    @Slot(dict)
    def apply_optimizer_settings(self, config: Dict[str, Any]):
        """Apply settings from the optimizer tab
        
        Args:
            config: Configuration dictionary
        """
        # Apply settings
        self.model_path.setText(config.get("model", ""))
        self.framework_combo.setCurrentText(config.get("framework", "llama.cpp"))
        self.command_text.setText(config.get("command", ""))
        
        # Show status
        self.status_label.setText("Settings applied from optimizer")
        self.output_text.append(f"Applied settings from optimizer:\n")
        for key, value in config.items():
            self.output_text.append(f"  {key}: {value}\n") 