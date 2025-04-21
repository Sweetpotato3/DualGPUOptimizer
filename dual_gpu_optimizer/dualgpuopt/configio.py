"""
Tiny helper to load / save user config to ~/.dualgpuopt/config.toml
"""
from __future__ import annotations
import os, tomllib, tomli_w, pathlib
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("dualgpuopt.config")

CFG_DIR = pathlib.Path.home() / ".dualgpuopt"
CFG_DIR.mkdir(exist_ok=True)
CFG_PATH = CFG_DIR / "config.toml"

# Default configuration
_DEFAULT = {
    "theme": "dark",
    "last_model": "",
    "ctx": 65536,
    "env_overrides": {},
    "fav_paths": [],
    "check_updates": True,
    "monitor_interval": 1.0,
    "alert_threshold": 30,  # % GPU utilization to trigger alert
    "alert_duration": 300,  # seconds of low utilization before alerting
}


def validate_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize configuration values.

    Args:
        cfg: Raw configuration dictionary

    Returns:
        Validated configuration with correct types
    """
    validated = _DEFAULT.copy()

    # Validate theme
    if "theme" in cfg and isinstance(cfg["theme"], str):
        if cfg["theme"] in ("dark", "light", "system"):
            validated["theme"] = cfg["theme"]

    # Validate strings
    for key in ("last_model",):
        if key in cfg and isinstance(cfg["last_model"], str):
            validated[key] = cfg[key]

    # Validate integers
    for key in ("ctx", "alert_threshold", "alert_duration"):
        if key in cfg and isinstance(cfg[key], int) and cfg[key] > 0:
            validated[key] = cfg[key]

    # Validate floats
    if "monitor_interval" in cfg:
        try:
            interval = float(cfg["monitor_interval"])
            if 0.1 <= interval <= 60.0:
                validated["monitor_interval"] = interval
        except (ValueError, TypeError):
            pass

    # Validate booleans
    if "check_updates" in cfg:
        validated["check_updates"] = bool(cfg["check_updates"])

    # Validate dictionary
    if "env_overrides" in cfg and isinstance(cfg["env_overrides"], dict):
        validated["env_overrides"] = {
            k: str(v) for k, v in cfg["env_overrides"].items()
        }

    # Validate lists
    if "fav_paths" in cfg and isinstance(cfg["fav_paths"], list):
        validated["fav_paths"] = [str(path) for path in cfg["fav_paths"] if str(path)]

    return validated


def load_cfg() -> dict:
    """
    Load configuration from file with fallback to defaults.

    Returns:
        Validated configuration dictionary
    """
    if not CFG_PATH.exists():
        logger.info(f"No config file found at {CFG_PATH}, using defaults")
        return _DEFAULT.copy()

    try:
        with CFG_PATH.open("rb") as fh:
            data = tomllib.load(fh)

        # Validate and merge with defaults
        validated = validate_config(data)
        logger.debug(f"Loaded configuration from {CFG_PATH}")
        return validated
    except Exception as err:
        logger.error(f"Failed to load config file: {err}")
        return _DEFAULT.copy()


def save_cfg(cfg: dict) -> None:
    """
    Save configuration to file after validation.

    Args:
        cfg: Configuration dictionary to save
    """
    # Validate before saving
    validated = validate_config(cfg)

    try:
        with CFG_PATH.open("wb") as fh:
            tomli_w.dump(validated, fh)
        logger.debug(f"Saved configuration to {CFG_PATH}")
    except Exception as err:
        logger.error(f"Failed to save config file: {err}")


def get_config_path() -> pathlib.Path:
    """Return the config directory path."""
    return CFG_DIR