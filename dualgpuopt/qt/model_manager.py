"""
Model Manager tab for searching, downloading, and managing ML models.
"""
from __future__ import annotations

import logging
import pathlib

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from dualgpuopt.engine.pool import EnginePool
from dualgpuopt.gpu.info import query as gpu_query
from dualgpuopt.model.hf_client import download, search
from dualgpuopt.model.quantise import to_awq, to_gguf
from dualgpuopt.model.vram_fit import fit_plan

logger = logging.getLogger(__name__)


class DownloadThread(QThread):
    """Thread for downloading models without blocking the UI."""

    progress = Signal(int, int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, model_id: str, pattern: str, dest: pathlib.Path):
        super().__init__()
        self.model_id = model_id
        self.pattern = pattern
        self.dest = dest

    def run(self):
        try:
            result = download(
                self.model_id,
                self.pattern,
                self.dest,
                lambda current, total: self.progress.emit(current, total),
            )
            self.finished.emit(str(result))
        except Exception as e:
            self.error.emit(str(e))


class QuantThread(QThread):
    """Thread for quantizing models without blocking the UI."""

    progress = Signal(str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, source_path: pathlib.Path, method: str):
        super().__init__()
        self.source_path = source_path
        self.method = method

    def run(self):
        try:
            self.progress.emit(f"Starting {self.method} quantization...")
            if self.method == "awq":
                result = to_awq(self.source_path)
            elif self.method == "gguf":
                result = to_gguf(self.source_path)
            else:
                raise ValueError(f"Unknown quantization method: {self.method}")
            self.finished.emit(str(result))
        except Exception as e:
            self.error.emit(str(e))


