import logging
import os

from PySide6.QtCore import QEvent, QSize, QTimer
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import QMainWindow, QMessageBox, QTabWidget, QPushButton

logger = logging.getLogger("DualGPUOptimizer")


class DualGPUOptimizerApp(QMainWindow):
    """Main application window for DualGPUOptimizer."""

    def __init__(self, mock_mode=False):
        super().__init__()
        self.mock_mode = mock_mode

        # Set up logging
        self.logger = logger
        self.logger.info("Initializing main application window")

        # Set basic window properties
        self.setWindowTitle("DualGPUOptimizer")
        self.setMinimumSize(1000, 650)

        # Set application icon if available
        self._set_application_icon()

        # Apply dark theme
        self._apply_theme()

        # Initialize UI components
        self._init_ui()

        # Initialize system tray
        self._init_system_tray()

        # Set up GPU monitoring timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_gpu_metrics)
        self.update_timer.start(1000)  # Update once per second

        self.logger.info("Application window initialization complete")

    def _set_application_icon(self):
        """Set the application icon if available."""
        icon_paths = [
            os.path.join(os.path.dirname(__file__), "..", "resources", "icon.png"),
            os.path.join(os.path.dirname(__file__), "..", "..", "resources", "icon.png"),
            os.path.join("resources", "icon.png"),
        ]

        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                self.logger.info(f"Found icon at: {icon_path}")
                try:
                    self.setWindowIcon(QIcon(icon_path))
                    return
                except Exception as e:
                    self.logger.warning(f"Failed to set icon: {e}")

        self.logger.warning("No application icon found")

    def _apply_theme(self):
        """Apply dark theme to the application."""
        # Purple dark theme
        self.setStyleSheet(
            """
            QMainWindow, QTabWidget, QWidget {
                background-color: #2D1E40; 
                color: #FFFFFF;
            }
            
            QTabWidget::pane {
                border: 1px solid #3D2A50;
                background-color: #2D1E40;
            }
            
            QTabBar::tab {
                background-color: #241934;
                color: #FFFFFF;
                padding: 8px 20px;
                margin-right: 2px;
                margin-bottom: -1px;
            }
            
            QTabBar::tab:selected {
                background-color: #8A54FD;
                border-bottom: 2px solid #A883FD;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #372952;
            }
            
            QPushButton {
                background-color: #8A54FD;
                color: #FFFFFF;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
            }
            
            QPushButton:hover {
                background-color: #A883FD;
            }
            
            QPushButton:pressed {
                background-color: #6A3EBD;
            }
            
            QProgressBar {
                border: 1px solid #3D2A50;
                border-radius: 4px;
                background-color: #241934;
                text-align: center;
                color: #FFFFFF;
            }
            
            QProgressBar::chunk {
                background-color: #8A54FD;
                border-radius: 3px;
            }
            
            QLabel {
                color: #FFFFFF;
            }
            
            QComboBox {
                background-color: #241934;
                color: #FFFFFF;
                padding: 4px 8px;
                border: 1px solid #3D2A50;
                border-radius: 4px;
            }
            
            QComboBox:hover {
                background-color: #372952;
            }
            
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 18px;
                border-left: 1px solid #3D2A50;
            }
            
            QComboBox QAbstractItemView {
                background-color: #241934;
                color: #FFFFFF;
                selection-background-color: #8A54FD;
                selection-color: #FFFFFF;
            }
            
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #241934;
                color: #FFFFFF;
                border: 1px solid #3D2A50;
                border-radius: 4px;
                padding: 4px;
            }
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border: 1px solid #8A54FD;
            }
            
            QScrollBar:vertical {
                background-color: #241934;
                width: 12px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #3D2A50;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #8A54FD;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background-color: #241934;
                height: 12px;
                margin: 0px;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #3D2A50;
                border-radius: 6px;
                min-width: 20px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #8A54FD;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            QStatusBar {
                background-color: #241934;
                color: #FFFFFF;
            }
            
            QStatusBar::item {
                border: none;
            }
            
            QCheckBox {
                spacing: 5px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #3D2A50;
                border-radius: 3px;
                background-color: #241934;
            }
            
            QCheckBox::indicator:checked {
                background-color: #8A54FD;
                border: 1px solid #8A54FD;
            }
            
            QCheckBox::indicator:hover {
                border: 1px solid #A883FD;
            }
            
            QSpinBox {
                background-color: #241934;
                color: #FFFFFF;
                border: 1px solid #3D2A50;
                border-radius: 4px;
                padding: 4px;
            }
            
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #372952;
                border-radius: 2px;
            }
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #8A54FD;
            }
        """
        )

        self.logger.info("Applied dark theme to application")

    def _init_ui(self):
        """Initialize the UI components."""
        # Create tab widget as central widget
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        # Import tab modules here to avoid circular imports
        try:
            from dualgpuopt.qt.dashboard_tab import DashboardTab

            self.dashboard_tab = DashboardTab(self.mock_mode)
            self.tabs.addTab(self.dashboard_tab, "Dashboard")
            self.logger.info("Dashboard tab initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Dashboard tab: {e}")
            self._show_error_message(
                "Dashboard Tab Error", f"Failed to initialize Dashboard tab: {str(e)}"
            )

        try:
            from dualgpuopt.qt.optimizer_tab import OptimizerTab

            self.optimizer_tab = OptimizerTab(self.mock_mode)
            self.tabs.addTab(self.optimizer_tab, "Optimizer")
            self.logger.info("Optimizer tab initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Optimizer tab: {e}")
            self._show_error_message(
                "Optimizer Tab Error", f"Failed to initialize Optimizer tab: {str(e)}"
            )

        # Add Launcher tab
        try:
            from dualgpuopt.qt.launcher_tab import LauncherTab

            self.launcher_tab = LauncherTab(self.mock_mode)
            self.tabs.addTab(self.launcher_tab, "Launcher")
            self.logger.info("Launcher tab initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Launcher tab: {e}")
            self._show_error_message(
                "Launcher Tab Error", f"Failed to initialize Launcher tab: {str(e)}"
            )

        # Add Memory Profiler tab
        try:
            from dualgpuopt.qt.memory_tab import MemoryProfilerTab

            self.memory_tab = MemoryProfilerTab(self.mock_mode)
            self.tabs.addTab(self.memory_tab, "Memory Profiler")
            self.logger.info("Memory Profiler tab initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Memory Profiler tab: {e}")
            self._show_error_message(
                "Memory Profiler Tab Error", f"Failed to initialize Memory Profiler tab: {str(e)}"
            )

        # Add Settings tab
        try:
            from dualgpuopt.qt.settings_tab import SettingsTab

            self.settings_tab = SettingsTab()
            self.tabs.addTab(self.settings_tab, "Settings")
            # Connect settings signal
            self.settings_tab.settings_applied.connect(self._on_settings_applied)
            self.logger.info("Settings tab initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Settings tab: {e}")
            self._show_error_message(
                "Settings Tab Error", f"Failed to initialize Settings tab: {str(e)}"
            )

        # Set up status bar
        self.statusBar().showMessage("Ready")

    def _init_system_tray(self):
        """Initialize system tray integration"""
        try:
            from dualgpuopt.qt.system_tray import GPUTrayManager

            # Get settings
            settings = {}
            if hasattr(self, "settings_tab"):
                # Get current settings from the settings tab
                settings = self.settings_tab.settings_manager.get_settings()

            # Create tray manager
            self.tray_manager = GPUTrayManager(settings)

            # Connect signals
            self.tray_manager.show_app_requested.connect(self.show_and_activate)
            self.tray_manager.exit_app_requested.connect(self.close_application)

            # If we have the launcher tab, connect the launch model signal
            if hasattr(self, "launcher_tab"):
                self.tray_manager.launch_model_requested.connect(self.launcher_tab.launch_model)

                # Update available models in tray
                models = self.launcher_tab.get_available_models()
                self.tray_manager.update_available_models(models)

            self.logger.info("System tray integration initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize system tray: {e}")
            self.tray_manager = None

    def _update_gpu_metrics(self):
        """Update GPU metrics on timer."""
        try:
            # Get GPU metrics using the selected mode
            if self.mock_mode:
                metrics = self._get_mock_metrics()
            else:
                metrics = self._get_real_metrics()

            # Update dashboard tab if initialized
            if hasattr(self, "dashboard_tab"):
                self.dashboard_tab.update_metrics(metrics)

            # Update tray metrics if initialized
            if hasattr(self, "tray_manager") and self.tray_manager:
                self.tray_manager.update_metrics(metrics)

        except Exception as e:
            self.logger.error(f"Error updating GPU metrics: {e}")
            self.statusBar().showMessage(f"Error: {str(e)}", 5000)  # Show for 5 seconds

    def _get_mock_metrics(self):
        """Generate mock GPU metrics for testing."""
        import random

        # Create mock data for 2 GPUs
        return [
            {
                "memory_used": random.randint(2048, 8192),
                "memory_total": 12288,
                "utilization": random.randint(10, 90),
                "temperature": random.randint(50, 85),
                "power": random.randint(80, 200),
                "power_limit": 250,
                "clock_sm": random.randint(1200, 1800),
                "clock_mem": random.randint(4000, 5000),
                "name": "NVIDIA GeForce RTX 3080",
            },
            {
                "memory_used": random.randint(1024, 6144),
                "memory_total": 12288,
                "utilization": random.randint(5, 80),
                "temperature": random.randint(45, 75),
                "power": random.randint(60, 180),
                "power_limit": 250,
                "clock_sm": random.randint(1100, 1700),
                "clock_mem": random.randint(3800, 4800),
                "name": "NVIDIA GeForce RTX 3070",
            },
        ]

    def _get_real_metrics(self):
        """Get real GPU metrics using pynvml."""
        try:
            import pynvml

            pynvml.nvmlInit()

            device_count = pynvml.nvmlDeviceGetCount()
            metrics = []

            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)

                # Device name
                name = pynvml.nvmlDeviceGetName(handle).decode("utf-8")

                # Memory info
                memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                memory_used = memory.used // 1024 // 1024  # Convert to MB
                memory_total = memory.total // 1024 // 1024

                # Utilization info
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_util = utilization.gpu

                # Temperature
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)

                # Power
                try:
                    power = pynvml.nvmlDeviceGetPowerUsage(handle) // 1000  # Convert to W
                    power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) // 1000
                except pynvml.NVMLError:
                    power = 0
                    power_limit = 0

                # Clock speeds
                try:
                    clock_sm = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
                    clock_mem = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
                except pynvml.NVMLError:
                    clock_sm = 0
                    clock_mem = 0

                metrics.append(
                    {
                        "name": name,
                        "memory_used": memory_used,
                        "memory_total": memory_total,
                        "utilization": gpu_util,
                        "temperature": temp,
                        "power": power,
                        "power_limit": power_limit,
                        "clock_sm": clock_sm,
                        "clock_mem": clock_mem,
                    }
                )

            pynvml.nvmlShutdown()
            return metrics

        except ImportError:
            self.logger.error("pynvml not installed - using mock data")
            self.statusBar().showMessage("pynvml not installed - using mock data", 5000)
            return self._get_mock_metrics()

        except Exception as e:
            self.logger.error(f"Error getting GPU metrics: {str(e)}")
            self.statusBar().showMessage(f"GPU Error: {str(e)}", 5000)
            return self._get_mock_metrics()

    def _show_error_message(self, title, message):
        """Show an error message dialog."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        return msg_box.exec_()

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event."""
        # Check for minimize to tray setting
        minimize_to_tray = True  # Default value

        if hasattr(self, "settings_tab"):
            minimize_to_tray = self.settings_tab.settings_manager.get_settings().get(
                "minimize_to_tray", True
            )

        if minimize_to_tray and hasattr(self, "tray_manager") and self.tray_manager:
            # Minimize to tray instead of closing
            self.logger.info("Minimizing to tray")
            self.hide()

            # Show notification
            self.tray_manager.show_notification(
                "DualGPUOptimizer",
                "Application minimized to tray. Double-click the tray icon to restore.",
                show_immediately=True,
            )

            # Ignore the close event
            event.ignore()
        else:
            # Actually close the application
            self.close_application()
            event.accept()

    def close_application(self):
        """Close the application completely."""
        self.logger.info("Application closing")

        # Stop the update timer
        if hasattr(self, "update_timer") and self.update_timer.isActive():
            self.update_timer.stop()

        # Clean up tray if active
        if hasattr(self, "tray_manager") and self.tray_manager:
            self.tray_manager.cleanup()

    def show_and_activate(self):
        """Show and activate the window."""
        # Show the window
        self.show()

        # Raise to top
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
        self.activateWindow()

        self.logger.info("Application window restored")

    def _on_settings_applied(self, settings):
        """Handle settings changes."""
        self.logger.info("Applying new settings")

        # Update tray settings
        if hasattr(self, "tray_manager") and self.tray_manager:
            self.tray_manager.update_settings(settings)

        # Update poll interval if changed
        if hasattr(self, "update_timer"):
            poll_interval = settings.get("poll_interval", 1000)
            if self.update_timer.interval() != poll_interval:
                self.update_timer.setInterval(poll_interval)
                self.logger.info(f"Updated poll interval to {poll_interval}ms")

        # Apply theme changes if needed
        theme_id = settings.get("theme", "dark_purple")
        # TODO: Implement theme switching when multiple themes are available

    def _init_tabs(self):
        """Initialize tabs and add them to the tab widget."""
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setMovable(False)
        self.tab_widget.setDocumentMode(True)
        
        # Initialize tabs in the correct order
        try:
            # Dashboard Tab
            self.dashboard_tab = DashboardTab(mock_mode=self.mock_mode)
            self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
            self.logger.info("Dashboard tab initialized")
            
            # Optimizer Tab
            self.optimizer_tab = OptimizerTab(mock_mode=self.mock_mode)
            self.tab_widget.addTab(self.optimizer_tab, "Optimizer")
            self.logger.info("Optimizer tab initialized")
            
            # Launcher Tab
            self.launcher_tab = LauncherTab(mock_mode=self.mock_mode)
            self.tab_widget.addTab(self.launcher_tab, "Launcher")
            self.logger.info("Launcher tab initialized")
            
            # Connect optimizer and launcher tabs
            self._connect_optimizer_launcher()
            
            # Memory Profiler Tab
            self.memory_profiler_tab = MemoryProfilerTab(mock_mode=self.mock_mode)
            self.tab_widget.addTab(self.memory_profiler_tab, "Memory Profiler")
            self.logger.info("Memory Profiler tab initialized")
            
            # Settings Tab
            self.settings_tab = SettingsTab()
            self.tab_widget.addTab(self.settings_tab, "Settings")
            self.logger.info("Settings tab initialized")
            
            # Connect settings changes
            self.settings_tab.settings_applied.connect(self._on_settings_applied)
            
        except Exception as e:
            self.logger.error(f"Error initializing tabs: {e}")
            
        # Add tab widget to central layout
        self.central_layout.addWidget(self.tab_widget)

    def _connect_optimizer_launcher(self):
        """Connect optimizer and launcher tabs for direct settings transfer."""
        try:
            if hasattr(self, 'optimizer_tab') and hasattr(self, 'launcher_tab'):
                # Add any additional connections beyond the event bus if needed
                self.logger.info("Connected optimizer and launcher tabs")
                
                # Use the event_bus mechanism for the main connections
                # The launcher tab subscribes to the "optimizer_settings" event
                
                # Add direct method to switch to launcher tab after applying settings
                optimizer_apply_button = self.optimizer_tab.findChild(QPushButton, "apply_button")
                if optimizer_apply_button:
                    optimizer_apply_button.clicked.connect(self._switch_to_launcher_tab)
        except Exception as e:
            self.logger.error(f"Error connecting optimizer and launcher tabs: {e}")
    
    def _switch_to_launcher_tab(self):
        """Switch to the launcher tab."""
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "Launcher":
                self.tab_widget.setCurrentIndex(i)
                break
