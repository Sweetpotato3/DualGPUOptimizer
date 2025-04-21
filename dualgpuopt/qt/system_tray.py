import logging
import os
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QAction
from PySide6.QtCore import Qt, Signal, QTimer, QSize

logger = logging.getLogger('DualGPUOptimizer')

class TrayNotification:
    """Data class for tray notification information"""

    def __init__(self, title: str, message: str, icon_type: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.Information):
        self.title = title
        self.message = message
        self.icon_type = icon_type


class GPUTrayManager:
    """Manages the system tray icon and notifications for the application"""

    # Signals
    show_app_requested = Signal()
    exit_app_requested = Signal()
    launch_model_requested = Signal(str)  # model name

    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger('DualGPUOptimizer')
        self.settings = settings or {}
        self.is_visible = True
        self.tray_icon = None
        self.context_menu = None
        self.notification_queue: List[TrayNotification] = []
        self.notification_timer = QTimer()
        self.notification_timer.timeout.connect(self._process_notification_queue)
        self.notification_timer.setInterval(3000)  # 3 seconds between notifications

        # Initialize tray icon
        self._init_tray()

        self.logger.info("System tray manager initialized")

    def _init_tray(self) -> None:
        """Initialize the system tray icon and menu"""
        # Create context menu
        self.context_menu = QMenu()

        # Add menu items
        show_action = QAction("Show DualGPUOptimizer", self.context_menu)
        show_action.triggered.connect(self.show_app_requested.emit)
        self.context_menu.addAction(show_action)

        self.context_menu.addSeparator()

        # Launch models submenu
        self.launch_menu = self.context_menu.addMenu("Launch Model")
        self._update_launch_menu([])  # Empty initially, will be updated later

        self.context_menu.addSeparator()

        # Quick Actions
        reset_action = QAction("Reset GPU Memory", self.context_menu)
        reset_action.triggered.connect(lambda: self._reset_gpu_memory())
        self.context_menu.addAction(reset_action)

        self.context_menu.addSeparator()

        # Exit action
        exit_action = QAction("Exit", self.context_menu)
        exit_action.triggered.connect(self.exit_app_requested.emit)
        self.context_menu.addAction(exit_action)

        # Create tray icon
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setContextMenu(self.context_menu)

        # Set icon
        self._set_tray_icon()

        # Connect signals
        self.tray_icon.activated.connect(self._icon_activated)

        # Show the tray icon
        self.tray_icon.show()

    def _set_tray_icon(self) -> None:
        """Set the tray icon from available resources"""
        icon_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'resources', 'icon.png'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'icon.png'),
            os.path.join('resources', 'icon.png')
        ]

        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                self.logger.info(f"Using icon at: {icon_path}")
                try:
                    self.tray_icon.setIcon(QIcon(icon_path))
                    self.tray_icon.setToolTip("DualGPUOptimizer")
                    return
                except Exception as e:
                    self.logger.warning(f"Failed to set tray icon: {e}")

        # Fallback: create a simple colored icon
        self.logger.warning("No tray icon found, using fallback")
        pixmap = QPixmap(QSize(32, 32))
        pixmap.fill(Qt.transparent)
        icon = QIcon(pixmap)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("DualGPUOptimizer")

    def _icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_app_requested.emit()

    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Update settings for the tray manager"""
        self.settings = settings

    def show_notification(self, title: str, message: str,
                          icon_type: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.Information,
                          show_immediately: bool = False) -> None:
        """Show a notification from the tray icon

        Args:
            title: Notification title
            message: Notification message
            icon_type: Icon type (Information, Warning, Critical)
            show_immediately: If True, show immediately; otherwise queue
        """
        if not self.tray_icon.supportsMessages():
            self.logger.warning("System tray notifications not supported")
            return

        notification = TrayNotification(title, message, icon_type)

        if show_immediately:
            self._show_notification(notification)
        else:
            self.notification_queue.append(notification)

            # Start the timer if not already running
            if not self.notification_timer.isActive():
                self.notification_timer.start()

    def _show_notification(self, notification: TrayNotification) -> None:
        """Show a single notification"""
        self.tray_icon.showMessage(
            notification.title,
            notification.message,
            notification.icon_type,
            5000  # Display for 5 seconds
        )

    def _process_notification_queue(self) -> None:
        """Process the next notification in the queue"""
        if self.notification_queue:
            notification = self.notification_queue.pop(0)
            self._show_notification(notification)

        # Stop timer if queue is empty
        if not self.notification_queue:
            self.notification_timer.stop()

    def update_metrics(self, metrics_list: List[Dict[str, Any]]) -> None:
        """Update tray tooltip with current GPU metrics

        Args:
            metrics_list: List of GPU metrics dicts
        """
        if not self.tray_icon:
            return

        # Create tooltip text with formatted metrics
        tooltip = "DualGPUOptimizer\n"

        for i, metrics in enumerate(metrics_list):
            name = metrics.get("name", f"GPU {i}")
            mem_used = metrics.get("memory_used", 0)
            mem_total = metrics.get("memory_total", 1)
            mem_percent = (mem_used / mem_total) * 100 if mem_total > 0 else 0
            util = metrics.get("utilization", 0)
            temp = metrics.get("temperature", 0)

            tooltip += f"\n{name}:\n"
            tooltip += f"Memory: {mem_used}/{mem_total} MB ({mem_percent:.1f}%)\n"
            tooltip += f"Util: {util}%, Temp: {temp}°C\n"

        self.tray_icon.setToolTip(tooltip)

        # Check for temperature alerts
        if self.settings.get("notify_temperature", True):
            threshold = self.settings.get("temperature_threshold", 80)
            for i, metrics in enumerate(metrics_list):
                temp = metrics.get("temperature", 0)
                if temp >= threshold:
                    self.show_notification(
                        "Temperature Warning",
                        f"GPU {i} temperature is {temp}°C (threshold: {threshold}°C)",
                        QSystemTrayIcon.Warning
                    )

        # Check for memory alerts
        if self.settings.get("notify_memory", True):
            threshold = self.settings.get("memory_threshold", 90)
            for i, metrics in enumerate(metrics_list):
                mem_used = metrics.get("memory_used", 0)
                mem_total = metrics.get("memory_total", 1)
                mem_percent = (mem_used / mem_total) * 100 if mem_total > 0 else 0

                if mem_percent >= threshold:
                    self.show_notification(
                        "Memory Warning",
                        f"GPU {i} memory usage is {mem_percent:.1f}% (threshold: {threshold}%)",
                        QSystemTrayIcon.Warning
                    )

    def _reset_gpu_memory(self) -> None:
        """Reset GPU memory from tray icon"""
        try:
            import torch
            torch.cuda.empty_cache()
            self.show_notification("Memory Reset", "GPU memory cache has been reset", QSystemTrayIcon.Information, True)
            self.logger.info("Reset GPU memory from tray icon")
        except ImportError:
            self.show_notification("Error", "PyTorch not available for memory reset", QSystemTrayIcon.Warning, True)
            self.logger.warning("PyTorch not available for memory reset (tray)")
        except Exception as e:
            self.show_notification("Error", f"Failed to reset GPU memory: {e}", QSystemTrayIcon.Critical, True)
            self.logger.error(f"Error resetting GPU memory from tray: {e}")

    def _update_launch_menu(self, models: List[str]) -> None:
        """Update the launch model submenu with available models

        Args:
            models: List of model names
        """
        # Clear existing items
        self.launch_menu.clear()

        if not models:
            no_models_action = QAction("No models available", self.launch_menu)
            no_models_action.setEnabled(False)
            self.launch_menu.addAction(no_models_action)
            return

        # Add model actions
        for model in models:
            model_action = QAction(model, self.launch_menu)
            model_action.triggered.connect(lambda checked=False, m=model: self.launch_model_requested.emit(m))
            self.launch_menu.addAction(model_action)

    def update_available_models(self, models: List[str]) -> None:
        """Update available models in the launch menu

        Args:
            models: List of model names
        """
        self._update_launch_menu(models)

    def set_visible(self, visible: bool) -> None:
        """Set visibility of the tray icon

        Args:
            visible: Whether the tray icon should be visible
        """
        if self.tray_icon:
            if visible:
                self.tray_icon.show()
            else:
                self.tray_icon.hide()
            self.is_visible = visible

    def cleanup(self) -> None:
        """Clean up resources used by the tray icon"""
        if self.notification_timer.isActive():
            self.notification_timer.stop()

        if self.tray_icon:
            self.tray_icon.hide()
            del self.tray_icon
            self.tray_icon = None