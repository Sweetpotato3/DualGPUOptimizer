"""
System tray integration for DualGPUOptimizer
"""
import logging
import os
from typing import Optional, List, Dict, Any, Callable

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, Signal, QTimer, QSize, QObject

logger = logging.getLogger('DualGPUOptimizer')

class TrayNotification:
    """Data class for tray notification information"""
    
    def __init__(self, title: str, message: str, icon_type: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.Information):
        self.title = title
        self.message = message
        self.icon_type = icon_type

class GPUTrayManager(QObject):
    """Manages the system tray icon and notifications for the application"""
    
    # Signals
    show_app_requested = Signal()
    exit_app_requested = Signal()
    launch_model_requested = Signal(str)
    reset_gpu_memory_requested = Signal()
    
    def __init__(self, parent=None):
        """Initialize the tray manager
        
        Args:
            parent: Parent QObject
        """
        super().__init__(parent)
        
        self.tray_icon = None
        self.context_menu = None
        self.launch_menu = None
        self.is_visible = False
        
        # Queue for notifications
        self.notification_queue = []
        self.is_showing_notification = False
        
        # Setup notification timer
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self._process_notification_queue)
        self.notification_timer.setInterval(3000)  # 3 second delay between notifications
        
        # Initialize tray icon
        self._init_tray()
    
    def _init_tray(self):
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
        reset_action.triggered.connect(lambda: self.reset_gpu_memory_requested.emit())
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
        self.is_visible = True
        
        logger.info("System tray initialized")
    
    def _set_tray_icon(self):
        """Set the system tray icon"""
        # Check for icon files
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
                    self.tray_icon.setIcon(icon)
                    logger.info(f"Set tray icon from {path}")
                    return
                except Exception as e:
                    logger.warning(f"Failed to set tray icon from {path}: {e}")
        
        # If no icon file is found, create a basic icon
        self._create_basic_icon()
    
    def _create_basic_icon(self):
        """Create a basic icon when no icon file is available"""
        try:
            # Create a simple colored square icon
            pixmap = QPixmap(QSize(64, 64))
            pixmap.fill(Qt.darkMagenta)
            icon = QIcon(pixmap)
            self.tray_icon.setIcon(icon)
            logger.info("Created basic tray icon")
        except Exception as e:
            logger.error(f"Failed to create basic tray icon: {e}")
    
    def _icon_activated(self, reason):
        """Handle tray icon activation
        
        Args:
            reason: The activation reason
        """
        if reason == QSystemTrayIcon.DoubleClick:
            # Show the main window
            self.show_app_requested.emit()
    
    def show_notification(self, title: str, message: str, icon_type: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.Information, show_immediately: bool = False):
        """Show a notification in the system tray
        
        Args:
            title: Notification title
            message: Notification message
            icon_type: Type of notification icon
            show_immediately: Whether to show immediately, bypassing the queue
        """
        notification = TrayNotification(title, message, icon_type)
        
        if show_immediately and self.tray_icon and not self.is_showing_notification:
            self._show_notification(notification)
        else:
            # Add to queue
            self.notification_queue.append(notification)
            
            # Start timer if not already running
            if not self.notification_timer.isActive():
                self.notification_timer.start()
    
    def _show_notification(self, notification: TrayNotification):
        """Show a notification
        
        Args:
            notification: The notification to show
        """
        if not self.tray_icon:
            logger.warning("Cannot show notification: no tray icon")
            return
        
        self.is_showing_notification = True
        self.tray_icon.showMessage(
            notification.title,
            notification.message,
            notification.icon_type,
            3000  # Show for 3 seconds
        )
        
    def _process_notification_queue(self):
        """Process pending notifications in the queue"""
        if not self.notification_queue:
            # Stop timer if queue is empty
            self.notification_timer.stop()
            self.is_showing_notification = False
            return
        
        # Get the next notification
        notification = self.notification_queue.pop(0)
        self._show_notification(notification)
    
    def update_metrics(self, metrics: List[Dict[str, Any]]):
        """Update metrics for display in tooltip
        
        Args:
            metrics: List of GPU metrics dictionaries
        """
        if not self.tray_icon:
            return
        
        # Create tooltip with GPU metrics
        tooltip = "DualGPUOptimizer\n\n"
        
        for i, gpu in enumerate(metrics):
            name = gpu.get("name", f"GPU {i}")
            util = gpu.get("utilization", 0)
            mem_used = gpu.get("memory_used", 0)
            mem_total = gpu.get("memory_total", 1)
            temp = gpu.get("temperature", 0)
            
            # Calculate memory percentage
            mem_percent = (mem_used / mem_total) * 100 if mem_total > 0 else 0
            
            tooltip += f"{name}:\n"
            tooltip += f"  Util: {util}%  Temp: {temp}°C\n"
            tooltip += f"  Mem: {mem_used}/{mem_total} MB ({mem_percent:.1f}%)\n\n"
        
        self.tray_icon.setToolTip(tooltip)
    
    def _update_launch_menu(self, models: List[str]):
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
    
    def update_available_models(self, models: List[str]):
        """Update available models in the launch menu
        
        Args:
            models: List of model names
        """
        self._update_launch_menu(models)
    
    def set_visible(self, visible: bool):
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
    
    def cleanup(self):
        """Clean up resources used by the tray icon"""
        if self.notification_timer.isActive():
            self.notification_timer.stop()
        
        if self.tray_icon:
            self.tray_icon.hide()
            del self.tray_icon
            self.tray_icon = None 