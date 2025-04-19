"""
Configuration service for managing application settings.
"""
from __future__ import annotations

import json
import logging
import pathlib
from typing import Dict, Any, Optional

from dualgpuopt.services.event_service import event_bus


class ConfigService:
    """Service for handling configuration operations."""
    
    DEFAULT_CONFIG = {
        "theme": "dark",
        "ttk_theme": "",
        "start_minimized": False,
        "idle_alerts": True,
        "idle_threshold": 30,
        "idle_time": 5,
        "last_model": "",
        "context_size": 65536,
        "gpu_overclock": {}
    }
    
    def __init__(self, config_path: Optional[pathlib.Path] = None) -> None:
        """
        Initialize the configuration service.
        
        Args:
            config_path: Optional custom config path
        """
        self.logger = logging.getLogger("dualgpuopt.services.config")
        
        # Set default config path if not provided
        if config_path is None:
            self.config_path = pathlib.Path.home() / ".dualgpuopt" / "config.json"
        else:
            self.config_path = config_path
            
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default.
        
        Returns:
            Configuration dictionary
        """
        if not self.config_path.exists():
            self.logger.info(f"Config file not found, creating default at {self.config_path}")
            return self.DEFAULT_CONFIG.copy()
            
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                
            # Ensure all default keys are present
            for key, value in self.DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
                    
            return config
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Error loading config: {e}")
            return self.DEFAULT_CONFIG.copy()
    
    def save(self) -> bool:
        """
        Save the current configuration to file.
        
        Returns:
            Success status
        """
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Configuration saved to {self.config_path}")
            
            # Notify that config was saved
            event_bus.publish("config_saved", self.config)
            return True
        except IOError as e:
            self.logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any, save_immediately: bool = True) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            save_immediately: Whether to save to disk immediately
        """
        old_value = self.config.get(key)
        self.config[key] = value
        
        # Notify if value changed
        if old_value != value:
            self.logger.debug(f"Configuration changed: {key}")
            event_bus.publish(f"config_changed:{key}", value)
            event_bus.publish("config_changed", {"key": key, "value": value})
        
        # Save if requested
        if save_immediately:
            self.save()
    
    def update(self, new_config: Dict[str, Any], save_immediately: bool = True) -> None:
        """
        Update multiple configuration values.
        
        Args:
            new_config: Dictionary of updates
            save_immediately: Whether to save to disk immediately
        """
        changed_keys = []
        
        for key, value in new_config.items():
            if self.config.get(key) != value:
                self.config[key] = value
                changed_keys.append(key)
        
        # Notify of changes
        if changed_keys:
            self.logger.debug(f"Multiple configurations changed: {', '.join(changed_keys)}")
            event_bus.publish("config_updated", {"keys": changed_keys, "config": self.config})
        
        # Save if requested
        if save_immediately and changed_keys:
            self.save()

# Create a global config instance
config_service = ConfigService() 