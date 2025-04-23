"""
Unified Configuration System for DualGPUOptimizer

This module provides centralized configuration management for all aspects of the application:
- User preferences
- GPU settings
- UI options
- Models configuration
- System settings
"""
import json
import logging
import os
import threading
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger("DualGPUOpt.Config")

# Default configuration directories
if os.name == "nt":  # Windows
    DEFAULT_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".dualgpuopt")
else:  # Unix-like
    DEFAULT_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "dualgpuopt")

# Environment variable for config directory override
CONFIG_DIR_ENV = "DUALGPUOPT_CONFIG_DIR"


# Define configuration keys with categories
class ConfigCategory(Enum):
    """Categories for configuration settings"""

    CORE = "core"
    GPU = "gpu"
    UI = "ui"
    MODELS = "models"
    SYSTEM = "system"


class ConfigKey:
    """Configuration keys with metadata"""

    def __init__(
        self,
        name: str,
        category: ConfigCategory,
        default_value: Any,
        description: str = "",
        validator: Optional[callable] = None,
    ):
        self.name = name
        self.category = category
        self.default_value = default_value
        self.description = description
        self.validator = validator

    def __str__(self) -> str:
        return f"{self.category.value}.{self.name}"

    def validate(self, value: Any) -> bool:
        """
        Validate a value for this configuration key

        Args:
        ----
            value: Value to validate

        Returns:
        -------
            True if valid, False otherwise

        """
        if self.validator is None:
            return True

        try:
            return self.validator(value)
        except Exception:
            return False


# Core settings
MOCK_GPU = ConfigKey(
    "mock_gpu",
    ConfigCategory.CORE,
    False,
    "Enable mock GPU mode for testing without real GPUs",
    lambda x: isinstance(x, bool),
)

VERBOSE_LOGGING = ConfigKey(
    "verbose_logging",
    ConfigCategory.CORE,
    False,
    "Enable verbose logging",
    lambda x: isinstance(x, bool),
)

# GPU settings
GPU_COUNT = ConfigKey(
    "gpu_count",
    ConfigCategory.GPU,
    None,
    "Override detected GPU count (None for auto-detect)",
    lambda x: x is None or (isinstance(x, int) and x > 0),
)

POLL_INTERVAL = ConfigKey(
    "poll_interval",
    ConfigCategory.GPU,
    1.0,
    "Telemetry polling interval in seconds",
    lambda x: isinstance(x, (int, float)) and x > 0,
)

# UI settings
THEME = ConfigKey(
    "theme",
    ConfigCategory.UI,
    "default",
    "UI theme name",
    lambda x: isinstance(x, str),
)

FONT_SIZE = ConfigKey(
    "font_size",
    ConfigCategory.UI,
    12,
    "Base font size for UI",
    lambda x: isinstance(x, int) and 8 <= x <= 24,
)

# Models settings
DEFAULT_MODEL_PATH = ConfigKey(
    "default_model_path",
    ConfigCategory.MODELS,
    "",
    "Default model path",
    lambda x: isinstance(x, str),
)

MODEL_PRESETS = ConfigKey(
    "model_presets",
    ConfigCategory.MODELS,
    {},
    "Dictionary of model presets",
    lambda x: isinstance(x, dict),
)

# System settings
MAX_RECOVERY_ATTEMPTS = ConfigKey(
    "max_recovery_attempts",
    ConfigCategory.SYSTEM,
    3,
    "Maximum recovery attempts for errors",
    lambda x: isinstance(x, int) and x >= 0,
)

MEMORY_SAFETY_MARGIN = ConfigKey(
    "memory_safety_margin",
    ConfigCategory.SYSTEM,
    0.1,
    "Memory safety margin (0.0-1.0)",
    lambda x: isinstance(x, (int, float)) and 0 <= x <= 1,
)

# All configuration keys
ALL_CONFIG_KEYS = [
    # Core
    MOCK_GPU,
    VERBOSE_LOGGING,
    # GPU
    GPU_COUNT,
    POLL_INTERVAL,
    # UI
    THEME,
    FONT_SIZE,
    # Models
    DEFAULT_MODEL_PATH,
    MODEL_PRESETS,
    # System
    MAX_RECOVERY_ATTEMPTS,
    MEMORY_SAFETY_MARGIN,
]

# Create a lookup dictionary for faster access
CONFIG_KEYS_DICT = {str(key): key for key in ALL_CONFIG_KEYS}


