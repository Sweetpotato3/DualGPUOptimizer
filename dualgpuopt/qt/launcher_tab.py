"""
Launcher tab for DualGPUOptimizer Qt implementation.
Provides an interface for launching and managing model execution.
"""

import logging
from typing import Any, Dict, Optional

from PySide6.QtCore import QProcess, QTimer, Signal, Slot
from PySide6.QtGui import QFont, QIcon, QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Import shared constants
from dualgpuopt.engine.backend import Engine
from dualgpuopt.services.presets import PresetManager

logger = logging.getLogger("DualGPUOptimizer.Launcher")


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
            self.output_display.append(f"Error starting process: {e!s}")

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
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        self.output_display.append(data)
        self.output_display.moveCursor(QTextCursor.End)

    def handle_stderr(self):
        """Handle standard error from the process."""
        data = self.process.readAllStandardError().data().decode("utf-8", errors="replace")
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
        """
        Initialize the launcher tab

        Args:
        ----
            parent: Parent widget

        """
        super().__init__(parent)

        # Initialize engine (will be set from main app)
        self.engine = None
        self.process_cards = {}
        self.next_process_id = 1

        # Setup UI
        self._setup_ui()

    def set_engine(self, engine: Engine):
        """
        Set the engine instance

        Args:
        ----
            engine: The unified Engine instance

        """
        self.engine = engine
        logger.info("Engine instance set in LauncherTab")
        self.status_label.setText("Engine connected")

        # Populate model formats based on engine capabilities
        if engine:
            self.format_combo.clear()
            for fmt in engine.supported_formats:
                self.format_combo.addItem(fmt)

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
        model_path_layout = QHBoxLayout()
        self.model_path = QLineEdit()
        self.model_path.setPlaceholderText("Enter model path or name...")
        model_path_layout.addWidget(self.model_path)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_model)
        model_path_layout.addWidget(self.browse_btn)

        config_layout.addRow("Model:", model_path_layout)

        # Model format
        self.format_combo = QComboBox()
        self.format_combo.addItems(["auto", "gguf", "awq", "hf"])
        config_layout.addRow("Format:", self.format_combo)

        # Framework
        self.framework_combo = QComboBox()
        self.framework_combo.addItems(["llama.cpp", "vLLM"])
        config_layout.addRow("Framework:", self.framework_combo)

        # Context size
        self.context_size = QLineEdit()
        self.context_size.setPlaceholderText("Default")
        config_layout.addRow("Context Size:", self.context_size)

        # GPU split layout
        split_layout = QHBoxLayout()
        self.gpu0_split = QLineEdit()
        self.gpu0_split.setPlaceholderText("Auto")
        split_layout.addWidget(QLabel("GPU 0:"))
        split_layout.addWidget(self.gpu0_split)

        self.gpu1_split = QLineEdit()
        self.gpu1_split.setPlaceholderText("Auto")
        split_layout.addWidget(QLabel("GPU 1:"))
        split_layout.addWidget(self.gpu1_split)

        config_layout.addRow("GPU Split:", split_layout)

        # Button layout
        button_layout = QHBoxLayout()

        # Launch button
        self.launch_btn = QPushButton("Launch Model")
        self.launch_btn.clicked.connect(self._launch_model)
        button_layout.addWidget(self.launch_btn)

        # Save preset button
        self.save_preset_btn = QPushButton("Save as Preset")
        self.save_preset_btn.clicked.connect(self.save_preset)
        button_layout.addWidget(self.save_preset_btn)

        config_layout.addRow("", button_layout)

        main_layout.addWidget(config_group)

        # Process tabs
        self.process_tabs = QTabWidget()
        self.process_tabs.setTabsClosable(True)
        self.process_tabs.tabCloseRequested.connect(self._close_process_tab)
        main_layout.addWidget(self.process_tabs)

        # Status label
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)

    def _browse_model(self):
        """Open file browser to select model"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Model File",
            "",
            "Model Files (*.gguf *.bin *.pt);;All Files (*.*)",
        )

        if file_path:
            self.model_path.setText(file_path)

            # Try to auto-detect format
            if self.engine:
                detected_format = self.engine.detect_model_format(file_path)
                if detected_format:
                    index = self.format_combo.findText(detected_format)
                    if index >= 0:
                        self.format_combo.setCurrentIndex(index)

    def _launch_model(self):
        """Launch the model using the engine"""
        if not self.engine:
            self.status_label.setText("Error: Engine not initialized")
            QMessageBox.critical(self, "Error", "Engine not initialized. Cannot launch model.")
            return

        model_path = self.model_path.text().strip()
        if not model_path:
            self.status_label.setText("Error: No model specified")
            return

        # Get parameters
        model_format = self.format_combo.currentText()
        framework = self.framework_combo.currentText()

        # Parse context size
        context_size = None
        if self.context_size.text().strip():
            try:
                context_size = int(self.context_size.text().strip())
            except ValueError:
                self.status_label.setText("Error: Invalid context size")
                return

        # Parse GPU splits
        gpu_split = None
        if self.gpu0_split.text().strip() and self.gpu1_split.text().strip():
            try:
                gpu0 = int(self.gpu0_split.text().strip())
                gpu1 = int(self.gpu1_split.text().strip())
                gpu_split = (gpu0, gpu1)
            except ValueError:
                self.status_label.setText("Error: Invalid GPU split values")
                return

        try:
            # Generate command through the engine
            command = self.engine.generate_command(
                model_path=model_path,
                model_format=model_format,
                framework=framework,
                context_size=context_size,
                gpu_split=gpu_split,
            )

            # Create new process card
            process_id = self.next_process_id
            self.next_process_id += 1

            card = ProcessCard(process_id, command)
            card.terminate_signal.connect(self._handle_process_termination)

            # Add to tabs
            tab_name = f"Process #{process_id}"
            tab_index = self.process_tabs.addTab(card, tab_name)
            self.process_tabs.setCurrentIndex(tab_index)

            # Store process card
            self.process_cards[process_id] = card

            # Start process
            card.start_process()

            self.status_label.setText(f"Launched model with process ID {process_id}")

        except Exception as e:
            logger.error(f"Failed to launch model: {e}")
            self.status_label.setText(f"Error: {e!s}")
            QMessageBox.critical(self, "Launch Error", f"Failed to launch model: {e!s}")

    def _close_process_tab(self, index):
        """Handle tab close request"""
        widget = self.process_tabs.widget(index)

        # Check if process is running
        if hasattr(widget, "is_running") and widget.is_running:
            confirm = QMessageBox.question(
                self,
                "Confirm Close",
                "Process is still running. Stop it and close the tab?",
                QMessageBox.Yes | QMessageBox.No,
            )

            if confirm == QMessageBox.Yes:
                widget.stop_process()
            else:
                return

        # Remove tab and clean up
        self.process_tabs.removeTab(index)

        # Find and remove from process cards
        to_remove = None
        for pid, card in self.process_cards.items():
            if card == widget:
                to_remove = pid
                break

        if to_remove is not None:
            del self.process_cards[to_remove]

    def _handle_process_termination(self, process_id):
        """Handle process termination signal"""
        self.status_label.setText(f"Process {process_id} terminated")

    @Slot(dict)
    def apply_optimizer_settings(self, config: Dict[str, Any]):
        """
        Apply settings from the optimizer tab

        Args:
        ----
            config: Configuration dictionary

        """
        # Apply settings
        self.model_path.setText(config.get("model", ""))

        # Set model format if available
        if "format" in config:
            index = self.format_combo.findText(config.get("format"))
            if index >= 0:
                self.format_combo.setCurrentIndex(index)

        # Set framework
        if "framework" in config:
            index = self.framework_combo.findText(config.get("framework"))
            if index >= 0:
                self.framework_combo.setCurrentIndex(index)

        # Set context size
        if "context_size" in config:
            self.context_size.setText(str(config.get("context_size")))

        # Set GPU splits
        if (
            "gpu_split" in config
            and isinstance(config["gpu_split"], tuple)
            and len(config["gpu_split"]) == 2
        ):
            self.gpu0_split.setText(str(config["gpu_split"][0]))
            self.gpu1_split.setText(str(config["gpu_split"][1]))

        # Show status
        self.status_label.setText("Settings applied from optimizer")

    @Slot(dict)
    def apply_preset(self, preset_data: Dict[str, Any]):
        """
        Apply preset data to the launcher tab

        Args:
        ----
            preset_data: Dictionary containing preset configuration

        """
        try:
            # Extract settings from preset
            if not preset_data:
                self.status_label.setText("Error: Empty preset data")
                return

            # Extract model path if available
            model_path = preset_data.get("model_path", "")
            if model_path:
                self.model_path.setText(model_path)

            # Extract framework
            framework = preset_data.get("framework", "")
            if framework:
                index = self.framework_combo.findText(framework)
                if index >= 0:
                    self.framework_combo.setCurrentIndex(index)

            # Extract format
            model_format = preset_data.get("model_format", "")
            if model_format:
                index = self.format_combo.findText(model_format)
                if index >= 0:
                    self.format_combo.setCurrentIndex(index)

            # Extract context size
            context_size = preset_data.get("context_size", "")
            if context_size:
                self.context_size.setText(str(context_size))

            # Extract GPU splits
            gpu_settings = preset_data.get("gpu_settings", {})
            if gpu_settings:
                gpu0 = gpu_settings.get("gpu0_allocation", "")
                gpu1 = gpu_settings.get("gpu1_allocation", "")

                if gpu0 and "%" in gpu0:
                    gpu0 = gpu0.replace("%", "")
                if gpu1 and "%" in gpu1:
                    gpu1 = gpu1.replace("%", "")

                if gpu0:
                    self.gpu0_split.setText(gpu0)
                if gpu1:
                    self.gpu1_split.setText(gpu1)

            # Extract command if present
            command = preset_data.get("command", "")
            if command:
                # Pre-fill command, but don't launch automatically
                self.status_label.setText(f"Loaded preset: {preset_data.get('name', 'Unknown')}")

        except Exception as e:
            logger.error(f"Error applying preset: {e}")
            self.status_label.setText(f"Error applying preset: {e}")

    def save_preset(self):
        """Save current launcher configuration as a preset"""
        try:
            name, ok = QInputDialog.getText(self, "Save Preset", "Enter preset name:")

            if ok and name:
                # Get GPU splits as percentages
                gpu0_split = self.gpu0_split.text().strip()
                gpu1_split = self.gpu1_split.text().strip()

                if gpu0_split and not gpu0_split.endswith("%"):
                    gpu0_split += "%"
                if gpu1_split and not gpu1_split.endswith("%"):
                    gpu1_split += "%"

                # Create preset data
                preset_data = {
                    "name": name,
                    "type": "launcher",
                    "model_path": self.model_path.text(),
                    "model_format": self.format_combo.currentText(),
                    "framework": self.framework_combo.currentText(),
                    "context_size": self.context_size.text(),
                    "gpu_settings": {
                        "gpu0_allocation": gpu0_split,
                        "gpu1_allocation": gpu1_split,
                        "max_context": self.context_size.text(),
                    },
                    "prompt_template": "",  # For chat components
                    "persona": "",  # For chat components
                }

                # Save preset
                manager = PresetManager()
                manager.save_preset(name, preset_data)

                self.status_label.setText(f"Preset '{name}' saved successfully")
        except Exception as e:
            logger.error(f"Error saving preset: {e}")
            self.status_label.setText(f"Error saving preset: {e}")
