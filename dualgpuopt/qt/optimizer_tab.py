"""
Optimizer tab for DualGPUOptimizer Qt implementation.
Provides model parameter optimization and GPU split calculations.
"""

import logging
from typing import Any, Dict, Optional

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger("DualGPUOptimizer.Optimizer")


class OptimizerTab(QWidget):
    """Optimizer tab for calculating optimal GPU configurations"""

    # Signals
    settings_applied = Signal(dict)  # Emitted when settings are applied

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the optimizer tab

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
        title_label = QLabel("GPU Memory Optimizer")
        title_font = title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 2)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # Description
        desc_label = QLabel("Calculate optimal GPU memory and layer distribution")
        main_layout.addWidget(desc_label)

        # Create a horizontal layout for the main components
        h_layout = QHBoxLayout()
        main_layout.addLayout(h_layout)

        # Left panel - inputs
        input_group = QGroupBox("Model Parameters")
        input_layout = QFormLayout(input_group)

        # Model selection
        self.model_combo = QComboBox()
        self.model_combo.addItems(
            ["Llama-2-7B", "Llama-2-13B", "Llama-2-70B", "Mistral-7B", "Mixtral-8x7B"]
        )
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        input_layout.addRow("Model:", self.model_combo)

        # Context size
        self.context_size = QSpinBox()
        self.context_size.setRange(128, 32768)
        self.context_size.setValue(2048)
        self.context_size.setSingleStep(512)
        input_layout.addRow("Context Size:", self.context_size)

        # Framework
        self.framework_combo = QComboBox()
        self.framework_combo.addItems(["llama.cpp", "vLLM"])
        input_layout.addRow("Framework:", self.framework_combo)

        # Precision/Quantization
        self.precision_combo = QComboBox()
        self.precision_combo.addItems(["float16", "float8", "Q8_0", "Q6_K", "Q5_K", "Q4_K", "Q4_0"])
        input_layout.addRow("Precision:", self.precision_combo)

        # Add button layout for actions
        button_layout = QHBoxLayout()

        # Add optimize button
        self.optimize_btn = QPushButton("Calculate Optimal Configuration")
        self.optimize_btn.clicked.connect(self._calculate_config)
        button_layout.addWidget(self.optimize_btn)

        # Add save preset button
        self.save_preset_btn = QPushButton("Save as Preset")
        self.save_preset_btn.clicked.connect(self.save_preset)
        button_layout.addWidget(self.save_preset_btn)

        input_layout.addRow(button_layout)

        h_layout.addWidget(input_group)

        # Right panel - results
        results_group = QGroupBox("Optimization Results")
        results_layout = QVBoxLayout(results_group)

        # Results grid
        results_grid = QGridLayout()

        # GPU 0 allocation
        results_grid.addWidget(QLabel("GPU 0:"), 0, 0)
        self.gpu0_allocation = QLabel("N/A")
        results_grid.addWidget(self.gpu0_allocation, 0, 1)

        # GPU 1 allocation
        results_grid.addWidget(QLabel("GPU 1:"), 1, 0)
        self.gpu1_allocation = QLabel("N/A")
        results_grid.addWidget(self.gpu1_allocation, 1, 1)

        # Max context
        results_grid.addWidget(QLabel("Max Context:"), 2, 0)
        self.max_context = QLabel("N/A")
        results_grid.addWidget(self.max_context, 2, 1)

        # Layer distribution
        results_grid.addWidget(QLabel("Layer Distribution:"), 3, 0)
        self.layer_distribution = QLabel("N/A")
        results_grid.addWidget(self.layer_distribution, 3, 1)

        results_layout.addLayout(results_grid)

        # Command line
        results_layout.addWidget(QLabel("Command:"))
        self.command_text = QTextEdit()
        self.command_text.setReadOnly(True)
        self.command_text.setMinimumHeight(100)
        results_layout.addWidget(self.command_text)

        # Apply button
        self.apply_btn = QPushButton("Apply to Launcher")
        self.apply_btn.clicked.connect(self._apply_to_launcher)
        self.apply_btn.setEnabled(False)
        results_layout.addWidget(self.apply_btn)

        h_layout.addWidget(results_group)

        # Add status label
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)

        # Stretch to push everything to the top
        main_layout.addStretch(1)

    def _on_model_changed(self, index):
        """Handle model selection change

        Args:
            index: New index
        """
        model_name = self.model_combo.currentText()

        # Set reasonable defaults based on model
        if "70B" in model_name:
            self.context_size.setValue(2048)
        elif "13B" in model_name:
            self.context_size.setValue(4096)
        elif "Mixtral" in model_name:
            self.context_size.setValue(4096)
        else:
            self.context_size.setValue(8192)

        self.status_label.setText(f"Selected model: {model_name}")

    def _calculate_config(self):
        """Calculate optimal configuration based on inputs"""
        model_name = self.model_combo.currentText()
        context_size = self.context_size.value()
        framework = self.framework_combo.currentText()
        precision = self.precision_combo.currentText()

        # Mock optimization calculation
        if "70B" in model_name:
            gpu0_mem = "70%"
            gpu1_mem = "30%"
            layer_distribution = "0-39:GPU0, 40-79:GPU1"
            max_context = min(context_size, 4096)
        elif "Mixtral" in model_name:
            gpu0_mem = "60%"
            gpu1_mem = "40%"
            layer_distribution = "0-15:GPU0, 16-31:GPU1"
            max_context = min(context_size, 8192)
        elif "13B" in model_name:
            gpu0_mem = "50%"
            gpu1_mem = "50%"
            layer_distribution = "0-19:GPU0, 20-39:GPU1"
            max_context = min(context_size, 12288)
        else:
            gpu0_mem = "40%"
            gpu1_mem = "60%"
            layer_distribution = "All layers on GPU 0"
            max_context = min(context_size, 16384)

        # Update results
        self.gpu0_allocation.setText(gpu0_mem)
        self.gpu1_allocation.setText(gpu1_mem)
        self.max_context.setText(str(max_context))
        self.layer_distribution.setText(layer_distribution)

        # Create command
        if framework == "llama.cpp":
            command = f"./main -m {model_name} -c {max_context} --gpu-layers-gpu0 {gpu0_mem} --gpu-layers-gpu1 {gpu1_mem}"
            if precision != "float16":
                command += f" -q {precision}"
        else:  # vLLM
            command = f"python -m vllm.entrypoints.api_server --model {model_name} --tensor-parallel-size 2 --max-model-len {max_context}"
            if precision != "float16":
                command += f" --dtype {precision}"

        self.command_text.setText(command)

        # Enable apply button
        self.apply_btn.setEnabled(True)

        self.status_label.setText("Configuration calculated successfully")

    def _apply_to_launcher(self):
        """Apply the current configuration to the launcher tab"""
        # Create configuration dictionary
        config = {
            "model": self.model_combo.currentText(),
            "context_size": self.context_size.value(),
            "framework": self.framework_combo.currentText(),
            "precision": self.precision_combo.currentText(),
            "command": self.command_text.toPlainText(),
            "gpu0_allocation": self.gpu0_allocation.text(),
            "gpu1_allocation": self.gpu1_allocation.text(),
            "max_context": self.max_context.text(),
            "layer_distribution": self.layer_distribution.text(),
        }

        # Emit signal with configuration
        self.settings_applied.emit(config)

        self.status_label.setText("Settings applied to launcher")

    @Slot(dict)
    def apply_preset(self, preset_data: Dict[str, Any]):
        """Apply preset data to the optimizer tab

        Args:
            preset_data: Dictionary containing preset configuration
        """
        try:
            # Extract settings from preset
            if not preset_data:
                self.status_label.setText("Error: Empty preset data")
                return

            logger.info(f"Applying preset: {preset_data.get('name', 'Unknown')}")
            
            # Extract model information - support both formats
            model_name = preset_data.get("model_name", preset_data.get("model", ""))
            if model_name:
                index = self.model_combo.findText(model_name)
                if index >= 0:
                    self.model_combo.setCurrentIndex(index)
                else:
                    logger.warning(f"Model {model_name} not found in combo box")

            # Extract context size
            context_size = preset_data.get("context_size", 0)
            if isinstance(context_size, str) and context_size.isdigit():
                context_size = int(context_size)
            if context_size > 0:
                self.context_size.setValue(context_size)

            # Extract framework
            framework = preset_data.get("framework", "")
            if framework:
                index = self.framework_combo.findText(framework)
                if index >= 0:
                    self.framework_combo.setCurrentIndex(index)

            # Extract precision
            precision = preset_data.get("precision", "")
            if precision:
                index = self.precision_combo.findText(precision)
                if index >= 0:
                    self.precision_combo.setCurrentIndex(index)

            # Update command if present
            command = preset_data.get("command", "")
            if command:
                self.command_text.setText(command)
                self.apply_btn.setEnabled(True)

            # Extract other settings if present
            gpu_settings = preset_data.get("gpu_settings", {})
            if gpu_settings:
                gpu0 = gpu_settings.get("gpu0_allocation", "")
                gpu1 = gpu_settings.get("gpu1_allocation", "")
                max_ctx = gpu_settings.get("max_context", "")
                layer_dist = gpu_settings.get("layer_distribution", "")

                if gpu0:
                    self.gpu0_allocation.setText(gpu0)
                if gpu1:
                    self.gpu1_allocation.setText(gpu1)
                if max_ctx:
                    self.max_context.setText(str(max_ctx))
                if layer_dist:
                    self.layer_distribution.setText(layer_dist)

            # Auto-calculate if no command was provided
            if not command:
                self._calculate_config()

            self.status_label.setText(f"Applied preset: {preset_data.get('name', 'Unknown')}")

        except Exception as e:
            logger.error(f"Error applying preset: {e}")
            self.status_label.setText(f"Error applying preset: {e}")

    def save_preset(self):
        """Save current configuration as a preset"""
        try:
            from dualgpuopt.services.presets import PresetManager
            from PySide6.QtWidgets import QInputDialog

            name, ok = QInputDialog.getText(self, "Save Preset", "Enter preset name:")

            if ok and name:
                # Create preset data with a consistent format for all components
                preset_data = {
                    "name": name,
                    "type": "optimizer",
                    "model_name": self.model_combo.currentText(),
                    "model_path": "",  # Will be set by launcher if available
                    "context_size": self.context_size.value(),
                    "framework": self.framework_combo.currentText(),
                    "precision": self.precision_combo.currentText(),
                    "command": self.command_text.toPlainText(),
                    "gpu_settings": {
                        "gpu0_allocation": self.gpu0_allocation.text(),
                        "gpu1_allocation": self.gpu1_allocation.text(),
                        "max_context": self.max_context.text(),
                        "layer_distribution": self.layer_distribution.text(),
                    },
                    "prompt_template": "",  # For chat components
                    "persona": "",          # For chat components
                }

                # Save preset
                manager = PresetManager()
                manager.save_preset(name, preset_data)

                self.status_label.setText(f"Preset '{name}' saved successfully")
        except Exception as e:
            logger.error(f"Error saving preset: {e}")
            self.status_label.setText(f"Error saving preset: {e}")
