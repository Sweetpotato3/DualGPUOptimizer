"""
Configuration service for DualGPUOptimizer
"""
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger("DualGPUOpt.ConfigService")

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
                with open(self.config_file, "r") as f:
                    loaded_config = json.load(f)
                    # Update config with loaded values
                    self.config.update(loaded_config)
                    logger.info(f"Loaded configuration from {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")

    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
                logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

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
        self.config[key] = value
        self.save()

# Singleton instance
config_service = ConfigService()
