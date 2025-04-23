"""
Configuration service for DualGPUOptimizer.
Manages persistent storage of application settings.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("DualGPUOpt.ConfigService")

# Import event bus if available
try:
    from dualgpuopt.services.event_bus import ConfigChangedEvent, event_bus

    event_bus_available = True
    logger.debug("Event bus available for configuration events")
except ImportError:
    event_bus_available = False
    logger.warning("Event bus not available for configuration events")


class ConfigService:
    """Service for managing application configuration"""

    def __init__(self, config_dir: Optional[str] = None, config_file: str = "config.json"):
        """
        Initialize the config service

        Args:
        ----
            config_dir: Directory for config files (defaults to ~/.dualgpuopt)
            config_file: Configuration file name

        """
        # Default to user home directory if not specified
        if config_dir is None:
            home_dir = os.path.expanduser("~")
            config_dir = os.path.join(home_dir, ".dualgpuopt")

        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / config_file
        self.config: Dict[str, Any] = {}

        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True, parents=True)

        # Load config
        self.load()

        logger.info(f"Config service initialized with config file: {self.config_file}")

    def load(self) -> bool:
        """
        Load configuration from file

        Returns
        -------
            True if loaded successfully, False otherwise

        """
        try:
            if self.config_file.exists():
                with open(self.config_file) as f:
                    self.config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return True
            logger.info(f"Config file {self.config_file} not found, using defaults")
            self.config = {}
            return False
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = {}
            return False

    def save(self) -> bool:
        """
        Save configuration to file

        Returns
        -------
            True if saved successfully, False otherwise

        """
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value

        Args:
        ----
            key: Configuration key
            default: Default value if key not found

        Returns:
        -------
            Configuration value or default

        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value

        Args:
        ----
            key: Configuration key
            value: Value to set

        """
        self.config[key] = value

    def delete(self, key: str) -> bool:
        """
        Delete configuration key

        Args:
        ----
            key: Configuration key

        Returns:
        -------
            True if key was deleted, False if not found

        """
        if key in self.config:
            del self.config[key]
            return True
        return False

    def _publish_config_change(self, key: str, new_value: Any, old_value: Any) -> None:
        """
        Publish configuration change event

        Args:
        ----
            key: Configuration key that changed
            new_value: New configuration value
            old_value: Previous configuration value

        """
        if not event_bus_available:
            return

        try:
            # Publish as typed event
            config_event = ConfigChangedEvent(
                config_key=key,
                new_value=new_value,
                old_value=old_value,
            )
            event_bus.publish_typed(config_event)

            # Also publish as string event for non-typed subscribers
            event_bus.publish(
                "config_changed",
                {
                    "key": key,
                    "value": new_value,
                    "old_value": old_value,
                },
            )

            # Publish key-specific event for targeted subscribers
            event_bus.publish(
                f"config_changed.{key}",
                {
                    "value": new_value,
                    "old_value": old_value,
                },
            )

            logger.debug(f"Published config change event for key: {key}")
        except Exception as e:
            logger.error(f"Error publishing config change event: {e}")


# Singleton instance
_config_service: Optional[ConfigService] = None


def get_config_service() -> ConfigService:
    """
    Get the config service singleton

    Returns
    -------
        Config service instance

    """
    global _config_service
    if _config_service is None:
        _config_service = ConfigService()
    return _config_service
