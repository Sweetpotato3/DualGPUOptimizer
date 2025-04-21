"""
Configuration service for DualGPUOptimizer
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("DualGPUOpt.ConfigService")

# Import event bus if available
try:
    from dualgpuopt.services.event_bus import event_bus, ConfigChangedEvent
    event_bus_available = True
    logger.debug("Event bus available for configuration events")
except ImportError:
    event_bus_available = False
    logger.warning("Event bus not available for configuration events")

# Import resource manager if available
try:
    from dualgpuopt.services.resource_manager import ResourceManager
    resource_manager_available = True
    logger.debug("Resource manager available for configuration processing")
except ImportError:
    resource_manager_available = False
    logger.warning("Resource manager not available for configuration processing")

class ConfigService:
    """Service for managing application configuration"""

    def __init__(self):
        """Initialize config service with default values"""
        self.config = {
            "theme": "dark_purple",
            "gpu_layers": -1,
            "context_size": 4096,
            "thread_count": 8,
            "last_model_path": "",
            "gpu_split": "0.60,0.40"
        }

        # Config file path in user directory
        self.config_dir = Path.home() / ".dualgpuopt"
        self.config_file = self.config_dir / "config.json"

        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)

        # Load configuration from file
        self.load()

    def load(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                # Use resource manager to offload file loading to CPU if available
                if resource_manager_available:
                    resource_manager = ResourceManager.get_instance()
                    if resource_manager.should_use_cpu("configuration"):
                        loaded_config = resource_manager.run_on_cpu(self._cpu_load_config)
                        self.config.update(loaded_config)
                        logger.info(f"Loaded configuration from {self.config_file} (CPU)")
                        return

                # Default loading method
                loaded_config = self._cpu_load_config()
                self.config.update(loaded_config)
                logger.info(f"Loaded configuration from {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")

    def _cpu_load_config(self) -> Dict[str, Any]:
        """CPU-optimized configuration loading

        Returns:
            Loaded configuration dictionary
        """
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                return json.load(f)
        return {}

    def save(self):
        """Save configuration to file"""
        try:
            # Use resource manager to offload file saving to CPU if available
            if resource_manager_available:
                resource_manager = ResourceManager.get_instance()
                if resource_manager.should_use_cpu("configuration"):
                    success = resource_manager.run_on_cpu(self._cpu_save_config, self.config)
                    if success:
                        logger.info(f"Saved configuration to {self.config_file} (CPU)")
                    return

            # Default saving method
            success = self._cpu_save_config(self.config)
            if success:
                logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def _cpu_save_config(self, config_data: Dict[str, Any]) -> bool:
        """CPU-optimized configuration saving

        Args:
            config_data: Configuration data to save

        Returns:
            Success status
        """
        try:
            with open(self.config_file, "w") as f:
                json.dump(config_data, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error in CPU save: {e}")
            return False

    def get(self, key, default=None):
        """Get a configuration value

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def set(self, key, value):
        """Set a configuration value and save

        Args:
            key: Configuration key
            value: Configuration value
        """
        old_value = self.config.get(key)
        self.config[key] = value

        # Use resource manager for config processing if available
        if resource_manager_available:
            resource_manager = ResourceManager.get_instance()
            if resource_manager.should_use_cpu("configuration"):
                resource_manager.run_on_cpu(self._process_config_update, key, value, old_value)
                return

        # Default processing
        self.save()
        self._publish_config_change(key, value, old_value)

    def _process_config_update(self, key: str, value: Any, old_value: Any) -> None:
        """Process configuration update on CPU

        Args:
            key: Configuration key
            value: New value
            old_value: Previous value
        """
        self._cpu_save_config(self.config)
        self._publish_config_change(key, value, old_value)

    def _publish_config_change(self, key: str, new_value: Any, old_value: Any) -> None:
        """Publish configuration change event

        Args:
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
                old_value=old_value
            )
            event_bus.publish_typed(config_event)

            # Also publish as string event for non-typed subscribers
            event_bus.publish("config_changed", {
                "key": key,
                "value": new_value,
                "old_value": old_value
            })

            # Publish key-specific event for targeted subscribers
            event_bus.publish(f"config_changed.{key}", {
                "value": new_value,
                "old_value": old_value
            })

            logger.debug(f"Published config change event for key: {key}")
        except Exception as e:
            logger.error(f"Error publishing config change event: {e}")

# Singleton instance
config_service = ConfigService()
