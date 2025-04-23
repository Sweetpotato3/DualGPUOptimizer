"""
Qt widgets for DualGPUOptimizer GUI.

This module provides specialized widgets for visualizing telemetry data,
GPU metrics, and other components needed for the DualGPUOptimizer GUI.
"""

from __future__ import annotations

import logging
from typing import Optional

import pyqtgraph as pg
from PySide6 import QtCore as QtC
from PySide6 import QtWidgets as QtW

from dualgpuopt.telemetry_history import TelemetrySample, hist

# Import telemetry module if needed for GPUMetrics

# Configure logger
logger = logging.getLogger(__name__)

# Set pyqtgraph global configuration
pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")


class HistoryPlot(pg.PlotWidget):
    """
    Interactive plot with time window selection for telemetry history.

    Features:
    - Shows a time series of a specific metric
    - Provides an interactive region selector for time window filtering
    - Auto-updates when new data arrives via signals
    """

    # Signal emitted when the visible region changes
    region_changed = QtC.Signal(float, float)  # (start_time, end_time)

    def __init__(self, metric: str, parent: Optional[QtW.QWidget] = None):
        """
        Initialize the history plot.

        Args:
        ----
            metric: The metric key to plot from history (e.g., 'vram_0')
            parent: Optional parent widget

        """
        # Create plot with DateAxisItem for time-based x-axis
        super().__init__(parent=parent, axisItems={"bottom": pg.DateAxisItem()})

        # Store parameters
        self.metric = metric

        # Create main data curve
        self.curve = self.plot(
            pen=pg.mkPen("#9B59B6", width=2),  # Purple pen
            symbolBrush="#9B59B6",
            symbolPen="w",
            symbol="o",
            symbolSize=4,
            name=metric,
        )

        # Add region selector for time filtering
        self.region = pg.LinearRegionItem()
        self.region.setZValue(10)  # Put above other plot elements
        self.addItem(self.region)

        # Connect region change to update function
        self.region.sigRegionChanged.connect(self._region_changed)

        # Store full data series
        self._full_data: list[tuple[float, float]] = []

        # Set background/text colors based on theme
        self.setBackground("k")

        # Add legend
        self.addLegend()

        # Set better default viewport limits
        self.setLabel("left", metric)

    def update_series(self, samples: list[TelemetrySample]):
        """
        Update the plot with new telemetry data.

        Args:
        ----
            samples: List of TelemetrySample objects

        """
        if not samples:
            return

        # Convert samples to time series data
        x_values = [sample.timestamp for sample in samples]
        y_values = [sample.value for sample in samples]

        # Store full data series
        self._full_data = list(zip(x_values, y_values))

        # Set region to show last 60 seconds by default
        if len(x_values) > 1:
            last_time = x_values[-1]
            # Try to set region to last 30 seconds if enough data
            first_time = x_values[0]
            window_start = max(first_time, last_time - 30)
            self.region.setRegion((window_start, last_time))

        # Update visible plot data based on region
        self._apply_region_filter()

    def _region_changed(self):
        """Handler for when the region selector is changed by user."""
        self._apply_region_filter()

        # Emit signal with new region bounds
        region_min, region_max = self.region.getRegion()
        self.region_changed.emit(region_min, region_max)

    def _apply_region_filter(self):
        """Apply the region filter to show only data in the selected time window."""
        if not self._full_data:
            return

        # Get region bounds
        region_min, region_max = self.region.getRegion()

        # Filter data to only show points within the region
        filtered_data = [(x, y) for x, y in self._full_data if region_min <= x <= region_max]

        if filtered_data:
            # Unzip the filtered data
            x_values, y_values = zip(*filtered_data)

            # Update the curve
            self.curve.setData(x_values, y_values)

            # Auto-scale Y axis to fit the visible data
            self.setYRange(min(y_values), max(y_values) * 1.1)

    def export_png(self, filename: str):
        """
        Export the current plot view as a PNG image.

        Args:
        ----
            filename: The filename to save the PNG to

        """
        exporter = pg.exporters.ImageExporter(self.plotItem)
        exporter.export(filename)

    def export_csv(self, filename: str):
        """
        Export the current data as a CSV file.

        Args:
        ----
            filename: The filename to save the CSV to

        """
        exporter = pg.exporters.CSVExporter(self.plotItem)
        exporter.export(filename)


