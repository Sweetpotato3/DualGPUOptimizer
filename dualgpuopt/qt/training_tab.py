from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QComboBox, QSpinBox, QPlainTextEdit, QProgressBar
)
from PySide6.QtCore import Signal, Slot, Qt

from dualgpuopt.qt.shared_constants import PAD
from dualgpuopt.qt.workers.trainer_worker import TrainerWorker

class TrainingTab(QWidget):
    train_started = Signal()
    train_finished = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker: TrainerWorker | None = None
        self._setup_ui()

    # --------------------------------------------------------- UI
    def _setup_ui(self):
        lay = QVBoxLayout(self); lay.setSpacing(PAD)

        # row: model + dataset selectors
        sel = QHBoxLayout(); lay.addLayout(sel)
        sel.addWidget(QLabel("Base model:"))
        self.model_cmb = QComboBox()
        self.model_cmb.addItems(self._discover_models())
        sel.addWidget(self.model_cmb, 1)

        sel.addWidget(QLabel("Dataset:"))
        self.dataset_btn = QPushButton("Browse…", clicked=self._browse_dataset)
        sel.addWidget(self.dataset_btn)
        self.dataset_lbl = QLabel("None"); sel.addWidget(self.dataset_lbl, 2)

        # row: epochs & batch
        row2 = QHBoxLayout(); lay.addLayout(row2)
        row2.addWidget(QLabel("Epochs:"))
        self.ep_spin = QSpinBox(); self.ep_spin.setRange(1, 10); self.ep_spin.setValue(3)
        row2.addWidget(self.ep_spin)
        row2.addWidget(QLabel("Batch per GPU:"))
        self.bs_spin = QSpinBox(); self.bs_spin.setRange(1, 256); self.bs_spin.setValue(32)
        row2.addWidget(self.bs_spin)

        # progress + metrics
        self.prog = QProgressBar(); lay.addWidget(self.prog)
        self.metrics = QLabel("tokens/s: –  loss: –"); lay.addWidget(self.metrics)

        # log pane
        self.log = QPlainTextEdit(readOnly=True); lay.addWidget(self.log, 2)

        # start/stop
        btn_row = QHBoxLayout(); lay.addLayout(btn_row)
        self.start_btn = QPushButton("Start", clicked=self._start)
        self.stop_btn  = QPushButton("Stop",  clicked=self._stop)
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.start_btn); btn_row.addWidget(self.stop_btn)

    # --------------------------------------------------------- actions
    def _discover_models(self):
        favs = ["mistralai/Mistral-7B-Instruct", "TheBloke/dolphin-2.2-yi-34b-200k-AWQ"]
        local = [p.name for p in Path("models").glob("*") if p.is_dir()]
        return favs + local

    def _browse_dataset(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Choose JSONL dataset",
                                            "datasets", "JSONL (*.jsonl)")
        if fn: self.dataset_lbl.setText(Path(fn).name); self.dataset_btn.setProperty("path", fn)

    def _start(self):
        model = self.model_cmb.currentText()
        ds    = self.dataset_btn.property("path")
        if not ds:
            self.log.appendPlainText("Dataset not selected!"); return
        self.worker = TrainerWorker(
            base_model=model,
            dataset=ds,
            epochs=self.ep_spin.value(),
            per_device_batch=self.bs_spin.value()
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.log_line.connect(self.log.appendPlainText)
        self.worker.finished.connect(self._on_done)
        self.worker.start()
        self.start_btn.setEnabled(False); self.stop_btn.setEnabled(True)

    def _stop(self): 
        if self.worker: self.worker.request_stop()
        self.stop_btn.setEnabled(False)

    # --------------------------------------------------------- slots
    @Slot(int, float, float)
    def _on_progress(self, pct: int, tok_s: float, loss: float):
        self.prog.setValue(pct)
        self.metrics.setText(f"tokens/s: {tok_s:.1f}   loss: {loss:.3f}")

    @Slot(bool)
    def _on_done(self, ok: bool):
        self.start_btn.setEnabled(True); self.stop_btn.setEnabled(False)
        self.train_finished.emit(ok) 