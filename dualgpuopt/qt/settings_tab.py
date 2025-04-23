"""
Settings tab for DualGPUOptimizer Qt implementation.
Provides configuration options for the application.
"""

import logging
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Signal, Qt, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# Import shared constants
from dualgpuopt.qt.shared_constants import PAD, DEFAULT_FONT, DEFAULT_FONT_SIZE

# Import config service
try:
    from dualgpuopt.services.config_service import get_config_service
except ImportError:
    get_config_service = None

logger = logging.getLogger("DualGPUOptimizer.Settings")

# Default settings
DEFAULT_SETTINGS = {
    "theme": "dark_purple",
    "minimize_to_tray": True,
    "poll_interval": 1000,  # milliseconds
    "notify_temperature": True,
    "temperature_threshold": 80,
    "notify_memory": True,
    "memory_threshold": 90,  # percentage
    "auto_cleanup": True,
    "default_model_dir": "",
    "log_level": "INFO",
}

THEMES = [
    {"id": "dark_purple", "name": "Dark Purple", "primary": "#8A54FD", "bg": "#2D1E40"},
    {"id": "dark_blue", "name": "Dark Blue", "primary": "#3498db", "bg": "#1E2A40"},
    {"id": "dark_green", "name": "Dark Green", "primary": "#2ecc71", "bg": "#1E402A"},
    {"id": "dark_red", "name": "Dark Red", "primary": "#e74c3c", "bg": "#401E1E"},
]


class SettingsManager:
    """Manages settings storage and retrieval"""

    def __init__(self):
        """Initialize settings manager"""
        self.config_service = get_config_service() if get_config_service else None
        self._default_settings = {
            "minimize_to_tray": True,
            "start_with_system": False,
            "check_for_updates": True,
            "poll_interval": 1000,
            "temperature_alert": 80,
            "memory_alert": 90,
            "theme": "dark",
        }

    def get_settings(self) -> Dict[str, Any]:
        """
        Get current settings

        Returns
        -------
            Dictionary of settings

        """
        if self.config_service:
            settings = self.config_service.get("settings", {})
            # Apply defaults for missing settings
            for key, value in self._default_settings.items():
                if key not in settings:
                    settings[key] = value
            return settings
        return self._default_settings

    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Save settings

        Args:
        ----
            settings: Settings dictionary

        Returns:
        -------
            True if successful, False otherwise

        """
        if self.config_service:
            self.config_service.set("settings", settings)
            return self.config_service.save()
        return False


class SettingsSection(QFrame):
    """Base class for a settings section"""

    settings_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            """
            SettingsSection {
                background-color: #372952;
                border-radius: 8px;
                padding: 8px;
            }
        """,
        )

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        """Apply settings to UI controls"""

    def get_settings(self) -> Dict[str, Any]:
        """Get settings from UI controls"""
        return {}


class AppearanceSettings(SettingsSection):
    """Settings section for appearance settings"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Section title
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)

        title = QLabel("Appearance Settings")
        title.setFont(title_font)
        layout.addWidget(title)

        # Settings form
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(12)
        form_layout.setHorizontalSpacing(24)

        # Theme selector
        self.theme_combo = QComboBox()
        for theme in THEMES:
            self.theme_combo.addItem(theme["name"], theme["id"])
        form_layout.addRow("Theme:", self.theme_combo)

        # Minimize to tray option
        self.minimize_checkbox = QCheckBox("Minimize to system tray when closed")
        form_layout.addRow("", self.minimize_checkbox)

        layout.addLayout(form_layout)

        # Add spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        # Set theme
        theme_id = settings.get("theme", "dark_purple")
        index = self.theme_combo.findData(theme_id)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        # Set minimize to tray
        self.minimize_checkbox.setChecked(settings.get("minimize_to_tray", True))

    def get_settings(self) -> Dict[str, Any]:
        return {
            "theme": self.theme_combo.currentData(),
            "minimize_to_tray": self.minimize_checkbox.isChecked(),
        }