class AlertBadge(QtW.QLabel):
    """
    Alert badge widget that displays colored notifications.

    Shows color-coded alerts with appropriate styling based on severity.
    """

    # Color mapping for different alert levels
    colors = {
        "EMERGENCY": "#e74c3c",  # Red
        "CRITICAL": "#e67e22",  # Orange
        "WARNING": "#f1c40f",  # Yellow
        "NORMAL": "#2ecc71",  # Green
    }

    def __init__(self, parent: Optional[QtW.QWidget] = None):
        """
        Initialize the alert badge.

        Args:
        ----
            parent: Optional parent widget

        """
        super().__init__(parent)

        # Set default style
        self.setStyleSheet("padding: 4px; border-radius: 4px;")
        self.setAlignment(QtC.Qt.AlignCenter)
        self.setMinimumWidth(150)
        self.setText("")

    def push(self, level: str, message: str, duration: int = 5000):
        """
        Show a new alert with the specified level and message.

        Args:
        ----
            level: Alert level (EMERGENCY, CRITICAL, WARNING, NORMAL)
            message: Alert message to display
            duration: Time in ms to show the alert (0 for no auto-hide)

        """
        # Set text and styling based on alert level
        self.setText(message)
        color = self.colors.get(level, self.colors["NORMAL"])

        # Set appropriate styling
        self.setStyleSheet(
            f"""
            background-color: {color};
            color: white;
            padding: 4px;
            border-radius: 4px;
            font-weight: bold;
        """
        )

        # Auto-hide after duration if specified
        if duration > 0:
            QtC.QTimer.singleShot(duration, lambda: self.setText(""))


class CompareDock(QtW.QDockWidget):
    """
    Dock widget for comparing multiple GPU metrics.

    Allows side-by-side comparison of different metrics or the same
    metric across different GPUs.
    """

    def __init__(self, parent: Optional[QtW.QWidget] = None):
        """
        Initialize the comparison dock widget.

        Args:
        ----
            parent: Optional parent widget

        """
        super().__init__("GPU Comparison", parent)

        # Main widget and layout
        content = QtW.QWidget()
        layout = QtW.QVBoxLayout(content)

        # Create splitter for resizable sections
        self.splitter = QtW.QSplitter(QtC.Qt.Vertical)

        # First plot section
        self.top_container = QtW.QWidget()
        top_layout = QtW.QVBoxLayout(self.top_container)

        self.top_selector = QtW.QComboBox()
        self.top_plot = HistoryPlot("util_0")

        top_layout.addWidget(self.top_selector)
        top_layout.addWidget(self.top_plot)

        # Second plot section
        self.bottom_container = QtW.QWidget()
        bottom_layout = QtW.QVBoxLayout(self.bottom_container)

        self.bottom_selector = QtW.QComboBox()
        self.bottom_plot = HistoryPlot("vram_0")

        bottom_layout.addWidget(self.bottom_selector)
        bottom_layout.addWidget(self.bottom_plot)

        # Add containers to splitter
        self.splitter.addWidget(self.top_container)
        self.splitter.addWidget(self.bottom_container)

        # Add splitter to main layout
        layout.addWidget(self.splitter)

        # Set the content widget
        self.setWidget(content)

        # Populate metric selectors
        self._populate_selectors()

        # Connect signals
        self.top_selector.currentTextChanged.connect(self._top_metric_changed)
        self.bottom_selector.currentTextChanged.connect(self._bottom_metric_changed)

    def _populate_selectors(self):
        """Populate the metric selector comboboxes."""
        # Common metrics for all GPUs
        base_metrics = ["util", "vram", "temp", "power"]

        # Add metrics for each GPU (assuming max 8 GPUs)
        for gpu_id in range(8):
            for metric in base_metrics:
                metric_key = f"{metric}_{gpu_id}"
                self.top_selector.addItem(f"GPU {gpu_id} - {metric}", metric_key)
                self.bottom_selector.addItem(f"GPU {gpu_id} - {metric}", metric_key)

        # Add average metrics
        self.top_selector.addItem("Average Utilization", "util_avg")
        self.top_selector.addItem("Average VRAM", "vram_avg")
        self.bottom_selector.addItem("Average Utilization", "util_avg")
        self.bottom_selector.addItem("Average VRAM", "vram_avg")

        # Set default selections
        self.top_selector.setCurrentIndex(0)  # GPU 0 utilization
        self.bottom_selector.setCurrentIndex(1)  # GPU 0 VRAM

    def _top_metric_changed(self, text: str):
        """Handler when top metric selection changes."""
        metric_key = self.top_selector.currentData()
        if metric_key:
            self.top_plot.metric = metric_key
            # Update plot with current history data for this metric
            samples = hist.snapshot(metric_key)
            if samples:
                self.top_plot.update_series(samples)

    def _bottom_metric_changed(self, text: str):
        """Handler when bottom metric selection changes."""
        metric_key = self.bottom_selector.currentData()
        if metric_key:
            self.bottom_plot.metric = metric_key
            # Update plot with current history data for this metric
            samples = hist.snapshot(metric_key)
            if samples:
                self.bottom_plot.update_series(samples)

    def update_plots(self, metric: str, value: float):
        """
        Update plots when new telemetry data is available.

        Args:
        ----
            metric: Metric key that was updated
            value: New value for the metric

        """
        # Check if either plot is showing this metric
        if self.top_plot.metric == metric:
            samples = hist.snapshot(metric)
            if samples:
                self.top_plot.update_series(samples)

        if self.bottom_plot.metric == metric:
            samples = hist.snapshot(metric)
            if samples:
                self.bottom_plot.update_series(samples)


