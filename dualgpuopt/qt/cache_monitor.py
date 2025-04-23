"""
Cache monitor widget for engine pool visualization.
Displays currently loaded models and allows management.
"""

from __future__ import annotations

from PySide6 import QtCore as QtC
from PySide6 import QtWidgets as QtW

# Import shared constants
from dualgpuopt.qt.shared_constants import PAD, DEFAULT_FONT, DEFAULT_FONT_SIZE, UPDATE_INTERVAL_MS

from dualgpuopt.engine.pool.core import EnginePool


class CacheMonitor(QtW.QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Engine Pool", parent)
        self.table = QtW.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Model", "Evict"])
        self.setWidget(self.table)
        self.refresh_btn = QtW.QPushButton("Refresh", clicked=self.refresh)
        self.setTitleBarWidget(self.refresh_btn)
        self.timer = QtC.QTimer(interval=2500, timeout=self.refresh)
        self.timer.start()

    def refresh(self):
        stats = EnginePool.stats()
        self.table.clearContents()
        self.table.setRowCount(len(stats["models"]))
        for r, m in enumerate(stats["models"]):
            self.table.setItem(r, 0, QtW.QTableWidgetItem(str(m)))
            btn = QtW.QPushButton("Evict", clicked=lambda _, p=m: self._evict(p))
            self.table.setCellWidget(r, 1, btn)

    def _evict(self, path):
        EnginePool.evict(path)
