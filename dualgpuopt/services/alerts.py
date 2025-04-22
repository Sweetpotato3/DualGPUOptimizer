"""
Simplified alert system with only WARNING/CRITICAL levels
that integrates with tray notifications and dashboard badge.
"""
from __future__ import annotations
import logging
from typing import Literal, Optional
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSystemTrayIcon, QLabel
from PySide6.QtCore import QObject, Signal

log = logging.getLogger("alerts")

AlertLevel = Literal["WARNING", "CRITICAL"]
ALERT_COLORS = {"WARNING": "#f39c12", "CRITICAL": "#e74c3c"}

class AlertService(QObject):
    alert_signal = Signal(str, str)  # level, message
    
    def __init__(self):
        super().__init__()
        self._tray: Optional[QSystemTrayIcon] = None
        self._badge: Optional[QLabel] = None
        
    def setup(self, parent_statusbar, app_instance):
        # Create status bar badge
        self._badge = QLabel("")
        self._badge.setStyleSheet("padding:4px;font-weight:bold;color:white;")
        parent_statusbar.addPermanentWidget(self._badge)
        
        # Set up system tray
        self._tray = QSystemTrayIcon(QIcon(":/icons/gpu.png"), app_instance)
        self._tray.show()
        
        # Connect signal to update UI
        self.alert_signal.connect(self._update_ui)
        
    def alert(self, level: AlertLevel, message: str):
        """Send alert with specified level and message"""
        if level not in ALERT_COLORS:
            return
        
        log.warning("%s: %s", level, message)
        self.alert_signal.emit(level, message)
        
    def _update_ui(self, level: str, message: str):
        """Update UI elements with alert information"""
        if self._badge:
            self._badge.setStyleSheet(f"background:{ALERT_COLORS[level]};padding:4px;color:white;")
            self._badge.setText(message)
            
        if self._tray:
            self._tray.showMessage(level, message, QIcon(), 4000)

# Singleton instance
alert_service = AlertService() 