class PresetListWidget(QtW.QListWidget):
    """Widget for displaying and managing configuration presets."""

    preset_selected = QtC.Signal(str)  # Emitted when a preset is selected

    def __init__(self, parent: Optional[QtW.QWidget] = None):
        """
        Initialize the preset list widget.

        Args:
        ----
            parent: Optional parent widget

        """
        super().__init__(parent)

        # Set selection mode
        self.setSelectionMode(QtW.QAbstractItemView.SingleSelection)

        # Connect double-click signal
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def _on_item_double_clicked(self, item: QtW.QListWidgetItem):
        """Handler for double-clicking a preset."""
        self.preset_selected.emit(item.text())


class PresetDock(QtW.QDockWidget):
    """Dock widget for managing configuration presets."""

    preset_selected = QtC.Signal(str)  # Emitted when a preset is selected

    def __init__(self, parent: Optional[QtW.QWidget] = None):
        """
        Initialize the preset dock widget.

        Args:
        ----
            parent: Optional parent widget

        """
        super().__init__("Configuration Presets", parent)

        # Main widget and layout
        content = QtW.QWidget()
        layout = QtW.QVBoxLayout(content)

        # Create toolbar
        toolbar = QtW.QToolBar()

        # Add actions
        self.new_action = toolbar.addAction("New")
        self.save_action = toolbar.addAction("Save")
        self.delete_action = toolbar.addAction("Delete")

        # Create preset list
        self.preset_list = PresetListWidget()

        # Add widgets to layout
        layout.addWidget(toolbar)
        layout.addWidget(self.preset_list)

        # Set the content widget
        self.setWidget(content)

        # Connect signals
        self.new_action.triggered.connect(self._on_new)
        self.save_action.triggered.connect(self._on_save)
        self.delete_action.triggered.connect(self._on_delete)
        self.preset_list.preset_selected.connect(self.preset_selected)

    def _on_new(self):
        """Handler for creating a new preset."""
        # TODO: Implement preset creation

    def _on_save(self):
        """Handler for saving the current preset."""
        # TODO: Implement preset saving

    def _on_delete(self):
        """Handler for deleting the selected preset."""
        # TODO: Implement preset deletion

    def refresh_presets(self):
        """Refresh the preset list from disk."""
        # TODO: Implement preset refresh
