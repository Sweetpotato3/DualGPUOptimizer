import logging
from typing import Dict, Any
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QComboBox, QCheckBox, QFrame,
                              QFormLayout, QSpinBox, QFileDialog, QMessageBox,
                              QSpacerItem, QSizePolicy)
from PySide6.QtCore import Signal, QSettings
from PySide6.QtGui import QFont

logger = logging.getLogger('DualGPUOptimizer')

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
    "log_level": "INFO"
}

THEMES = [
    {"id": "dark_purple", "name": "Dark Purple", "primary": "#8A54FD", "bg": "#2D1E40"},
    {"id": "dark_blue", "name": "Dark Blue", "primary": "#3498db", "bg": "#1E2A40"},
    {"id": "dark_green", "name": "Dark Green", "primary": "#2ecc71", "bg": "#1E402A"},
    {"id": "dark_red", "name": "Dark Red", "primary": "#e74c3c", "bg": "#401E1E"}
]

class SettingsManager:
    """Manages application settings persistence"""

    def __init__(self):
        self.settings = QSettings("DualGPUOptimizer", "Settings")
        self.current_settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from QSettings"""
        settings = DEFAULT_SETTINGS.copy()

        # Load each setting
        for key in DEFAULT_SETTINGS:
            if self.settings.contains(key):
                value = self.settings.value(key)

                # Convert string to bool if needed
                if isinstance(DEFAULT_SETTINGS[key], bool) and isinstance(value, str):
                    value = value.lower() in ("true", "1", "yes")

                # Convert string to int if needed
                if isinstance(DEFAULT_SETTINGS[key], int) and isinstance(value, str):
                    value = int(value)

                settings[key] = value

        return settings

    def save_settings(self, settings: Dict[str, Any]) -> None:
        """Save settings to QSettings"""
        self.current_settings = settings

        # Save each setting
        for key, value in settings.items():
            self.settings.setValue(key, value)

        self.settings.sync()
        logger.info("Settings saved successfully")

    def get_settings(self) -> Dict[str, Any]:
        """Get current settings"""
        return self.current_settings


class SettingsSection(QFrame):
    """Base class for a settings section"""

    settings_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            SettingsSection {
                background-color: #372952;
                border-radius: 8px;
                padding: 8px;
            }
        """)

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
            "minimize_to_tray": self.minimize_checkbox.isChecked()
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
            "auto_cleanup": self.auto_cleanup.isChecked()
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
            self, "Select Default Model Directory",
            self.model_dir.text() if self.model_dir.text() != "Not set" else ""
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
            "log_level": self.log_level.currentData()
        }


class SettingsTab(QWidget):
    """Settings tab allowing configuration of application preferences"""

    settings_applied = Signal(dict)

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('DualGPUOptimizer')
        self.logger.info("Initializing Settings tab")
        self.settings_manager = SettingsManager()
        self.current_settings = self.settings_manager.get_settings()
        self.setup_ui()
        self.apply_settings(self.current_settings)

    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header_layout = QHBoxLayout()

        # Title
        title = QLabel("Settings")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)

        # Spacer
        header_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        main_layout.addLayout(header_layout)

        # Description label
        desc_label = QLabel("Configure application preferences and behavior")
        desc_label.setStyleSheet("color: #A0A0A0;")
        main_layout.addWidget(desc_label)

        # Settings sections
        self.appearance_settings = AppearanceSettings(self)
        main_layout.addWidget(self.appearance_settings)

        self.monitoring_settings = MonitoringSettings(self)
        main_layout.addWidget(self.monitoring_settings)

        self.path_settings = PathSettings(self)
        main_layout.addWidget(self.path_settings)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        buttons_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        buttons_layout.addWidget(self.reset_button)

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self._apply_settings)
        buttons_layout.addWidget(self.apply_button)

        main_layout.addLayout(buttons_layout)

        self.logger.info("Settings UI setup complete")

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        """Apply settings to all sections"""
        self.appearance_settings.apply_settings(settings)
        self.monitoring_settings.apply_settings(settings)
        self.path_settings.apply_settings(settings)

    def _reset_to_defaults(self) -> None:
        """Reset all settings to defaults"""
        confirmation = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if confirmation == QMessageBox.Yes:
            self.apply_settings(DEFAULT_SETTINGS)
            self.logger.info("Settings reset to defaults")

    def _apply_settings(self) -> None:
        """Apply and save current settings"""
        # Collect settings from all sections
        settings = {}
        settings.update(self.appearance_settings.get_settings())
        settings.update(self.monitoring_settings.get_settings())
        settings.update(self.path_settings.get_settings())

        # Save settings
        self.settings_manager.save_settings(settings)

        # Emit signal with new settings
        self.settings_applied.emit(settings)

        QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")