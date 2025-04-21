import logging
import os
from typing import Dict, List, Optional, Tuple

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

logger = logging.getLogger('DualGPUOptimizer.LauncherTab')

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
    """Tab for launching and managing models with optimized settings."""
    
    def __init__(self, mock_mode=False):
        super().__init__()
        self.mock_mode = mock_mode
        self.logger = logging.getLogger("DualGPUOpt.LauncherTab")
        self.process_cards = {}
        self.next_process_id = 1
        
        # Create launch controller
        self.launch_controller = LaunchController(mock_mode=mock_mode)
        
        # Subscribe to events
        from dualgpuopt.services.event_service import event_bus
        event_bus.subscribe("optimizer_settings", self.apply_optimizer_settings)
        
        self._init_ui()
        
    def apply_optimizer_settings(self, settings):
        """
        Apply settings received from optimizer tab.
        
        Args:
            settings: Dictionary with optimizer settings
        """
        try:
            self.logger.info(f"Received optimizer settings: {settings}")
            
            # Update framework
            if "framework" in settings and settings["framework"] in self.framework_options:
                self.framework_combo.setCurrentText(settings["framework"])
            
            # Update model path if model_name is specified
            if "model_name" in settings and settings["model_name"]:
                # Check if this is a local path or just a model name
                model_name = settings["model_name"]
                if os.path.exists(model_name):
                    self.model_path_input.setText(model_name)
                else:
                    # Try to find in models directory
                    models_dir = os.path.join(os.getcwd(), "models")
                    if os.path.exists(models_dir):
                        model_path = os.path.join(models_dir, f"{model_name}.gguf")
                        if os.path.exists(model_path):
                            self.model_path_input.setText(model_path)
                        else:
                            # Just use as is
                            self.model_path_input.setText(model_name)
                    else:
                        self.model_path_input.setText(model_name)
            
            # Handle framework-specific settings
            framework = self.framework_combo.currentText()
            
            if framework == "llama.cpp":
                # Update context size
                if "context_size" in settings:
                    self.context_input.setText(str(settings["context_size"]))
                
                # Update GPU split
                if "gpu_split" in settings:
                    self.split_checkbox.setChecked(True)
                    self.split_input.setText(settings["gpu_split"])
                    
            elif framework == "vLLM":
                # Update context size (max_model_len in vLLM)
                if "context_size" in settings:
                    self.context_input.setText(str(settings["context_size"]))
                
                # Update tensor parallel size
                if "tensor_parallel_size" in settings:
                    self.tp_checkbox.setChecked(True)
                    self.tp_input.setText(str(settings["tensor_parallel_size"]))
            
            # Update command preview with new settings
            self.update_command_preview()
            
            # Show notification
            self.status_label.setText("Optimizer settings applied")
            
        except Exception as e:
            self.logger.error(f"Error applying optimizer settings: {e}")
            self.status_label.setText(f"Error applying settings: {str(e)}")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Model Launcher")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        # Add preset buttons to header
        preset_layout = QHBoxLayout()
        
        # Save preset button
        self.save_preset_button = QPushButton("Save Preset")
        self.save_preset_button.setIcon(QIcon.fromTheme("document-save"))
        self.save_preset_button.clicked.connect(self.save_preset)
        preset_layout.addWidget(self.save_preset_button)
        
        # Load preset button
        self.load_preset_button = QPushButton("Load Preset")
        self.load_preset_button.setIcon(QIcon.fromTheme("document-open"))
        self.load_preset_button.clicked.connect(self.load_preset)
        preset_layout.addWidget(self.load_preset_button)
        
        # Add preset layout to header with spacer
        header_layout.addStretch(1)
        header_layout.addLayout(preset_layout)
        
        main_layout.addLayout(header_layout)
        
        # Create a splitter for configuration and processes
        splitter = QSplitter(Qt.Vertical)
        
        # === Model Configuration Section ===
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        
        # Model selection group
        model_group = QGroupBox("Model Configuration")
        model_layout = QFormLayout(model_group)
        
        # Model path selection
        model_path_layout = QHBoxLayout()
        self.model_path_input = QLineEdit()
        self.model_path_input.setPlaceholderText("Path to model file")
        model_path_layout.addWidget(self.model_path_input, 1)
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_model)
        model_path_layout.addWidget(self.browse_button)
        
        model_layout.addRow("Model Path:", model_path_layout)
        
        # Model framework selection
        self.framework_combo = QComboBox()
        self.framework_combo.addItems(["llama.cpp", "vLLM"])
        model_layout.addRow("Framework:", self.framework_combo)
        
        # Context size
        self.context_input = QLineEdit()
        self.context_input.setPlaceholderText("Default: auto")
        model_layout.addRow("Context Size:", self.context_input)
        
        # GPU split option for llama.cpp
        self.split_layout = QHBoxLayout()
        self.split_checkbox = QCheckBox("Enable GPU Split")
        self.split_input = QLineEdit()
        self.split_input.setPlaceholderText("Default: auto")
        self.split_input.setEnabled(False)
        self.split_checkbox.stateChanged.connect(
            lambda state: self.split_input.setEnabled(state == Qt.Checked)
        )
        self.split_layout.addWidget(self.split_checkbox)
        self.split_layout.addWidget(self.split_input)
        model_layout.addRow("GPU Split:", self.split_layout)
        
        # Tensor parallel for vLLM
        self.tp_layout = QHBoxLayout()
        self.tp_checkbox = QCheckBox("Enable Tensor Parallel")
        self.tp_input = QLineEdit()
        self.tp_input.setPlaceholderText("Default: auto")
        self.tp_input.setEnabled(False)
        self.tp_checkbox.stateChanged.connect(
            lambda state: self.tp_input.setEnabled(state == Qt.Checked)
        )
        self.tp_layout.addWidget(self.tp_checkbox)
        self.tp_layout.addWidget(self.tp_input)
        model_layout.addRow("Tensor Parallel:", self.tp_layout)
        
        # Add additional arguments
        self.args_input = QLineEdit()
        self.args_input.setPlaceholderText("Additional command line arguments")
        model_layout.addRow("Extra Args:", self.args_input)
        
        config_layout.addWidget(model_group)
        
        # Command preview and launch button
        command_layout = QHBoxLayout()
        self.command_preview = QLineEdit()
        self.command_preview.setReadOnly(True)
        self.command_preview.setPlaceholderText("Command will appear here")
        command_layout.addWidget(self.command_preview, 1)
        
        self.launch_button = QPushButton("Launch")
        self.launch_button.setIcon(QIcon.fromTheme("media-playback-start"))
        self.launch_button.clicked.connect(self.launch_model)
        command_layout.addWidget(self.launch_button)
        
        config_layout.addLayout(command_layout)
        
        # Update command button
        self.update_command_button = QPushButton("Update Command")
        self.update_command_button.clicked.connect(self.update_command_preview)
        config_layout.addWidget(self.update_command_button)
        
        # Add config widget to splitter
        splitter.addWidget(config_widget)
        
        # === Running Processes Section ===
        self.processes_tab = QTabWidget()
        self.processes_tab.setTabPosition(QTabWidget.North)
        self.processes_tab.setTabsClosable(True)
        self.processes_tab.tabCloseRequested.connect(self.close_process_tab)
        
        # Add processes widget to splitter
        splitter.addWidget(self.processes_tab)
        
        # Set initial sizes for splitter
        splitter.setSizes([300, 500])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Connect signals
        self.framework_combo.currentTextChanged.connect(self.handle_framework_change)
        
        # Initialize UI state based on current framework
        self.handle_framework_change(self.framework_combo.currentText())
    
    def handle_framework_change(self, framework):
        """Update UI based on selected framework."""
        if framework == "llama.cpp":
            # Enable llama.cpp specific options
            self.split_checkbox.setEnabled(True)
            self.tp_checkbox.setEnabled(False)
            self.tp_input.setEnabled(False)
        else:  # vLLM
            # Enable vLLM specific options
            self.split_checkbox.setEnabled(False)
            self.split_input.setEnabled(False)
            self.tp_checkbox.setEnabled(True)
        
        # Update command preview
        self.update_command_preview()
    
    def browse_model(self):
        """Open file dialog to select model path."""
        model_path, _ = QFileDialog.getOpenFileName(
            self, "Select Model File", "", 
            "Model Files (*.bin *.gguf *.ggml *.safetensors);;All Files (*)"
        )
        
        if model_path:
            self.model_path_input.setText(model_path)
            self.update_command_preview()
    
    def update_command_preview(self):
        """Update the command preview based on current settings."""
        try:
            framework = self.framework_combo.currentText()
            model_path = self.model_path_input.text()
            
            if not model_path:
                self.command_preview.setText("")
                return
            
            # Get context size if specified
            context_text = self.context_input.text().strip()
            context = int(context_text) if context_text else None
            
            # Additional arguments
            extra_args = self.args_input.text().strip()
            
            command = ""
            if framework == "llama.cpp":
                # GPU split for llama.cpp
                split = None
                if self.split_checkbox.isChecked() and self.split_input.isEnabled():
                    split_text = self.split_input.text().strip()
                    if split_text:
                        try:
                            split = float(split_text)
                        except ValueError:
                            pass
                
                command = self.launch_controller.generate_llama_command(
                    model_path, context_size=context, gpu_split=split, extra_args=extra_args
                )
            else:  # vLLM
                # Tensor parallel for vLLM
                tp_size = None
                if self.tp_checkbox.isChecked() and self.tp_input.isEnabled():
                    tp_text = self.tp_input.text().strip()
                    if tp_text:
                        try:
                            tp_size = int(tp_text)
                        except ValueError:
                            pass
                
                command = self.launch_controller.generate_vllm_command(
                    model_path, tp_size=tp_size, extra_args=extra_args
                )
            
            self.command_preview.setText(command)
            
        except Exception as e:
            self.logger.error(f"Error updating command preview: {e}")
            self.command_preview.setText(f"Error: {str(e)}")
    
    def launch_model(self):
        """Launch the model with current settings."""
        command = self.command_preview.text()
        
        if not command:
            QMessageBox.warning(self, "Launch Error", "Please configure a valid command first.")
            return
        
        # Create a new process card and add it to the tab
        process_id = self.next_process_id
        self.next_process_id += 1
        
        process_card = ProcessCard(process_id, command)
        process_card.terminate_signal.connect(self.handle_process_terminated)
        
        # Add to processes tab
        tab_name = f"Process #{process_id}"
        tab_index = self.processes_tab.addTab(process_card, tab_name)
        self.processes_tab.setCurrentIndex(tab_index)
        
        # Store reference to process card
        self.process_cards[process_id] = process_card
        
        # Start the process
        process_card.start_process()
    
    def handle_process_terminated(self, process_id):
        """Handle process termination notification."""
        self.logger.info(f"Process #{process_id} terminated")
        # We could update the tab title or add an indicator here
    
    def close_process_tab(self, index):
        """Handle tab close request."""
        process_card = self.processes_tab.widget(index)
        
        # If process is still running, confirm before closing
        if process_card.is_running:
            reply = QMessageBox.question(
                self, "Close Process", 
                "This process is still running. Do you want to terminate it and close the tab?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                process_card.stop_process()
            else:
                return  # Don't close the tab
        
        # Remove the tab
        self.processes_tab.removeTab(index)
        
        # Remove from our tracking dict if it's there
        for pid, card in list(self.process_cards.items()):
            if card == process_card:
                del self.process_cards[pid]
                break
    
    def save_preset(self):
        """Save current configuration as a preset."""
        try:
            # Get current settings
            current_config = self._get_current_config()
            
            # Ask for preset name
            preset_name, ok = QInputDialog.getText(
                self, "Save Preset", "Enter preset name:", 
                QLineEdit.Normal, f"{current_config.get('framework', '')}_{current_config.get('model_name', 'config')}"
            )
            
            if not ok or not preset_name:
                return
                
            # Get presets storage
            from dualgpuopt.services.config_service import config_service
            presets = config_service.get("launcher_presets", {})
            
            # Add new preset
            presets[preset_name] = current_config
            
            # Save to config service
            config_service.set("launcher_presets", presets)
            config_service.save()
            
            self.logger.info(f"Saved preset: {preset_name}")
            self.status_label.setText(f"Preset '{preset_name}' saved")
            
        except Exception as e:
            self.logger.error(f"Error saving preset: {e}")
            QMessageBox.warning(self, "Error", f"Error saving preset: {e}")
    
    def load_preset(self):
        """Load a saved preset configuration."""
        try:
            # Get presets storage
            from dualgpuopt.services.config_service import config_service
            presets = config_service.get("launcher_presets", {})
            
            if not presets:
                QMessageBox.information(self, "No Presets", "No presets have been saved yet.")
                return
                
            # Show preset selection dialog
            preset_name, ok = QInputDialog.getItem(
                self, "Load Preset", "Select a preset:", 
                list(presets.keys()), 0, False
            )
            
            if not ok or not preset_name:
                return
                
            # Get preset configuration
            config = presets.get(preset_name, {})
            if not config:
                self.logger.warning(f"Preset '{preset_name}' is empty or invalid")
                return
                
            # Apply the configuration
            self._apply_config(config)
            
            self.logger.info(f"Loaded preset: {preset_name}")
            self.status_label.setText(f"Preset '{preset_name}' loaded")
            
        except Exception as e:
            self.logger.error(f"Error loading preset: {e}")
            QMessageBox.warning(self, "Error", f"Error loading preset: {e}")
    
    def _get_current_config(self):
        """Get current configuration as a dictionary."""
        config = {
            "framework": self.framework_combo.currentText(),
            "model_path": self.model_path_input.text(),
        }
        
        # Framework-specific settings
        if config["framework"] == "llama.cpp":
            config.update({
                "context_size": self.context_input.text(),
                "gpu_split": self.split_input.text() if self.split_checkbox.isChecked() else None,
                "extra_args": self.args_input.text()
            })
        elif config["framework"] == "vLLM":
            config.update({
                "context_size": self.context_input.text(),
                "tensor_parallel_size": self.tp_input.text() if self.tp_checkbox.isChecked() else None,
                "extra_args": self.args_input.text()
            })
        
        return config
    
    def _apply_config(self, config):
        """Apply a configuration dictionary to the UI."""
        # Set framework
        if "framework" in config and config["framework"] in self.framework_options:
            self.framework_combo.setCurrentText(config["framework"])
            
        # Set model path
        if "model_path" in config:
            self.model_path_input.setText(config["model_path"])
            
        # Handle framework-specific settings
        framework = config.get("framework")
        
        # Wait for framework UI to update
        QApplication.processEvents()
        
        if framework == "llama.cpp":
            # Set context size
            if "context_size" in config:
                self.context_input.setText(str(config["context_size"]))
                
            # Set GPU split
            if "gpu_split" in config and config["gpu_split"]:
                self.split_checkbox.setChecked(True)
                self.split_input.setText(config["gpu_split"])
                
            # Set extra args
            if "extra_args" in config:
                self.args_input.setText(config["extra_args"])
                
        elif framework == "vLLM":
            # Set context size
            if "context_size" in config:
                self.context_input.setText(str(config["context_size"]))
                
            # Set tensor parallel size
            if "tensor_parallel_size" in config and config["tensor_parallel_size"]:
                self.tp_checkbox.setChecked(True)
                self.tp_input.setText(str(config["tensor_parallel_size"]))
                
            # Set extra args
            if "extra_args" in config:
                self.args_input.setText(config["extra_args"])
        
        # Update command preview
        self.update_command_preview() 