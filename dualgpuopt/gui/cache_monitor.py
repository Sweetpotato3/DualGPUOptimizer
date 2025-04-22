"""
UI component for monitoring and controlling the EnginePool cache.
Displays statistics, loaded models, and provides controls for managing the cache.
"""

from __future__ import annotations

import logging
import subprocess
import threading
from typing import List

try:
    from PySide6.QtCore import QTimer, Signal, Slot
    from PySide6.QtWidgets import (
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QSpinBox,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    UI_AVAILABLE = True
except ImportError:
    logging.warning("PySide6 not available, CacheMonitorWidget will not be functional")
    UI_AVAILABLE = False

    # Create dummy base classes for type checking
    class QWidget:
        pass

    class Signal:
        pass

    class Slot:
        pass


from dualgpuopt.engine.pool import EnginePool


class CacheMonitorWidget(QWidget if UI_AVAILABLE else object):
    """Widget for monitoring and controlling the EnginePool cache."""

    # Signals
    cache_cleared = Signal() if UI_AVAILABLE else None
    model_evicted = Signal(str) if UI_AVAILABLE else None

    def __init__(self, parent=None):
        """Initialize the cache monitor widget."""
        if not UI_AVAILABLE:
            return

        super().__init__(parent)

        self.logger = logging.getLogger("DualGPUOpt.CacheMonitor")
        self.logger.info("Initializing CacheMonitorWidget")

        # Set up UI
        self._setup_ui()

        # Start update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_stats)
        self.timer.start(2000)  # Update every 2 seconds

        # Initial update
        self._update_stats()

    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # Stats group
        stats_group = QGroupBox("Cache Statistics")
        stats_layout = QVBoxLayout(stats_group)

        # Cache size progress
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Cache size:"))
        self.cache_progress = QProgressBar()
        self.cache_progress.setTextVisible(True)
        self.cache_progress.setMinimum(0)
        self.cache_progress.setMaximum(EnginePool._cache.max_size)
        size_layout.addWidget(self.cache_progress)

        # Max size control
        size_layout.addWidget(QLabel("Max:"))
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setMinimum(1)
        self.max_size_spin.setMaximum(10)
        self.max_size_spin.setValue(EnginePool._cache.max_size)
        self.max_size_spin.valueChanged.connect(self._on_max_size_changed)
        size_layout.addWidget(self.max_size_spin)

        stats_layout.addLayout(size_layout)

        # Hit rate progress
        hit_layout = QHBoxLayout()
        hit_layout.addWidget(QLabel("Hit rate:"))
        self.hit_rate_progress = QProgressBar()
        self.hit_rate_progress.setTextVisible(True)
        self.hit_rate_progress.setMinimum(0)
        self.hit_rate_progress.setMaximum(100)
        hit_layout.addWidget(self.hit_rate_progress)
        stats_layout.addLayout(hit_layout)

        # Health check info
        health_layout = QHBoxLayout()
        health_layout.addWidget(QLabel("Health checks:"))
        self.health_checks_label = QLabel("0")
        health_layout.addWidget(self.health_checks_label)
        health_layout.addStretch()

        health_layout.addWidget(QLabel("Failures:"))
        self.health_failures_label = QLabel("0")
        health_layout.addWidget(self.health_failures_label)
        health_layout.addStretch()

        health_layout.addWidget(QLabel("Auto-restarts:"))
        self.auto_restarts_label = QLabel("0")
        health_layout.addWidget(self.auto_restarts_label)

        stats_layout.addLayout(health_layout)

        # Loads/unloads
        load_layout = QHBoxLayout()
        load_layout.addWidget(QLabel("Total loads:"))
        self.total_loads_label = QLabel("0")
        load_layout.addWidget(self.total_loads_label)
        load_layout.addStretch()

        load_layout.addWidget(QLabel("Total unloads:"))
        self.total_unloads_label = QLabel("0")
        load_layout.addWidget(self.total_unloads_label)

        stats_layout.addLayout(load_layout)

        main_layout.addWidget(stats_group)

        # Models group
        models_group = QGroupBox("Cached Models")
        models_layout = QVBoxLayout(models_group)

        # Models table
        self.models_table = QTableWidget(0, 4)
        self.models_table.setHorizontalHeaderLabels(
            ["Model", "VRAM (MiB)", "GPU Util (%)", "Actions"]
        )
        self.models_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.models_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.models_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.models_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.models_table.setAlternatingRowColors(True)
        models_layout.addWidget(self.models_table)

        main_layout.addWidget(models_group)

        # Actions group
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout(actions_group)

        # Quantise selected model
        self.quant_btn = QPushButton("Quantise")
        self.quant_btn.clicked.connect(self._quantise_selected)
        actions_layout.addWidget(self.quant_btn)

        # Clear cache button
        self.clear_btn = QPushButton("Clear Cache")
        self.clear_btn.clicked.connect(self._on_clear_cache)
        actions_layout.addWidget(self.clear_btn)

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._update_stats)
        actions_layout.addWidget(self.refresh_btn)

        main_layout.addWidget(actions_group)

    @Slot()
    def _update_stats(self):
        """Update cache statistics display."""
        if not UI_AVAILABLE:
            return

        # Get current stats
        stats = EnginePool.get_stats()

        # Update cache size
        self.cache_progress.setMaximum(stats["max_size"])
        self.cache_progress.setValue(stats["cache_size"])
        self.cache_progress.setFormat(f"{stats['cache_size']}/{stats['max_size']}")

        # Update hit rate
        self.hit_rate_progress.setValue(int(stats["hit_rate"]))
        self.hit_rate_progress.setFormat(
            f"{stats['hit_rate']:.1f}% ({stats['hits']}/{stats['hits'] + stats['misses']})"
        )

        # Update health checks
        self.health_checks_label.setText(str(stats["health_checks"]))
        self.health_failures_label.setText(str(stats["health_failures"]))
        self.auto_restarts_label.setText(str(stats["auto_restarts"]))

        # Update load counts
        self.total_loads_label.setText(str(stats["total_loads"]))
        self.total_unloads_label.setText(str(stats["total_unloads"]))

        # Update models table
        self._update_models_table(stats["models"])

    def _update_models_table(self, models: List[str]):
        """Update the models table with currently cached models."""
        if not UI_AVAILABLE:
            return

        # Clear current items
        self.models_table.setRowCount(0)

        # Add models
        for i, model in enumerate(models):
            self.models_table.insertRow(i)

            # Model name
            name_item = QTableWidgetItem(model)
            self.models_table.setItem(i, 0, name_item)

            # Get performance metrics if available
            try:
                perf = EnginePool.get_model_performance(model)
                vram = f"{perf['memory_used']:.0f}" if perf and "memory_used" in perf else "-"
                util = (
                    f"{perf['gpu_utilization']:.0f}" if perf and "gpu_utilization" in perf else "-"
                )
            except Exception as exc:
                vram = "-"
                util = "-"
                log.debug("Failed to get model performance: %s", exc)

            self.models_table.setItem(i, 1, QTableWidgetItem(vram))
            self.models_table.setItem(i, 2, QTableWidgetItem(util))

            # Create actions widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)

            # Evict button
            evict_btn = QPushButton("Evict")
            evict_btn.setProperty("model_path", model)
            evict_btn.clicked.connect(lambda checked, m=model: self._on_evict_model(m))
            actions_layout.addWidget(evict_btn)

            self.models_table.setCellWidget(i, 3, actions_widget)

    @Slot(int)
    def _on_max_size_changed(self, value: int):
        """Handle max size spin box value change."""
        if not UI_AVAILABLE:
            return

        EnginePool.set_max_size(value)
        self._update_stats()

    @Slot()
    def _on_clear_cache(self):
        """Handle clear cache button click."""
        if not UI_AVAILABLE:
            return

        EnginePool.clear()
        self._update_stats()
        if self.cache_cleared is not None:
            self.cache_cleared.emit()

    @Slot(str)
    def _on_evict_model(self, model_path: str):
        """Handle evict model button click."""
        if not UI_AVAILABLE:
            return

        EnginePool.evict(model_path)
        self._update_stats()
        if self.model_evicted is not None:
            self.model_evicted.emit(model_path)

    @Slot()
    def _quantise_selected(self):
        """Handle quantise button click for selected model."""
        if not UI_AVAILABLE:
            return

        idx = self.models_table.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "No model selected", "Select a model to quantise.")
            return

        model_path = self.models_table.item(idx, 0).text()
        # Fire-and-forget thread to keep UI responsive
        threading.Thread(target=self._run_awq, args=(model_path,), daemon=True).start()

    def _run_awq(self, model_path: str):
        """Run AutoAWQ quantization in a background thread."""
        self.logger.info(f"Quantising {model_path}...")

        # Use environment variable to prevent path traversal
        env = {"HF_HUB_DISABLE_SYMLINKS": "1"}

        cmd = ["python", "-m", "autoawq", "quantize", model_path]
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if proc.returncode != 0:
            self.logger.error(f"Quantization failed: {proc.stderr}")
            return

        self.logger.info("Quantization finished")