class ModelManager(QWidget):
    """Tab for searching, downloading, and managing ML models."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.models = []
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)

        # Search controls
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for models (e.g., 'mistral', 'llama')")
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self._search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        # Results table
        self.res = QTableWidget(0, 7)
        self.res.setHorizontalHeaderLabels(["Model", "DLs", "Size GB", "Plan", "VRAM", "Disk", ""])
        self.res.setSelectionBehavior(QTableWidget.SelectRows)
        self.res.setEditTriggers(QTableWidget.NoEditTriggers)
        self.res.verticalHeader().setVisible(False)
        self.res.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.res)

        # Auto-load checkbox
        self.auto = QCheckBox("Auto-load after download")
        self.auto.setChecked(True)
        layout.addWidget(self.auto)

        # Progress area
        progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout(progress_group)
        self.progress_label = QLabel("No download in progress")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        layout.addWidget(progress_group)

        # Local models
        local_group = QGroupBox("Local Models")
        local_layout = QVBoxLayout(local_group)

        # Local controls
        local_buttons = QHBoxLayout()
        self.local_dir = QLineEdit()
        self.local_dir.setPlaceholderText("Directory containing model files")
        self.local_dir.setText(str(pathlib.Path.home() / "models"))
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._scan_local)
        local_buttons.addWidget(self.local_dir)
        local_buttons.addWidget(self.browse_btn)
        local_buttons.addWidget(self.refresh_btn)
        local_layout.addLayout(local_buttons)

        # Local models table
        self.local_models = QTableWidget(0, 4)
        self.local_models.setHorizontalHeaderLabels(["File", "Size", "Type", "Actions"])
        self.local_models.setSelectionBehavior(QTableWidget.SelectRows)
        self.local_models.setEditTriggers(QTableWidget.NoEditTriggers)
        self.local_models.verticalHeader().setVisible(False)
        self.local_models.horizontalHeader().setStretchLastSection(True)
        local_layout.addWidget(self.local_models)

        # Quantization controls
        quant_layout = QHBoxLayout()
        self.quant_method = QComboBox()
        self.quant_method.addItems(["awq", "gguf"])
        self.quant_btn = QPushButton("Quantize Selected")
        self.quant_btn.clicked.connect(self._quantize)
        quant_layout.addWidget(QLabel("Method:"))
        quant_layout.addWidget(self.quant_method)
        quant_layout.addWidget(self.quant_btn)
        quant_layout.addStretch()
        local_layout.addLayout(quant_layout)

        layout.addWidget(local_group)

        # Set up initial state
        try:
            model_dir = pathlib.Path(self.local_dir.text())
            model_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Could not create models directory: {e}")

        self.search_input.setFocus()

    def _search(self):
        """Search for models based on user input."""
        query = self.search_input.text().strip()
        if not query:
            return

        self.search_btn.setEnabled(False)
        self.search_btn.setText("Searching...")

        try:
            self.models = search(query)
            self.res.setRowCount(len(self.models))

            for r, m in enumerate(self.models):
                self.res.setItem(r, 0, QTableWidgetItem(m["id"]))

                if m["downloads"] is not None:
                    dl_item = QTableWidgetItem(f"{m['downloads']:,}")
                    dl_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.res.setItem(r, 1, dl_item)

                if m["size"] is not None:
                    size_gb = m["size"] / 1_073_741_824  # Convert to GB
                    size_item = QTableWidgetItem(f"{size_gb:.1f}")
                    size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.res.setItem(r, 2, size_item)

                    plan = fit_plan(m["size"] or 1 << 30, gpu_query())
                    self.res.setItem(r, 3, QTableWidgetItem(plan.get("quant", "N/A")))

                    vram_item = QTableWidgetItem(
                        f"GPU: {plan.get('gpu_layers', 'All')}"
                        if plan.get("quant") == "gguf"
                        else "All GPU"
                        if not plan.get("device_map")
                        else "Split",
                    )
                    self.res.setItem(r, 4, vram_item)

                    disk = "✓" if plan.get("disk") else "—"
                    self.res.setItem(r, 5, QTableWidgetItem(disk))

                btn = QPushButton("Download")
                btn.clicked.connect(
                    lambda _, idx=r: self._download(
                        self.models[idx]["id"],
                        fit_plan(self.models[idx]["size"] or 1 << 30, gpu_query()),
                    )
                )
                self.res.setCellWidget(r, 6, btn)

            self.res.resizeColumnsToContents()

        except Exception as e:
            logger.error(f"Search error: {e}")
            QMessageBox.warning(self, "Search Error", f"Error searching for models: {e}")

        finally:
            self.search_btn.setEnabled(True)
            self.search_btn.setText("Search")

    def _download(self, model_id: str, plan: dict):
        """Download a model and optionally quantize it."""
        try:
            fmt = plan["quant"]
            pattern = ".gguf" if fmt == "gguf" else ".safetensors"

            # Check for existing models first
            model_dir = pathlib.Path(self.local_dir.text())
            model_dir.mkdir(parents=True, exist_ok=True)

            # Start download in a separate thread
            self.dl_thread = DownloadThread(model_id, pattern, model_dir)
            self.dl_thread.progress.connect(self._update_progress)
            self.dl_thread.finished.connect(lambda path: self._download_finished(path, plan))
            self.dl_thread.error.connect(self._download_error)

            self.progress_bar.setVisible(True)
            self.progress_label.setText(f"Downloading {model_id}...")
            self.dl_thread.start()

        except Exception as e:
            logger.error(f"Download error: {e}")
            QMessageBox.warning(self, "Download Error", f"Error starting download: {e}")

    @Slot(int, int)
    def _update_progress(self, current: int, total: int):
        """Update the progress bar with download progress."""
        percent = int(current * 100 / total) if total else 0
        self.progress_bar.setValue(percent)
        self.progress_label.setText(
            f"Downloaded: {current/(1024*1024):.1f} MB / {total/(1024*1024):.1f} MB ({percent}%)"
        )

    @Slot(str)
    def _download_finished(self, path: str, plan: dict):
        """Handle completed download."""
        self.progress_bar.setVisible(False)
        self.progress_label.setText(f"Download complete: {path}")
        QMessageBox.information(self, "Download Complete", f"Successfully downloaded to {path}")

        # Scan local directory to refresh list
        self._scan_local()

        # Auto-load if selected
        local = pathlib.Path(path)
        if local.exists():
            if self.auto.isChecked():
                try:
                    EnginePool.get(str(local), **plan)
                    self.progress_label.setText(f"Loaded {local.name} into engine pool")
                except Exception as e:
                    logger.error(f"Auto-load error: {e}")
                    self.progress_label.setText(f"Error loading model: {e}")

    @Slot(str)
    def _download_error(self, error_msg: str):
        """Handle download error."""
        self.progress_bar.setVisible(False)
        self.progress_label.setText(f"Download failed: {error_msg}")
        QMessageBox.warning(self, "Download Error", f"Download failed: {error_msg}")

    def _browse(self):
        """Open a folder browser dialog to select model directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Models Directory", self.local_dir.text()
        )
        if directory:
            self.local_dir.setText(directory)
            self._scan_local()

    def _scan_local(self):
        """Scan local directory for model files."""
        try:
            model_dir = pathlib.Path(self.local_dir.text())
            if not model_dir.exists():
                model_dir.mkdir(parents=True, exist_ok=True)
                return

            files = []
            for ext in ("*.gguf", "*.bin", "*.safetensors"):
                files.extend(model_dir.glob(f"**/{ext}"))

            self.local_models.setRowCount(len(files))

            for r, file in enumerate(files):
                rel_path = file.relative_to(model_dir)
                self.local_models.setItem(r, 0, QTableWidgetItem(str(rel_path)))

                size_mb = file.stat().st_size / 1_048_576
                size_item = QTableWidgetItem(f"{size_mb:.1f} MB")
                size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.local_models.setItem(r, 1, size_item)

                ext = file.suffix.lower()
                if "awq" in file.name.lower() and ext == ".safetensors":
                    model_type = "AWQ"
                elif ext == ".gguf":
                    model_type = "GGUF"
                elif ext == ".safetensors":
                    model_type = "FP16"
                elif ext == ".bin":
                    model_type = "HF Bin"
                else:
                    model_type = ext
                self.local_models.setItem(r, 2, QTableWidgetItem(model_type))

                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)

                load_btn = QPushButton("Load")
                load_btn.clicked.connect(lambda _, f=file: self._load_model(f))
                actions_layout.addWidget(load_btn)

                self.local_models.setCellWidget(r, 3, actions_widget)

            self.local_models.resizeColumnsToContents()

        except Exception as e:
            logger.error(f"Scan error: {e}")
            QMessageBox.warning(self, "Scan Error", f"Error scanning model directory: {e}")

    def _load_model(self, file_path: pathlib.Path):
        """Load a model into the engine pool."""
        try:
            size_bytes = file_path.stat().st_size
            plan = fit_plan(size_bytes, gpu_query())

            EnginePool.get(str(file_path), **plan)
            self.progress_label.setText(f"Loaded {file_path.name} into engine pool")
            QMessageBox.information(self, "Model Loaded", f"Successfully loaded {file_path.name}")

        except Exception as e:
            logger.error(f"Load error: {e}")
            QMessageBox.warning(self, "Load Error", f"Error loading model: {e}")

    def _quantize(self):
        """Quantize the selected model file."""
        selected = self.local_models.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a model to quantize")
            return

        try:
            model_name = selected[0].text()
            model_dir = pathlib.Path(self.local_dir.text())
            model_path = model_dir / model_name

            method = self.quant_method.currentText()

            # Check if appropriate format
            if method == "awq" and model_path.suffix != ".safetensors":
                QMessageBox.warning(
                    self, "Format Error", "AWQ quantization requires a .safetensors model"
                )
                return

            if method == "gguf" and not (
                model_path.suffix == ".safetensors" or model_path.suffix == ".bin"
            ):
                QMessageBox.warning(
                    self,
                    "Format Error",
                    "GGUF quantization requires HF model (.safetensors or .bin)",
                )
                return

            # Start quantization in a thread
            self.quant_thread = QuantThread(model_path, method)
            self.quant_thread.progress.connect(self.progress_label.setText)
            self.quant_thread.finished.connect(self._quant_finished)
            self.quant_thread.error.connect(self._quant_error)

            self.progress_bar.setVisible(False)
            self.progress_label.setText(f"Quantizing {model_path.name} to {method}...")
            self.quant_thread.start()

        except Exception as e:
            logger.error(f"Quantization error: {e}")
            QMessageBox.warning(self, "Quantization Error", f"Error starting quantization: {e}")

    @Slot(str)
    def _quant_finished(self, path: str):
        """Handle completed quantization."""
        self.progress_label.setText(f"Quantization complete: {path}")
        QMessageBox.information(self, "Quantization Complete", f"Successfully created {path}")
        self._scan_local()

    @Slot(str)
    def _quant_error(self, error_msg: str):
        """Handle quantization error."""
        self.progress_label.setText(f"Quantization failed: {error_msg}")
        QMessageBox.warning(self, "Quantization Error", f"Quantization failed: {error_msg}")
