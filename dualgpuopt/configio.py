"""
Configuration I/O module for DualGPUOptimizer
Provides functions for loading and saving configuration settings
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger("DualGPUOpt.ConfigIO")

# Default configuration
DEFAULT_CONFIG = {
    "theme": "neon_dark",
    "win": "1150x730",
    "start_minimized": False,
    "idle_alerts": True,
    "idle_threshold": 30,
    "idle_check_interval": 5,
    "last_model": "TheBloke/dolphin-2.2-yi-34b-200k-AWQ",
    "max_memory_percent": 95,
    "token_speed_sample_size": 20,
    "personas": {},
}


def get_config_path():
    """
    Get the path to the config file

    Returns
    -------
        Path: Path to the config file

    """
    # Try to use home directory for configuration
    home_dir = Path.home() / ".dualgpuopt"

    # Create directory if it doesn't exist
    try:
        home_dir.mkdir(exist_ok=True)
        return home_dir / "config.json"
    except Exception as e:
        logger.warning(f"Failed to create config directory in home: {e}")

    # Fallback to current directory if home directory is not accessible
    return Path("dualgpuopt_config.json")


def load_cfg():
    """
    Load configuration from file

    Returns
    -------
        dict: Configuration settings

    """
    config_path = get_config_path()
    config = DEFAULT_CONFIG.copy()

    try:
        if config_path.exists():
            with open(config_path) as f:
                user_config = json.load(f)
                config.update(user_config)
                logger.info(f"Loaded configuration from {config_path}")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")

    return config


def save_cfg(config_updates):
    """
    Save configuration to file

    Args:
    ----
        config_updates (dict): Configuration settings to update

    """
    config_path = get_config_path()

    try:
        # Load existing config first
        config = load_cfg()

        # Update with new values
        config.update(config_updates)

        # Save back to file
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Saved configuration to {config_path}")
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")


def get_value(key, default=None):
    """
    Get a specific configuration value

    Args:
    ----
        key (str): Configuration key
        default: Default value if key is not found

    Returns:
    -------
        Value for the specified key

    """
    config = load_cfg()
    return config.get(key, default)


def set_value(key, value):
    """
    Set a specific configuration value

    Args:
    ----
        key (str): Configuration key
        value: Value to set

    """
    save_cfg({key: value})
