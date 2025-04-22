"""
Main application module for DualGPUOptimizer Qt GUI.

This module provides the entry point for the Qt-based DualGPUOptimizer GUI.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pyqtgraph as pg
from PySide6 import QtCore as QtC
from PySide6 import QtGui as QtG
from PySide6 import QtWidgets as QtW

from dualgpuopt.qtgui.telethread import create_telemetry_thread

# Import our components
from dualgpuopt.qtgui.widgets import AlertBadge, CompareDock, HistoryPlot, PresetDock
from dualgpuopt.telemetry_history import hist

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path.home() / ".dualgpuopt" / "qtgui.log"),
    ],
)
logger = logging.getLogger(__name__)


class DualGPUDashboard(QtW.QMainWindow):
    """Main dashboard window for DualGPUOptimizer."""

    def __init__(self):
        """Initialize the dashboard window."""
        super().__init__()

        # Set window properties
        self.setWindowTitle("DualGPUOptimizer")
        self.setMinimumSize(1024, 768)

        # Create central widget and layout
        central = QtW.QWidget()
        layout = QtW.QVBoxLayout(central)

        # Create main dock area
        self.dock_area = QtW.QWidget()
        self.dock_layout = QtW.QHBoxLayout(self.dock_area)

        # Add dock area to layout
        layout.addWidget(self.dock_area)

        # Set central widget
        self.setCentralWidget(central)

        # Create dockable widgets
        self._create_docks()

        # Create status bar with alert badge
        self.status_bar = self.statusBar()
        self.alert_badge = AlertBadge()
        self.status_bar.addPermanentWidget(self.alert_badge)

        # Create menu bar
        self._create_menus()

        # Create system tray icon
        self._create_tray_icon()

        # Initialize telemetry thread
        self._init_telemetry()

        # Subscribe to events
        self._subscribe_events()

        logger.info("Dashboard window initialized")

    def _create_docks(self):
        """Create all dockable widgets."""
        # Create utilization plot dock
        self.util_dock = QtW.QDockWidget("GPU Utilization", self)
        self.util_plot = HistoryPlot("util_0")
        self.util_dock.setWidget(self.util_plot)

        # Create memory plot dock
        self.vram_dock = QtW.QDockWidget("VRAM Usage", self)
        self.vram_plot = HistoryPlot("vram_0")
        self.vram_dock.setWidget(self.vram_plot)

        # Create temperature plot dock
        self.temp_dock = QtW.QDockWidget("Temperature", self)
        self.temp_plot = HistoryPlot("temp_0")
        self.temp_dock.setWidget(self.temp_plot)

        # Create power plot dock
        self.power_dock = QtW.QDockWidget("Power Usage", self)
        self.power_plot = HistoryPlot("power_0")
        self.power_dock.setWidget(self.power_plot)

        # Create comparison dock
        self.compare_dock = CompareDock(self)

        # Create presets dock
        self.presets_dock = PresetDock(self)

        # Add docks to main window
        self.addDockWidget(QtC.Qt.LeftDockWidgetArea, self.util_dock)
        self.addDockWidget(QtC.Qt.LeftDockWidgetArea, self.vram_dock)
        self.addDockWidget(QtC.Qt.RightDockWidgetArea, self.temp_dock)
        self.addDockWidget(QtC.Qt.RightDockWidgetArea, self.power_dock)
        self.addDockWidget(QtC.Qt.BottomDockWidgetArea, self.compare_dock)
        self.addDockWidget(QtC.Qt.RightDockWidgetArea, self.presets_dock)

        # Tabify some docks for better space usage
        self.tabifyDockWidget(self.util_dock, self.vram_dock)
        self.tabifyDockWidget(self.temp_dock, self.power_dock)

        # Raise the first tab in each tabbed area
        self.util_dock.raise_()
        self.temp_dock.raise_()

    def _create_menus(self):
        """Create the application menus."""
        # Create menu bar
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")

        # Export submenu
        export_menu = file_menu.addMenu("&Export")

        # Export actions
        export_menu.addAction(
            "Export Utilization as PNG",
            lambda: self.util_plot.export_png(
                str(Path.home() / ".dualgpuopt" / "exports" / "utilization.png")
            ),
        )
        export_menu.addAction(
            "Export VRAM as PNG",
            lambda: self.vram_plot.export_png(
                str(Path.home() / ".dualgpuopt" / "exports" / "vram.png")
            ),
        )
        export_menu.addAction(
            "Export Utilization as CSV",
            lambda: self.util_plot.export_csv(
                str(Path.home() / ".dualgpuopt" / "exports" / "utilization.csv")
            ),
        )
        export_menu.addAction(
            "Export VRAM as CSV",
            lambda: self.vram_plot.export_csv(
                str(Path.home() / ".dualgpuopt" / "exports" / "vram.csv")
            ),
        )

        # File menu actions
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close)

        # View menu
        view_menu = menu_bar.addMenu("&View")

        # View actions for docks
        view_menu.addAction("&Utilization", lambda: self._toggle_dock(self.util_dock))
        view_menu.addAction("&VRAM Usage", lambda: self._toggle_dock(self.vram_dock))
        view_menu.addAction("&Temperature", lambda: self._toggle_dock(self.temp_dock))
        view_menu.addAction("&Power Usage", lambda: self._toggle_dock(self.power_dock))
        view_menu.addAction("&Comparison", lambda: self._toggle_dock(self.compare_dock))
        view_menu.addAction("&Presets", lambda: self._toggle_dock(self.presets_dock))

        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction("&About", self._show_about)

    def _toggle_dock(self, dock: QtW.QDockWidget):
        """Toggle visibility of a dock widget."""
        dock.setVisible(not dock.isVisible())

    def _show_about(self):
        """Show the about dialog."""
        QtW.QMessageBox.about(
            self,
            "About DualGPUOptimizer",
            "DualGPUOptimizer Qt Dashboard\n\n"
            "A modern GUI for optimizing and monitoring dual GPU setups.",
        )

    def _create_tray_icon(self):
        """Create the system tray icon."""
        # Create tray icon (using a built-in icon for now)
        self.tray_icon = QtW.QSystemTrayIcon(QtG.QIcon.fromTheme("computer"), self)

        # Create context menu for tray icon
        tray_menu = QtW.QMenu()

        # Add actions to tray menu
        tray_menu.addAction("Show Dashboard", self.show)
        tray_menu.addAction("Exit", self.close)

        # Set the tray icon's context menu
        self.tray_icon.setContextMenu(tray_menu)

        # Set tooltip
        self.tray_icon.setToolTip("DualGPUOptimizer")

        # Show the tray icon
        self.tray_icon.show()

    def _init_telemetry(self):
        """Initialize telemetry thread and connections."""
        # Create telemetry thread and worker
        self.telemetry_thread, self.telemetry_worker = create_telemetry_thread()

        # Connect worker signals to update methods
        self.telemetry_worker.metric_updated.connect(self._on_metric_updated)
        self.telemetry_worker.alert_triggered.connect(self._on_alert_triggered)

    def _subscribe_events(self):
        """Subscribe to events from the event bus."""
        # Add event bus subscriptions here
        pass

    def _on_metric_updated(self, metric: str, value: float):
        """Handler for metric update signals from telemetry worker."""
        # Update plots based on metric name
        if metric == "util_0":
            samples = hist.snapshot("util_0")
            if samples:
                self.util_plot.update_series(samples)

        elif metric == "vram_0":
            samples = hist.snapshot("vram_0")
            if samples:
                self.vram_plot.update_series(samples)

        elif metric == "temp_0":
            samples = hist.snapshot("temp_0")
            if samples:
                self.temp_plot.update_series(samples)

        elif metric == "power_0":
            samples = hist.snapshot("power_0")
            if samples:
                self.power_plot.update_series(samples)

        # Update comparison dock plots
        self.compare_dock.update_plots(metric, value)

    def _on_alert_triggered(self, level: str, message: str):
        """Handler for alert signals from telemetry worker."""
        # Update alert badge
        self.alert_badge.push(level, message)

        # Show system tray notification for high-priority alerts
        if level in ["EMERGENCY", "CRITICAL"]:
            self.tray_icon.showMessage(
                f"{level} Alert",
                message,
                (
                    QtW.QSystemTrayIcon.Critical
                    if level == "EMERGENCY"
                    else QtW.QSystemTrayIcon.Warning
                ),
                5000,  # 5 seconds
            )

    def closeEvent(self, event: QtG.QCloseEvent):
        """Handle window close event."""
        # Terminate telemetry thread
        if hasattr(self, "telemetry_worker"):
            self.telemetry_worker.stop()

        if hasattr(self, "telemetry_thread"):
            self.telemetry_thread.quit()
            self.telemetry_thread.wait(1000)  # Wait up to 1 second for thread to quit

        # Accept the close event
        event.accept()


def main():
    """Main entry point for the Qt GUI."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="DualGPUOptimizer Qt GUI")
    parser.add_argument("--mock", action="store_true", help="Use mock GPU data")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Set up environment based on args
    if args.mock:
        import os

        os.environ["DUALGPUOPT_MOCK_GPU"] = "1"

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create QApplication
    app = QtW.QApplication(sys.argv)
    app.setApplicationName("DualGPUOptimizer")
    app.setOrganizationName("DualGPUOptimizer")

    # Set application style
    app.setStyle("Fusion")

    # Apply dark palette if needed
    _apply_dark_palette(app)

    # Create and show the main window
    main_window = DualGPUDashboard()
    main_window.show()

    # Start the event loop
    return app.exec()


