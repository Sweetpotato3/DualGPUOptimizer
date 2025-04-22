"""
Main application window for DualGPUOptimizer Qt implementation
"""

import logging
import os
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMenuBar,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QToolBar,
    QMessageBox,
)

# Import refactored components
from dualgpuopt.engine.backend import Engine
from dualgpuopt.services.alerts import AlertService
from dualgpuopt.engine.pool import EnginePool
from dualgpuopt.gui.cache_monitor import CacheMonitorWidget

# Local imports
from dualgpuopt.services.config_service import get_config_service
from dualgpuopt.services.telemetry import TelemetryWorker
from dualgpuopt.ui.advanced import AdvancedToolsDock

logger = logging.getLogger("DualGPUOptimizer")


class DualGPUOptimizerApp(QMainWindow):
    """Main application window for DualGPUOptimizer"""

    def __init__(self, mock_mode: bool = False, parent: Optional[QWidget] = None):
        """Initialize the main application window

        Args:
            mock_mode: Whether to use mock GPU data
            parent: Parent widget
        """
        super().__init__(parent)

        # Set up main window properties
        self.setWindowTitle("DualGPUOptimizer")
        self.resize(1024, 768)
        self.setMinimumSize(800, 600)

        # Track mock mode
        self.mock_mode = mock_mode

        # Initialize refactored core services
        self._init_services()

        # Initialize UI components
        self._setup_ui()

        # Set up status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Set up system tray
        self._setup_system_tray()

        # Initialize tabs
        self._init_tabs()

        # Set up menu bar
        self._setup_menu()

        # Set up timers
        self._setup_timers()

        logger.info("DualGPUOptimizer window initialized")

    def _init_services(self):
        """Initialize core services"""
        # Initialize the unified Engine
        try:
            self.engine = EnginePool.get("No model loaded", mock=True)
            logger.info("Unified Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Engine: {e}")
            self.engine = None

        # Initialize the Alert Service
        try:
            self.alert_service = AlertService()
            # Connect alert service to status bar updates
            self.alert_service.warning_alert.connect(self._handle_warning_alert)
            self.alert_service.critical_alert.connect(self._handle_critical_alert)
            logger.info("Alert Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Alert Service: {e}")
            self.alert_service = None

        # Initialize the Telemetry Worker
        try:
            self.telemetry_worker = TelemetryWorker(mock_mode=self.mock_mode)
            self.telemetry_worker.start()
            logger.info("Telemetry Worker started successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Telemetry Worker: {e}")
            self.telemetry_worker = None

    def _handle_warning_alert(self, message: str, details: Dict[str, Any]):
        """Handle warning alerts from the Alert Service"""
        self.status_bar.showMessage(f"WARNING: {message}", 5000)
        if hasattr(self, "tray_manager") and self.tray_manager:
            self.tray_manager.show_notification("Warning", message)

    def _handle_critical_alert(self, message: str, details: Dict[str, Any]):
        """Handle critical alerts from the Alert Service"""
        self.status_bar.showMessage(f"CRITICAL: {message}", 10000)
        if hasattr(self, "tray_manager") and self.tray_manager:
            self.tray_manager.show_notification("Critical Alert", message, critical=True)

    def _setup_ui(self):
        """Set up the main UI components"""
        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # Set application icon if available
        self._set_application_icon()

        # Initialize docks
        self._init_docks()

    def _set_application_icon(self):
        """Set the application icon"""
        # Try different icon paths
        icon_paths = [
            "dualgpuopt/assets/icon.ico",
            "dualgpuopt/assets/icon.png",
            "dualgpuopt/resources/icon.ico",
            "dualgpuopt/resources/icon.png",
        ]

        for path in icon_paths:
            if os.path.exists(path):
                try:
                    icon = QIcon(path)
                    self.setWindowIcon(icon)
                    logger.info(f"Set application icon from {path}")
                    return
                except Exception as e:
                    logger.warning(f"Failed to set icon from {path}: {e}")

        logger.warning("No application icon found")

    def _setup_system_tray(self):
        """Set up system tray integration"""
        # Import system tray here to avoid circular imports
        try:
            from dualgpuopt.qt.system_tray import GPUTrayManager

            self.tray_manager = GPUTrayManager()

            # Connect signals
            self.tray_manager.show_app_requested.connect(self._handle_show_app)
            self.tray_manager.exit_app_requested.connect(self._handle_exit_app)
            self.tray_manager.reset_gpu_memory_requested.connect(self._handle_reset_gpu_memory)

            logger.info("System tray integration initialized")
        except ImportError as e:
            logger.warning(f"Failed to initialize system tray: {e}")
            self.tray_manager = None

    def _init_tabs(self):
        """Initialize application tabs"""
        try:
            # Dashboard Tab
            from dualgpuopt.qt.dashboard_tab import DashboardTab

            self.dashboard_tab = DashboardTab(mock_mode=self.mock_mode)
            self.tab_widget.addTab(self.dashboard_tab, "Dashboard")

            # Connect telemetry worker if available
            if hasattr(self, "telemetry_worker") and self.telemetry_worker:
                self.dashboard_tab.set_telemetry_worker(self.telemetry_worker)

            # Optimizer Tab
            from dualgpuopt.qt.optimizer_tab import OptimizerTab

            self.optimizer_tab = OptimizerTab()
            self.tab_widget.addTab(self.optimizer_tab, "Optimizer")

            # Memory Profiler Tab
            from dualgpuopt.qt.memory_tab import MemoryProfilerTab

            self.memory_tab = MemoryProfilerTab()
            self.tab_widget.addTab(self.memory_tab, "Memory Profiler")

            # Connect memory tab to advanced dock if available
            if hasattr(self, "advanced_dock") and self.advanced_dock:
                # Memory timeline is shared between memory tab and advanced dock
                self.advanced_dock.set_memory_timeline(self.memory_tab.memory_timeline)

            # Launcher Tab
            from dualgpuopt.qt.launcher_tab import LauncherTab

            self.launcher_tab = LauncherTab()

            # Connect engine to launcher if available
            if hasattr(self, "engine") and self.engine:
                self.launcher_tab.set_engine(self.engine)

            self.tab_widget.addTab(self.launcher_tab, "Launcher")

            # Settings Tab
            from dualgpuopt.qt.settings_tab import SettingsTab

            self.settings_tab = SettingsTab()
            self.tab_widget.addTab(self.settings_tab, "Settings")

            # Cache Monitor Tab
            self.cache_tab = CacheMonitorWidget(self)
            self.tab_widget.addTab(self.cache_tab, "Engine Pool")

            # Connect tab signals
            self._connect_tab_signals()

            logger.info("Application tabs initialized")
        except ImportError as e:
            logger.error(f"Failed to initialize tabs: {e}")
            # Add fallback tab
            fallback_tab = QWidget()
            fallback_layout = QVBoxLayout(fallback_tab)
            fallback_label = QLabel(
                f"Failed to initialize tabs: {e}\n\nPlease check logs for details."
            )
            fallback_layout.addWidget(fallback_label)
            self.tab_widget.addTab(fallback_tab, "Error")

    def _connect_tab_signals(self):
        """Connect signals between tabs"""
        try:
            # Connect optimizer to launcher
            if hasattr(self, "optimizer_tab") and hasattr(self, "launcher_tab"):
                self.optimizer_tab.settings_applied.connect(
                    self.launcher_tab.apply_optimizer_settings
                )
                logger.info("Connected optimizer settings to launcher")
        except Exception as e:
            logger.error(f"Failed to connect tab signals: {e}")

    def _setup_menu(self):
        """Set up the application menu bar"""
        # Create menu bar
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)

        # File menu
        file_menu = menu_bar.addMenu("&File")

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menu_bar.addMenu("&View")

        # Toggle Advanced Tools action
        if hasattr(self, "advanced_dock") and self.advanced_dock:
            toggle_advanced_action = QAction("&Advanced Tools", self)
            toggle_advanced_action.setCheckable(True)
            toggle_advanced_action.setChecked(self.advanced_dock.isVisible())
            toggle_advanced_action.triggered.connect(self._toggle_advanced_dock)
            view_menu.addAction(toggle_advanced_action)

        # Toggle Preset Dock action
        if hasattr(self, "preset_dock") and self.preset_dock:
            toggle_preset_action = QAction("&Presets", self)
            toggle_preset_action.setCheckable(True)
            toggle_preset_action.setChecked(self.preset_dock.isVisible())
            toggle_preset_action.triggered.connect(self._toggle_preset_dock)
            view_menu.addAction(toggle_preset_action)

        # Tools menu
        tools_menu = menu_bar.addMenu("&Tools")

        # Reset GPU memory action
        reset_memory_action = QAction("&Reset GPU Memory", self)
        reset_memory_action.triggered.connect(self._handle_reset_gpu_memory)
        tools_menu.addAction(reset_memory_action)

        # Help menu
        help_menu = menu_bar.addMenu("&Help")

        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_timers(self):
        """Set up application timers"""
        # Status bar update timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(5000)  # Update every 5 seconds

    def _update_status(self):
        """Update the status bar with current information"""
        config_service = get_config_service()
        gpu_count = config_service.get("gpu_count", 0)
        mock_status = "(Mock Mode)" if self.mock_mode else ""
        self.status_bar.showMessage(f"Ready - {gpu_count} GPUs detected {mock_status}")

    def _handle_show_app(self):
        """Handle show application request from system tray"""
        self.show()
        self.raise_()
        self.activateWindow()

    def _handle_exit_app(self):
        """Handle exit application request from system tray"""
        self.close()

    def _handle_reset_gpu_memory(self):
        """Handle reset GPU memory request"""
        try:
            from dualgpuopt.gpu import reset_gpu_memory

            reset_gpu_memory()
            self.status_bar.showMessage("GPU memory reset successful", 3000)
        except Exception as e:
            logger.error(f"Failed to reset GPU memory: {e}")
            self.status_bar.showMessage(f"GPU memory reset failed: {e}", 3000)

    def _show_about(self):
        """Show about dialog"""
        try:
            QMessageBox.about(
                self,
                "About DualGPUOptimizer",
                "DualGPUOptimizer\n\n"
                "A tool for optimizing dual GPU setups for AI workloads.\n\n"
                "© 2024-2025"
            )
        except Exception as e:
            logger.error(f"Failed to show about dialog: {e}")

    def _init_docks(self):
        """Initialize dock widgets"""
        # Advanced Tools Dock
        try:
            self.advanced_dock = AdvancedToolsDock(self)
            self.addDockWidget(Qt.RightDockWidgetArea, self.advanced_dock)
            self.advanced_dock.hide()  # Hidden by default
            logger.info("Advanced Tools Dock initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Advanced Tools Dock: {e}")
            self.advanced_dock = None

        # Preset Dock - Add from services/presets.py
        try:
            from dualgpuopt.services.presets import PresetDock

            self.preset_dock = PresetDock(self)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.preset_dock)
            logger.info("Preset Dock initialized")

            # Connect preset dock to tabs
            self._connect_preset_dock()
        except Exception as e:
            logger.error(f"Failed to initialize Preset Dock: {e}")
            self.preset_dock = None

    def _connect_preset_dock(self):
        """Connect preset dock to tabs"""
        if not hasattr(self, "preset_dock") or not self.preset_dock:
            return

        try:
            # Connect to optimizer tab
            if hasattr(self, "optimizer_tab"):
                self.preset_dock.preset_selected.connect(self.optimizer_tab.apply_preset)
                logger.info("Connected preset dock to optimizer tab")

            # Connect to launcher tab
            if hasattr(self, "launcher_tab"):
                self.preset_dock.preset_selected.connect(self.launcher_tab.apply_preset)
                logger.info("Connected preset dock to launcher tab")
        except Exception as e:
            logger.error(f"Failed to connect preset dock: {e}")

    def _toggle_advanced_dock(self, checked):
        """Toggle visibility of the Advanced Tools dock"""
        if hasattr(self, "advanced_dock") and self.advanced_dock:
            if checked:
                self.advanced_dock.show()
            else:
                self.advanced_dock.hide()

    def _toggle_preset_dock(self, checked):
        """Toggle visibility of the Preset dock"""
        if hasattr(self, "preset_dock") and self.preset_dock:
            if checked:
                self.preset_dock.show()
            else:
                self.preset_dock.hide()

    def closeEvent(self, event):
        """Handle window close event"""
        # Clean up system tray
        if hasattr(self, "tray_manager") and self.tray_manager:
            self.tray_manager.cleanup()

        # Clean up telemetry worker
        if hasattr(self, "telemetry_worker") and self.telemetry_worker:
            try:
                self.telemetry_worker.stop()
                logger.info("Telemetry worker stopped")
            except Exception as e:
                logger.error(f"Error stopping telemetry worker: {e}")

        # Accept the event
        event.accept()
