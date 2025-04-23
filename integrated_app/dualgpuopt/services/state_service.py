"""
State management service for centralized application state.
"""
from __future__ import annotations

import json
import logging
import pathlib
from typing import Any, Optional

from dualgpuopt.services.event_bus import event_bus


class AppState:
    """Central state store for the application."""

    def __init__(self) -> None:
        """Initialize the application state."""
        self._state: dict[str, Any] = {
            "model_path": "",
            "context_size": 65536,
            "gpu_settings": {},
            "theme": "dark",
            "ttk_theme": "",
            "idle_detection": True,
            "idle_threshold": 30,
            "idle_time": 5,
            "last_model": "",
            "start_minimized": False,
            "gpu_overclock": {},
        }
        self.logger = logging.getLogger("dualgpuopt.services.state")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the state.

        Args:
        ----
            key: The state key to retrieve
            default: Default value if key doesn't exist

        Returns:
        -------
            The state value or default

        """
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the state and notify listeners.

        Args:
        ----
            key: The state key to set
            value: The value to set

        """
        old_value = self._state.get(key)
        self._state[key] = value

        # Only publish event if value actually changed
        if old_value != value:
            self.logger.debug(f"State changed: {key}")
            # Publish a specific event for this key
            event_bus.publish(f"state_changed:{key}", value)
            # Also publish a general state changed event
            event_bus.publish("state_changed", {"key": key, "value": value})

    def update(self, new_state: dict[str, Any]) -> None:
        """
        Update multiple state values at once.

        Args:
        ----
            new_state: Dictionary of state updates

        """
        for key, value in new_state.items():
            self.set(key, value)

    def save_to_disk(self, filepath: Optional[pathlib.Path] = None) -> None:
        """
        Save the current state to disk.

        Args:
        ----
            filepath: Optional custom filepath

        """
        if filepath is None:
            filepath = pathlib.Path.home() / ".dualgpuopt" / "app_state.json"

        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Save state
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2)
            self.logger.info(f"State saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving state to {filepath}: {e}")

    def load_from_disk(self, filepath: Optional[pathlib.Path] = None) -> None:
        """
        Load state from disk.

        Args:
        ----
            filepath: Optional custom filepath

        """
        if filepath is None:
            filepath = pathlib.Path.home() / ".dualgpuopt" / "app_state.json"

        if not filepath.exists():
            self.logger.info(f"State file {filepath} not found, using defaults")
            return

        try:
            with open(filepath, encoding="utf-8") as f:
                loaded_state = json.load(f)
                self.update(loaded_state)
            self.logger.info(f"State loaded from {filepath}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing state file {filepath}: {e}")
        except OSError as e:
            self.logger.error(f"Error reading state file {filepath}: {e}")


# Create a global state instance
app_state = AppState()