def _apply_dark_palette(app: QtW.QApplication):
    """Apply a dark color palette to the application."""
    dark_palette = QtG.QPalette()

    # Set colors
    dark_color = QtG.QColor(45, 45, 45)
    disabled_color = QtG.QColor(70, 70, 70)
    dark_text = QtG.QColor(200, 200, 200)

    # Apply colors to palette
    dark_palette.setColor(QtG.QPalette.Window, dark_color)
    dark_palette.setColor(QtG.QPalette.WindowText, dark_text)
    dark_palette.setColor(QtG.QPalette.Base, QtG.QColor(18, 18, 18))
    dark_palette.setColor(QtG.QPalette.AlternateBase, dark_color)
    dark_palette.setColor(QtG.QPalette.ToolTipBase, QtG.QColor(255, 255, 220))
    dark_palette.setColor(QtG.QPalette.ToolTipText, QtG.QColor(0, 0, 0))
    dark_palette.setColor(QtG.QPalette.Text, dark_text)
    dark_palette.setColor(QtG.QPalette.Button, dark_color)
    dark_palette.setColor(QtG.QPalette.ButtonText, dark_text)
    dark_palette.setColor(QtG.QPalette.Link, QtG.QColor(42, 130, 218))
    dark_palette.setColor(QtG.QPalette.Highlight, QtG.QColor(42, 130, 218))
    dark_palette.setColor(QtG.QPalette.HighlightedText, QtG.QColor(0, 0, 0))
    dark_palette.setColor(QtG.QPalette.Disabled, QtG.QPalette.Text, disabled_color)
    dark_palette.setColor(QtG.QPalette.Disabled, QtG.QPalette.ButtonText, disabled_color)

    # Apply the palette
    app.setPalette(dark_palette)

    # Update pyqtgraph configuration for dark theme
    pg.setConfigOption("background", (25, 25, 25))
    pg.setConfigOption("foreground", "w")


if __name__ == "__main__":
    sys.exit(main())