class MonitoringSettings(SettingsSection):
    """Settings section for monitoring settings"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Section title
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)

        title = QLabel("Monitoring Settings")
        title.setFont(title_font)
        layout.addWidget(title)

        # Settings form
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(12)
        form_layout.setHorizontalSpacing(24)

        # Poll interval
        self.poll_interval = QSpinBox()
        self.poll_interval.setMinimum(100)
        self.poll_interval.setMaximum(10000)
        self.poll_interval.setSingleStep(100)
        self.poll_interval.setSuffix(" ms")
        form_layout.addRow("Poll Interval:", self.poll_interval)

        # Temperature notifications
        self.notify_temp = QCheckBox()
        form_layout.addRow("Temperature Alerts:", self.notify_temp)

        # Temperature threshold
        self.temp_threshold = QSpinBox()
        self.temp_threshold.setMinimum(50)
        self.temp_threshold.setMaximum(100)
        self.temp_threshold.setSuffix(" °C")
        form_layout.addRow("Temperature Threshold:", self.temp_threshold)

        # Memory notifications
        self.notify_memory = QCheckBox()
        form_layout.addRow("Memory Alerts:", self.notify_memory)

        # Memory threshold
        self.memory_threshold = QSpinBox()
        self.memory_threshold.setMinimum(50)
        self.memory_threshold.setMaximum(100)
        self.memory_threshold.setSuffix(" %")
        form_layout.addRow("Memory Threshold:", self.memory_threshold)

        # Auto cleanup
        self.auto_cleanup = QCheckBox("Attempt memory cleanup when threshold exceeded")
        form_layout.addRow("", self.auto_cleanup)

        layout.addLayout(form_layout)

        # Add spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        self.poll_interval.setValue(settings.get("poll_interval", 1000))
        self.notify_temp.setChecked(settings.get("notify_temperature", True))
        self.temp_threshold.setValue(settings.get("temperature_threshold", 80))
        self.notify_memory.setChecked(settings.get("notify_memory", True))
        self.memory_threshold.setValue(settings.get("memory_threshold", 90))
        self.auto_cleanup.setChecked(settings.get("auto_cleanup", True))

    def get_settings(self) -> Dict[str, Any]:
        return {
            "poll_interval": self.poll_interval.value(),
            "notify_temperature": self.notify_temp.isChecked(),
            "temperature_threshold": self.temp_threshold.value(),
            "notify_memory": self.notify_memory.isChecked(),
            "memory_threshold": self.memory_threshold.value(),
            "auto_cleanup": self.auto_cleanup.isChecked(),
        }


class PathSettings(SettingsSection):
    """Settings section for path settings"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Section title
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)

        title = QLabel("Path Settings")
        title.setFont(title_font)
        layout.addWidget(title)

        # Model directory
        model_layout = QHBoxLayout()
        model_layout.setSpacing(8)

        self.model_dir_label = QLabel("Default Model Directory:")
        model_layout.addWidget(self.model_dir_label)

        self.model_dir = QLabel("Not set")
        self.model_dir.setStyleSheet("color: #A0A0A0;")
        model_layout.addWidget(self.model_dir, 1)

        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._browse_model_dir)
        model_layout.addWidget(self.browse_button)

        layout.addLayout(model_layout)

        # Logging level
        log_layout = QHBoxLayout()
        log_layout.setSpacing(8)

        log_label = QLabel("Log Level:")
        log_layout.addWidget(log_label)

        self.log_level = QComboBox()
        self.log_level.addItem("Debug", "DEBUG")
        self.log_level.addItem("Info", "INFO")
        self.log_level.addItem("Warning", "WARNING")
        self.log_level.addItem("Error", "ERROR")
        log_layout.addWidget(self.log_level)

        log_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout.addLayout(log_layout)

        # Add spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def _browse_model_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Default Model Directory",
            self.model_dir.text() if self.model_dir.text() != "Not set" else "",
        )

        if directory:
            self.model_dir.setText(directory)

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        model_dir = settings.get("default_model_dir", "")
        self.model_dir.setText(model_dir if model_dir else "Not set")

        log_level = settings.get("log_level", "INFO")
        index = self.log_level.findData(log_level)
        if index >= 0:
            self.log_level.setCurrentIndex(index)

    def get_settings(self) -> Dict[str, Any]:
        model_dir = self.model_dir.text()
        return {
            "default_model_dir": model_dir if model_dir != "Not set" else "",
            "log_level": self.log_level.currentData(),
        }


