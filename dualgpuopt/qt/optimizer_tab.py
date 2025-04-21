import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QComboBox, QPushButton, QGroupBox, QFormLayout,
                              QSpinBox, QDoubleSpinBox, QTextEdit, QSpacerItem,
                              QSizePolicy, QCheckBox, QMessageBox)
from PySide6.QtCore import Slot
from PySide6.QtGui import QFont

logger = logging.getLogger('DualGPUOptimizer')

class OptimizerTab(QWidget):
    """Optimizer tab for calculating optimal GPU configs."""

    def __init__(self, mock_mode=False):
        super().__init__()
        self.mock_mode = mock_mode
        self.logger = logging.getLogger('DualGPUOptimizer')
        self.logger.info("Initializing Optimizer tab")

        # Model configurations
        self.model_configs = {
            "llama2-7b": {
                "parameters": 7,
                "layers": 32,
                "heads": 32,
                "dims": 4096
            },
            "llama2-13b": {
                "parameters": 13,
                "layers": 40,
                "heads": 40,
                "dims": 5120
            },
            "llama3-8b": {
                "parameters": 8,
                "layers": 32,
                "heads": 32,
                "dims": 4096
            },
            "llama3-70b": {
                "parameters": 70,
                "layers": 80,
                "heads": 64,
                "dims": 8192
            },
            "mistral-7b": {
                "parameters": 7,
                "layers": 32,
                "heads": 32,
                "dims": 4096
            },
            "mixtral-8x7b": {
                "parameters": 47,
                "layers": 32,
                "heads": 32,
                "dims": 4096,
                "moe": True
            }
        }

        # Context lengths
        self.context_options = ["2k", "4k", "8k", "16k", "32k", "64k", "128k"]

        # Precision options
        self.precision_options = ["float16", "bfloat16", "int8", "int4"]

        # Default GPU memory values (MB)
        self.gpu_memory = [12288, 12288]  # Default to 12GB for each GPU

        self.setup_ui()

    def setup_ui(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header_layout = QHBoxLayout()

        # Title
        title = QLabel("GPU Optimizer")
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
        desc_label = QLabel("Calculate optimal GPU configurations for large language models")
        desc_label.setStyleSheet("color: #A0A0A0;")
        main_layout.addWidget(desc_label)

        # Content layout with two columns
        content_layout = QHBoxLayout()

        # Left column - Input parameters
        left_column = QVBoxLayout()

        # Model selection group
        model_group = QGroupBox("Model Selection")
        model_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #3D2A50;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        model_layout = QFormLayout(model_group)
        model_layout.setSpacing(10)

        # Model dropdown
        self.model_combo = QComboBox()
        for model in self.model_configs.keys():
            self.model_combo.addItem(model)
        self.model_combo.currentTextChanged.connect(self.update_model_params)
        model_layout.addRow("Model:", self.model_combo)

        # Context length
        self.context_combo = QComboBox()
        for ctx in self.context_options:
            self.context_combo.addItem(ctx)
        self.context_combo.setCurrentText("8k")  # Default to 8k
        model_layout.addRow("Context Length:", self.context_combo)

        # Precision
        self.precision_combo = QComboBox()
        for prec in self.precision_options:
            self.precision_combo.addItem(prec)
        model_layout.addRow("Precision:", self.precision_combo)

        left_column.addWidget(model_group)

        # Model parameters group
        params_group = QGroupBox("Model Parameters")
        params_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #3D2A50;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        params_layout = QFormLayout(params_group)
        params_layout.setSpacing(10)

        # Parameter fields
        self.param_billion = QDoubleSpinBox()
        self.param_billion.setRange(0.1, 200)
        self.param_billion.setValue(7)
        self.param_billion.setSingleStep(0.1)
        self.param_billion.setDecimals(1)
        self.param_billion.setSuffix(" B")
        params_layout.addRow("Parameters:", self.param_billion)

        self.param_layers = QSpinBox()
        self.param_layers.setRange(1, 200)
        self.param_layers.setValue(32)
        params_layout.addRow("Layers:", self.param_layers)

        self.param_heads = QSpinBox()
        self.param_heads.setRange(1, 128)
        self.param_heads.setValue(32)
        params_layout.addRow("Heads:", self.param_heads)

        self.param_dims = QSpinBox()
        self.param_dims.setRange(128, 16384)
        self.param_dims.setValue(4096)
        self.param_dims.setSingleStep(128)
        params_layout.addRow("Hidden Size:", self.param_dims)

        self.param_moe = QCheckBox("Mixture of Experts")
        params_layout.addRow("", self.param_moe)

        left_column.addWidget(params_group)

        # Calculate button
        self.calculate_button = QPushButton("Calculate Optimal Configuration")
        self.calculate_button.clicked.connect(self.calculate_configuration)
        left_column.addWidget(self.calculate_button)

        # Add left column to content layout
        content_layout.addLayout(left_column)

        # Right column - Results
        right_column = QVBoxLayout()

        # Results group
        results_group = QGroupBox("Results")
        results_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #3D2A50;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        results_layout = QVBoxLayout(results_group)
        results_layout.setSpacing(12)

        # GPU memory ratio
        ratio_layout = QHBoxLayout()
        ratio_layout.addWidget(QLabel("GPU Memory Split:"))

        self.ratio_label = QLabel("50% / 50%")
        self.ratio_label.setStyleSheet("font-weight: bold; color: #8A54FD;")
        ratio_layout.addWidget(self.ratio_label)

        ratio_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        results_layout.addLayout(ratio_layout)

        # Output text area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #241934;
                border: 1px solid #3D2A50;
                border-radius: 4px;
                padding: 8px;
                font-family: Consolas, monospace;
            }
        """)
        self.output_text.setMinimumHeight(300)
        results_layout.addWidget(self.output_text)

        # Command generation section
        cmd_layout = QHBoxLayout()

        # Command type
        self.cmd_type_combo = QComboBox()
        self.cmd_type_combo.addItems(["llama.cpp", "vLLM"])
        cmd_layout.addWidget(self.cmd_type_combo)

        # Generate button
        self.generate_cmd_button = QPushButton("Generate Command")
        self.generate_cmd_button.clicked.connect(self.generate_command)
        cmd_layout.addWidget(self.generate_cmd_button)

        # Add Apply to Launcher button
        self.apply_button = QPushButton("Apply to Launcher")
        self.apply_button.clicked.connect(self.apply_to_launcher)

        cmd_layout.addWidget(self.apply_button)

        results_layout.addLayout(cmd_layout)

        right_column.addWidget(results_group)

        # Add right column to content layout
        content_layout.addLayout(right_column)

        # Set the stretch factors for the columns
        content_layout.setStretch(0, 4)  # Left column
        content_layout.setStretch(1, 6)  # Right column

        # Add content layout to main layout
        main_layout.addLayout(content_layout)

        # Initialize model parameters
        self.update_model_params(self.model_combo.currentText())

        self.logger.info("Optimizer UI setup complete")

    @Slot(str)
    def update_model_params(self, model_name):
        """Update model parameter fields based on selected model."""
        if model_name in self.model_configs:
            config = self.model_configs[model_name]
            self.param_billion.setValue(config["parameters"])
            self.param_layers.setValue(config["layers"])
            self.param_heads.setValue(config["heads"])
            self.param_dims.setValue(config["dims"])

            if "moe" in config:
                self.param_moe.setChecked(config["moe"])
            else:
                self.param_moe.setChecked(False)

            self.logger.info(f"Updated model parameters for {model_name}")

    @Slot()
    def calculate_configuration(self):
        """Calculate the optimal GPU configuration."""
        try:
            self.logger.info("Calculating GPU configuration")

            # Get model parameters
            params_billion = self.param_billion.value()
            layers = self.param_layers.value()
            heads = self.param_heads.value()
            dims = self.param_dims.value()
            self.param_moe.isChecked()
            context_text = self.context_combo.currentText()
            precision = self.precision_combo.currentText()

            # Convert context text to size
            context_map = {
                "2k": 2048, "4k": 4096, "8k": 8192, "16k": 16384,
                "32k": 32768, "64k": 65536, "128k": 131072
            }
            context_size = context_map.get(context_text, 8192)

            # Get current GPU memory values
            if hasattr(self, 'gpu_memory') and len(self.gpu_memory) >= 2:
                gpu1_mem = self.gpu_memory[0]
                gpu2_mem = self.gpu_memory[1]
            else:
                gpu1_mem = 12288  # Default to 12GB
                gpu2_mem = 12288

            # Calculate optimal split ratio based on GPU memory
            total_mem = gpu1_mem + gpu2_mem

            if total_mem > 0:
                # Simple ratio calculation - in a real implementation this would be more complex
                gpu1_ratio = gpu1_mem / total_mem
                gpu2_ratio = gpu2_mem / total_mem

                # Format ratio as percentages
                ratio_str = f"{gpu1_ratio:.1%} / {gpu2_ratio:.1%}"
                self.ratio_label.setText(ratio_str)

                # Memory per token calculation (simplified)
                bytes_per_param = 2  # for float16/bfloat16
                if precision == "int8":
                    bytes_per_param = 1
                elif precision == "int4":
                    bytes_per_param = 0.5

                # Calculate memory requirements
                model_size_mb = params_billion * 1000 * bytes_per_param

                # KV cache per token (simplified calculation)
                kv_cache_per_token = 2 * heads * (dims // heads) * bytes_per_param / (1024 * 1024)

                # Total KV cache
                total_kv_cache = kv_cache_per_token * context_size

                # Generate summary
                summary = (
                    f"Model Parameters: {params_billion:.1f} billion\n"
                    f"Model Size: {model_size_mb:.0f} MB\n"
                    f"Layers: {layers}\n"
                    f"Context Length: {context_size}\n"
                    f"KV Cache (per token): {kv_cache_per_token:.3f} MB\n"
                    f"Total KV Cache: {total_kv_cache:.0f} MB\n\n"
                    f"GPU 0: {gpu1_mem} MB available\n"
                    f"GPU 1: {gpu2_mem} MB available\n\n"
                    f"Recommended Configuration:\n"
                    f"Memory Split: {ratio_str}\n"
                )

                # Tensor parallel recommendation
                tp_size = 2 if model_size_mb > min(gpu1_mem, gpu2_mem) * 0.8 else 1
                summary += f"Tensor Parallel Size: {tp_size}\n"

                # Layer distribution
                if tp_size == 1 and layers > 1:
                    # Calculate layers per GPU for non-TP mode
                    gpu1_layers = int(layers * gpu1_ratio)
                    gpu2_layers = layers - gpu1_layers
                    summary += f"Layer Distribution: {gpu1_layers} layers on GPU 0, {gpu2_layers} layers on GPU 1\n"

                # Max batch size (simplified)
                max_batch_tokens = min(
                    (gpu1_mem * 0.8 - (model_size_mb * gpu1_ratio)) / kv_cache_per_token,
                    (gpu2_mem * 0.8 - (model_size_mb * gpu2_ratio)) / kv_cache_per_token
                )

                max_batch = max(1, int(max_batch_tokens / context_size))
                summary += f"Estimated Max Batch Size: {max_batch}\n"

                # Update output text
                self.output_text.setText(summary)
                self.logger.info("Configuration calculated successfully")

            else:
                self.logger.error("Total GPU memory is zero")
                self.output_text.setText("Error: Could not retrieve valid GPU memory values")

        except Exception as e:
            self.logger.error(f"Error calculating configuration: {e}")
            self.output_text.setText(f"Error calculating configuration: {str(e)}")

    @Slot()
    def generate_command(self):
        """Generate command for selected framework."""
        try:
            framework = self.cmd_type_combo.currentText()
            model_name = self.model_combo.currentText()
            context_text = self.context_combo.currentText()
            precision = self.precision_combo.currentText()

            # Convert context text to size
            context_map = {
                "2k": 2048, "4k": 4096, "8k": 8192, "16k": 16384,
                "32k": 32768, "64k": 65536, "128k": 131072
            }
            context_size = context_map.get(context_text, 8192)

            # Get split ratio
            ratio_text = self.ratio_label.text().replace("%", "").split("/")
            gpu1_ratio = float(ratio_text[0].strip()) / 100
            gpu2_ratio = float(ratio_text[1].strip()) / 100

            command = ""

            if framework == "llama.cpp":
                # Simplified command for llama.cpp
                gpu_split = f"{gpu1_ratio:.1f},{gpu2_ratio:.1f}"

                command = (
                    f"./llama -m ./models/{model_name}.gguf \\\n"
                    f"  --ctx-size {context_size} \\\n"
                    f"  --gpu-layers 999 \\\n"
                    f"  --split-mode layer \\\n"
                    f"  --tensor-split {gpu_split} \\\n"
                    f"  --main-gpu 0 \\\n"
                    f"  --threads 8"
                )

                # Add quantization parameter if using int4 or int8
                if precision in ["int4", "int8"]:
                    command += f" \\\n  --{precision}"

            elif framework == "vLLM":
                # Simplified command for vLLM
                command = (
                    f"python -m vllm.entrypoints.api_server \\\n"
                    f"  --model {model_name} \\\n"
                    f"  --tensor-parallel-size 2 \\\n"
                    f"  --max-model-len {context_size} \\\n"
                    f"  --gpu-memory-utilization 0.8"
                )

                # Add dtype parameter
                dtype_map = {
                    "float16": "float16",
                    "bfloat16": "bfloat16",
                    "int8": "int8",
                    "int4": "int4"
                }

                command += f" \\\n  --dtype {dtype_map.get(precision, 'float16')}"

            # Update output text with command
            current_text = self.output_text.toPlainText()
            self.output_text.setText(f"{current_text}\n\n# {framework} Command:\n{command}")

            self.logger.info(f"Generated {framework} command")

        except Exception as e:
            self.logger.error(f"Error generating command: {e}")

            # Add error to output text
            current_text = self.output_text.toPlainText()
            self.output_text.setText(f"{current_text}\n\nError generating command: {str(e)}")

    @Slot()
    def apply_to_launcher(self):
        """Apply optimization settings directly to the launcher tab."""
        try:
            # Get current settings
            framework = self.cmd_type_combo.currentText()
            model_name = self.model_combo.currentText()

            if not model_name:
                QMessageBox.warning(self, "Missing Information", "Please enter a model name first.")
                return

            # Calculate split ratio based on GPU memory values
            if len(self.gpu_memory) >= 2:
                gpu1_mem = self.gpu_memory[0]
                gpu2_mem = self.gpu_memory[1]

                total_mem = gpu1_mem + gpu2_mem
                gpu1_ratio = gpu1_mem / total_mem
                gpu2_ratio = gpu2_mem / total_mem
            else:
                # Fallback if GPU info not available
                gpu1_ratio = 0.6
                gpu2_ratio = 0.4

            # Get context size
            context_text = self.context_combo.currentText()
            context_map = {
                "2k": 2048, "4k": 4096, "8k": 8192, "16k": 16384,
                "32k": 32768, "64k": 65536, "128k": 131072
            }
            context_size = context_map.get(context_text, 8192)

            # Get precision
            precision = self.precision_combo.currentText()

            # Create settings dictionary to send to launcher
            settings = {
                "framework": framework,
                "model_name": model_name,
                "context_size": context_size,
                "precision": precision,
                "gpu_split": f"{gpu1_ratio:.1f},{gpu2_ratio:.1f}",
                "tensor_parallel_size": 2 if len(self.gpu_memory) >= 2 else 1
            }

            # Use Qt's event system to communicate with launcher tab
            from dualgpuopt.services.event_service import event_bus
            event_bus.publish("optimizer_settings", settings)

            # Show confirmation
            QMessageBox.information(self, "Settings Applied",
                                   f"Optimization settings for {model_name} have been applied to the launcher tab.")

            self.logger.info(f"Applied optimizer settings to launcher: {settings}")

        except Exception as e:
            self.logger.error(f"Error applying settings to launcher: {e}")
            QMessageBox.warning(self, "Error", f"Error applying settings to launcher: {e}")

    def update_gpu_memory(self, metrics_list):
        """Update GPU memory values from metrics."""
        if not metrics_list or len(metrics_list) < 2:
            return

        # Update GPU memory values from metrics
        self.gpu_memory = [
            metrics_list[0].get("memory_total", 12288),
            metrics_list[1].get("memory_total", 12288)
        ]

        self.logger.info(f"Updated GPU memory values: {self.gpu_memory[0]}MB, {self.gpu_memory[1]}MB")