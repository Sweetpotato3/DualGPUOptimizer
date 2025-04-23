"""
Configuration handler for model launch settings.

This module handles saving, loading, and managing model launch configurations.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from dualgpuopt.services.config_service import config_service


class ConfigHandler:
    """Handler for model launch configurations."""

    def __init__(self, config_dir: Optional[str] = None) -> None:
        """
        Initialize the configuration handler.

        Args:
        ----
            config_dir: Directory to store configurations (defaults to user config dir)

        """
        self.logger = logging.getLogger("dualgpuopt.gui.launcher.config")

        # Default to config directory from config service
        self.config_dir = config_dir or config_service.config_dir
        self.config_file = os.path.join(self.config_dir, "launcher_configs.json")

        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)

        # Load existing configurations
        self.configs = self._load_configs()

    def _load_configs(self) -> dict[str, dict[str, Any]]:
        """
        Load configurations from file.

        Returns
        -------
            Dictionary of configurations

        """
        if not os.path.exists(self.config_file):
            return {}

        try:
            with open(self.config_file) as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading launch configurations: {e}")
            return {}

    def _save_configs(self) -> bool:
        """
        Save configurations to file.

        Returns
        -------
            True if saved successfully, False otherwise

        """
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.configs, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving launch configurations: {e}")
            return False

    def get_config(self, name: str) -> Optional[dict[str, Any]]:
        """
        Get a configuration by name.

        Args:
        ----
            name: Name of the configuration

        Returns:
        -------
            Configuration dictionary or None if not found

        """
        return self.configs.get(name)

    def save_config(self, name: str, config: dict[str, Any]) -> bool:
        """
        Save a configuration.

        Args:
        ----
            name: Name of the configuration
            config: Configuration dictionary

        Returns:
        -------
            True if saved successfully, False otherwise

        """
        self.configs[name] = config
        return self._save_configs()

    def delete_config(self, name: str) -> bool:
        """
        Delete a configuration.

        Args:
        ----
            name: Name of the configuration

        Returns:
        -------
            True if deleted successfully, False otherwise

        """
        if name in self.configs:
            del self.configs[name]
            return self._save_configs()
        return False

    def list_configs(self) -> list[str]:
        """
        List all available configurations.

        Returns
        -------
            List of configuration names

        """
        return list(self.configs.keys())

    def get_default_config(self, framework: str) -> dict[str, Any]:
        """
        Get default configuration for a framework.

        Args:
        ----
            framework: Framework to get default configuration for

        Returns:
        -------
            Default configuration dictionary

        """
        if framework == "llama.cpp":
            return {
                "ctx_size": 2048,
                "batch_size": 1,
                "threads": 4,
                "gpu_split": "auto",
            }
        if framework == "vllm":
            return {
                "tensor_parallel_size": "auto",
                "max_memory": "auto",
                "max_model_len": 8192,
            }
        return {}