class SettingsTab(QWidget):
    """Settings tab for application configuration"""

    # Signals
    settings_applied = Signal(dict)  # Emitted when settings are applied

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the settings tab

        Args:
        ----
            parent: Parent widget

        """
        super().__init__(parent)

        # Create settings manager
        self.settings_manager = SettingsManager()

        # Get current settings
        self.settings = self.settings_manager.get_settings()

        # Setup UI
        self._setup_ui()

        # Load current settings
        self._load_settings()

    def _setup_ui(self):
        """Set up the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Settings")
        title_font = title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 2)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # General settings group
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout(general_group)

        # Minimize to tray
        self.minimize_checkbox = QCheckBox("Minimize to tray when closed")
        general_layout.addRow("", self.minimize_checkbox)

        # Start with system
        self.start_with_system = QCheckBox("Start with system")
        general_layout.addRow("", self.start_with_system)

        # Check for updates
        self.check_updates = QCheckBox("Check for updates on startup")
        general_layout.addRow("", self.check_updates)

        # Polling interval
        general_layout.addRow("Polling Interval (ms):", QLabel(""))
        self.poll_interval = QSpinBox()
        self.poll_interval.setRange(500, 5000)
        self.poll_interval.setSingleStep(100)
        self.poll_interval.setValue(1000)
        general_layout.addRow("", self.poll_interval)

        main_layout.addWidget(general_group)

        # Alert settings group
        alert_group = QGroupBox("Alert Settings")
        alert_layout = QFormLayout(alert_group)

        # Temperature alert
        alert_layout.addRow("Temperature Alert (°C):", QLabel(""))
        self.temp_alert = QSpinBox()
        self.temp_alert.setRange(60, 100)
        self.temp_alert.setValue(80)
        alert_layout.addRow("", self.temp_alert)

        # Memory alert
        alert_layout.addRow("Memory Usage Alert (%):", QLabel(""))
        self.memory_alert = QSpinBox()
        self.memory_alert.setRange(50, 100)
        self.memory_alert.setValue(90)
        alert_layout.addRow("", self.memory_alert)

        main_layout.addWidget(alert_group)

        # Appearance settings group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)

        # Theme selection
        appearance_layout.addRow("Theme:", QLabel(""))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        appearance_layout.addRow("", self.theme_combo)

        main_layout.addWidget(appearance_group)

        # Buttons layout
        buttons_layout = QHBoxLayout()

        # Apply button
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self._apply_settings)
        buttons_layout.addWidget(self.apply_button)

        # Reset button
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self._reset_settings)
        buttons_layout.addWidget(self.reset_button)

        main_layout.addLayout(buttons_layout)

        # Status label
        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

        # Add stretch to push everything to the top
        main_layout.addStretch(1)

    def _load_settings(self):
        """Load current settings into UI"""
        # General settings
        self.minimize_checkbox.setChecked(self.settings.get("minimize_to_tray", True))
        self.start_with_system.setChecked(self.settings.get("start_with_system", False))
        self.check_updates.setChecked(self.settings.get("check_for_updates", True))
        self.poll_interval.setValue(self.settings.get("poll_interval", 1000))

        # Alert settings
        self.temp_alert.setValue(self.settings.get("temperature_alert", 80))
        self.memory_alert.setValue(self.settings.get("memory_alert", 90))

        # Appearance settings
        theme = self.settings.get("theme", "dark")
        self.theme_combo.setCurrentText("Dark" if theme == "dark" else "Light")

    def _apply_settings(self):
        """Apply settings from UI"""
        # Update settings dictionary
        self.settings["minimize_to_tray"] = self.minimize_checkbox.isChecked()
        self.settings["start_with_system"] = self.start_with_system.isChecked()
        self.settings["check_for_updates"] = self.check_updates.isChecked()
        self.settings["poll_interval"] = self.poll_interval.value()
        self.settings["temperature_alert"] = self.temp_alert.value()
        self.settings["memory_alert"] = self.memory_alert.value()
        self.settings["theme"] = "dark" if self.theme_combo.currentText() == "Dark" else "light"

        # Save settings
        if self.settings_manager.save_settings(self.settings):
            self.status_label.setText("Settings saved successfully")
        else:
            self.status_label.setText("Failed to save settings")

        # Emit signal with settings
        self.settings_applied.emit(self.settings)

    def _reset_settings(self):
        """Reset settings to defaults"""
        # Reset settings to defaults
        self.settings = self.settings_manager._default_settings.copy()

        # Update UI
        self._load_settings()

        self.status_label.setText("Settings reset to defaults")