class ConfigChangeEvent:
    """Event for configuration changes"""

    def __init__(self, key: str, old_value: Any, new_value: Any):
        self.key = key
        self.old_value = old_value
        self.new_value = new_value


class ConfigChangeListener:
    """Base class for configuration change listeners"""

    def on_config_changed(self, event: ConfigChangeEvent) -> None:
        """
        Called when a configuration value changes

        Args:
        ----
            event: Configuration change event

        """


class ConfigurationSystem:
    """Centralized configuration system"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigurationSystem, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration system

        Args:
        ----
            config_dir: Directory for configuration files

        """
        # Skip initialization if already initialized
        if self._initialized:
            return

        # Determine configuration directory
        if config_dir is None:
            config_dir = os.environ.get(CONFIG_DIR_ENV, DEFAULT_CONFIG_DIR)

        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"

        # Create directories if they don't exist
        self.config_dir.mkdir(exist_ok=True, parents=True)

        # Initialize configuration data
        self._config_data = {}
        self._listeners: Dict[str, List[ConfigChangeListener]] = {}
        self._initialized = True

        # Load configuration
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file"""
        if not self.config_file.exists():
            logger.info(f"Configuration file not found, creating default at {self.config_file}")
            self._create_default_config()
            return

        try:
            with open(self.config_file) as f:
                self._config_data = json.load(f)
            logger.info(f"Loaded configuration from {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._create_default_config()

    def _create_default_config(self) -> None:
        """Create default configuration"""
        # Create nested structure based on categories
        default_config = {}

        for key in ALL_CONFIG_KEYS:
            category = key.category.value
            if category not in default_config:
                default_config[category] = {}

            default_config[category][key.name] = key.default_value

        self._config_data = default_config
        self._save_config()

    def _save_config(self) -> bool:
        """
        Save configuration to file

        Returns
        -------
            True if successful, False otherwise

        """
        try:
            with open(self.config_file, "w") as f:
                json.dump(self._config_data, indent=4, sort_keys=True, default=str)
            logger.info(f"Saved configuration to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    def get(self, key: Union[ConfigKey, str], default: Any = None) -> Any:
        """
        Get a configuration value

        Args:
        ----
            key: Configuration key or string representation
            default: Default value if not found

        Returns:
        -------
            Configuration value or default if not found

        """
        # Convert string key to ConfigKey object if needed
        config_key = key if isinstance(key, ConfigKey) else CONFIG_KEYS_DICT.get(key)

        if config_key is None:
            logger.warning(f"Unknown configuration key: {key}")
            return default

        # Get value from config data
        category = config_key.category.value

        if category not in self._config_data:
            return config_key.default_value if default is None else default

        if config_key.name not in self._config_data[category]:
            return config_key.default_value if default is None else default

        return self._config_data[category][config_key.name]

    def set(self, key: Union[ConfigKey, str], value: Any) -> bool:
        """
        Set a configuration value

        Args:
        ----
            key: Configuration key or string representation
            value: New value

        Returns:
        -------
            True if successful, False otherwise

        """
        # Convert string key to ConfigKey object if needed
        config_key = key if isinstance(key, ConfigKey) else CONFIG_KEYS_DICT.get(key)

        if config_key is None:
            logger.warning(f"Unknown configuration key: {key}")
            return False

        # Validate value
        if not config_key.validate(value):
            logger.warning(f"Invalid value for {config_key}: {value}")
            return False

        # Get category and old value
        category = config_key.category.value
        old_value = self.get(config_key)

        # Update config data
        if category not in self._config_data:
            self._config_data[category] = {}

        self._config_data[category][config_key.name] = value

        # Save configuration
        success = self._save_config()

        # Notify listeners if successful
        if success:
            self._notify_listeners(str(config_key), old_value, value)

        return success

    def register_listener(
        self, key: Union[ConfigKey, str, None], listener: ConfigChangeListener
    ) -> None:
        """
        Register a listener for configuration changes

        Args:
        ----
            key: Configuration key to listen for changes to, or None for all changes
            listener: Listener to register

        """
        key_str = str(key) if key is not None else "*"

        if key_str not in self._listeners:
            self._listeners[key_str] = []

        self._listeners[key_str].append(listener)

    def unregister_listener(
        self, key: Union[ConfigKey, str, None], listener: ConfigChangeListener
    ) -> bool:
        """
        Unregister a listener

        Args:
        ----
            key: Configuration key the listener was registered for, or None for all changes
            listener: Listener to unregister

        Returns:
        -------
            True if the listener was found and removed, False otherwise

        """
        key_str = str(key) if key is not None else "*"

        if key_str not in self._listeners:
            return False

        try:
            self._listeners[key_str].remove(listener)
            return True
        except ValueError:
            return False

    def _notify_listeners(self, key: str, old_value: Any, new_value: Any) -> None:
        """
        Notify listeners of a configuration change

        Args:
        ----
            key: Key that changed
            old_value: Old value
            new_value: New value

        """
        event = ConfigChangeEvent(key, old_value, new_value)

        # Notify key-specific listeners
        if key in self._listeners:
            for listener in self._listeners[key]:
                try:
                    listener.on_config_changed(event)
                except Exception as e:
                    logger.error(f"Error in configuration listener: {e}")

        # Notify global listeners
        if "*" in self._listeners:
            for listener in self._listeners["*"]:
                try:
                    listener.on_config_changed(event)
                except Exception as e:
                    logger.error(f"Error in configuration listener: {e}")

    def reset_to_defaults(self, category: Optional[ConfigCategory] = None) -> bool:
        """
        Reset configuration to defaults

        Args:
        ----
            category: Category to reset, or None for all categories

        Returns:
        -------
            True if successful, False otherwise

        """
        if category is None:
            # Reset all categories
            self._create_default_config()
            return True

        category_value = category.value

        # Reset specific category
        default_config = {}

        for key in ALL_CONFIG_KEYS:
            if key.category == category:
                if category_value not in default_config:
                    default_config[category_value] = {}

                default_config[category_value][key.name] = key.default_value

        # Update config data
        self._config_data[category_value] = default_config[category_value]

        # Save configuration
        return self._save_config()

    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get all configuration settings as a flat dictionary

        Returns
        -------
            Dictionary of all settings

        """
        result = {}

        for key in ALL_CONFIG_KEYS:
            result[str(key)] = self.get(key)

        return result

    def import_from_dict(self, config_dict: Dict[str, Any]) -> bool:
        """
        Import configuration from a dictionary

        Args:
        ----
            config_dict: Dictionary of configuration values

        Returns:
        -------
            True if successful, False otherwise

        """
        success = True

        for key_str, value in config_dict.items():
            if key_str in CONFIG_KEYS_DICT:
                if not self.set(key_str, value):
                    success = False

        return success

    def export_to_file(self, file_path: str) -> bool:
        """
        Export configuration to a file

        Args:
        ----
            file_path: Path to export to

        Returns:
        -------
            True if successful, False otherwise

        """
        try:
            with open(file_path, "w") as f:
                json.dump(self._config_data, indent=4, sort_keys=True, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False

    def import_from_file(self, file_path: str) -> bool:
        """
        Import configuration from a file

        Args:
        ----
            file_path: Path to import from

        Returns:
        -------
            True if successful, False otherwise

        """
        try:
            with open(file_path) as f:
                new_config = json.load(f)

            # Validate and merge configuration
            for category, settings in new_config.items():
                if category not in self._config_data:
                    self._config_data[category] = {}

                for name, value in settings.items():
                    key_str = f"{category}.{name}"

                    if key_str in CONFIG_KEYS_DICT:
                        config_key = CONFIG_KEYS_DICT[key_str]

                        if config_key.validate(value):
                            old_value = self.get(config_key)
                            self._config_data[category][name] = value
                            self._notify_listeners(key_str, old_value, value)
                        else:
                            logger.warning(f"Invalid value for {key_str}: {value}")

            # Save configuration
            return self._save_config()
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False


# Global instance getter
def get_config_system() -> ConfigurationSystem:
    """
    Get the global configuration system instance

    Returns
    -------
        ConfigurationSystem instance

    """
    return ConfigurationSystem()


# Shorthand function for getting configuration values
def get_config(key: Union[ConfigKey, str], default: Any = None) -> Any:
    """
    Get a configuration value

    Args:
    ----
        key: Configuration key or string representation
        default: Default value if not found

    Returns:
    -------
        Configuration value or default if not found

    """
    return get_config_system().get(key, default)


# Shorthand function for setting configuration values
def set_config(key: Union[ConfigKey, str], value: Any) -> bool:
    """
    Set a configuration value

    Args:
    ----
        key: Configuration key or string representation
        value: New value

    Returns:
    -------
        True if successful, False otherwise

    """
    return get_config_system().set(key, value)
