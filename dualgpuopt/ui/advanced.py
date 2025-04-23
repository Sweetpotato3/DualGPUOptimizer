"""
Advanced tools dock with memory timeline visualization.
Hidden by default, accessible via View menu.
"""
from __future__ import annotations

from PySide6 import QtCore as QtC
from PySide6 import QtGui as QtG
from PySide6 import QtWidgets as QtW


class MemoryTimelineWidget(QtW.QWidget):
    """Memory timeline visualization widget"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Memory data
        self.history: list[float] = []
        self.max_points = 300  # Max points to show

        # Grid/axis settings
        self.margin = 40
        self.grid_color = QtG.QColor(60, 60, 60)
        self.text_color = QtG.QColor(200, 200, 200)

        # Configure widget
        self.setMinimumSize(500, 200)

    def add_data_point(self, value: float):
        """Add data point to timeline"""
        self.history.append(value)

        # Keep history bounded
        if len(self.history) > self.max_points:
            self.history = self.history[-self.max_points :]

        self.update()

    def paintEvent(self, event):
        """Paint the timeline"""
        painter = QtG.QPainter(self)
        painter.setRenderHint(QtG.QPainter.Antialiasing)

        # Get widget dimensions
        width = self.width()
        height = self.height()
        plot_width = width - 2 * self.margin
        plot_height = height - 2 * self.margin

        # Background
        painter.fillRect(0, 0, width, height, QtG.QColor(30, 30, 30))

        # Draw grid
        self._draw_grid(painter, self.margin, self.margin, plot_width, plot_height)

        # Draw data if we have any
        if self.history:
            self._draw_data(painter, self.margin, self.margin, plot_width, plot_height)

        # Draw axes
        self._draw_axes(painter, self.margin, self.margin, plot_width, plot_height)

    def _draw_grid(self, painter, x, y, width, height):
        """Draw background grid"""
        painter.setPen(QtG.QPen(self.grid_color, 1, QtC.Qt.DotLine))

        # Horizontal lines
        for i in range(5):
            y_pos = y + i * height / 4
            painter.drawLine(x, y_pos, x + width, y_pos)

        # Vertical lines
        for i in range(6):
            x_pos = x + i * width / 5
            painter.drawLine(x_pos, y, x_pos, y + height)

    def _draw_data(self, painter, x, y, width, height):
        """Draw the memory timeline data"""
        if not self.history:
            return

        # Find min/max for scaling
        min_val = min(self.history)
        max_val = max(self.history)
        range_val = max(max_val - min_val, 1.0)  # Avoid division by zero

        # Scale factor for data
        scale_y = height / range_val

        # Create points for the line
        points = []
        for i, val in enumerate(self.history):
            x_pos = x + i * width / (len(self.history) - 1 if len(self.history) > 1 else 1)
            y_pos = y + height - (val - min_val) * scale_y
            points.append(QtC.QPointF(x_pos, y_pos))

        # Draw line
        painter.setPen(QtG.QPen(QtG.QColor(0, 153, 255), 2))
        if len(points) > 1:
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])

        # Draw points
        painter.setPen(QtG.QPen(QtG.QColor(255, 255, 255), 1))
        painter.setBrush(QtG.QBrush(QtG.QColor(0, 153, 255)))
        for point in points:
            painter.drawEllipse(point, 3, 3)

    def _draw_axes(self, painter, x, y, width, height):
        """Draw axes and labels"""
        painter.setPen(QtG.QPen(self.text_color, 1))

        # Get min/max for labels
        min_val = min(self.history) if self.history else 0
        max_val = max(self.history) if self.history else 100

        # Y-axis labels
        for i in range(5):
            y_pos = y + i * height / 4
            val = max_val - i * (max_val - min_val) / 4
            label = f"{val:.1f} MB"
            text_rect = painter.fontMetrics().boundingRect(label)
            painter.drawText(
                x - text_rect.width() - 5,
                y_pos + text_rect.height() // 2,
                label,
            )

        # X-axis labels (time)
        for i in range(6):
            x_pos = x + i * width / 5
            time_val = len(self.history) * i / 5
            label = f"-{len(self.history) - time_val:.0f}s"
            text_rect = painter.fontMetrics().boundingRect(label)
            painter.drawText(
                x_pos - text_rect.width() // 2,
                y + height + text_rect.height() + 5,
                label,
            )

        # Title
        painter.drawText(
            x + width // 2 - 50,
            y - 10,
            "Memory Usage Timeline",
        )


class AdvancedDock(QtW.QDockWidget):
    """Advanced tools dock with memory timeline"""

    def __init__(self, parent=None):
        super().__init__("Advanced Tools", parent)
        self.setAllowedAreas(QtC.Qt.AllDockWidgetAreas)

        # Main widget
        main_widget = QtW.QWidget()
        layout = QtW.QVBoxLayout(main_widget)

        # Create memory timeline widget
        self.memory_timeline = MemoryTimelineWidget()
        layout.addWidget(self.memory_timeline)

        # Export button
        self.export_btn = QtW.QPushButton("Export PNG")
        self.export_btn.clicked.connect(self._export_png)
        layout.addWidget(self.export_btn)

        # Settings
        self.setWidget(main_widget)

        # Start timer to generate sample data for testing
        self._timer = self.startTimer(1000)

    def timerEvent(self, event):
        """Handle timer event - update with sample data"""
        import random

        # This would be replaced with actual memory measurements
        self.memory_timeline.add_data_point(random.uniform(800, 1200))

    def _export_png(self):
        """Export timeline as PNG image"""
        file_path, _ = QtW.QFileDialog.getSaveFileName(
            self,
            "Save PNG",
            "memory_timeline.png",
            "PNG Files (*.png)",
        )

        if file_path:
            # Capture widget as image
            pixmap = self.memory_timeline.grab()
            pixmap.save(file_path, "PNG")


class AdvancedToolsDock(AdvancedDock):
    """Compatibility alias for AdvancedDock"""

    def set_memory_timeline(self, timeline):
        """Set memory timeline object"""
        self.memory_timeline = timeline
