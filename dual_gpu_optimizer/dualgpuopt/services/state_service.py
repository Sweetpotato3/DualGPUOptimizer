"""
State management service for centralized application state.
"""
from __future__ import annotations

import json
import logging
import pathlib
from typing import Dict, Any, Callable, List, Optional

<<<<<<< HEAD
from dualgpuopt.services.event_bus import event_bus
=======
from dualgpuopt.services.event_service import event_bus
>>>>>>> 3565cbc (Update documentation for DualGPUOptimizer to provide a comprehensive overview of GPU management, model optimization, execution management, and configuration handling. Enhanced descriptions for clarity and organized content for better readability. Adjusted glob patterns for improved file matching, ensuring accurate documentation coverage for multi-GPU setups in machine learning workloads.)


class AppState:
    """Central state store for the application."""

    def __init__(self) -> None:
        """Initialize the application state."""
        self._state: Dict[str, Any] = {
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
            key: The state key to retrieve
            default: Default value if key doesn't exist

        Returns:
            The state value or default
        """
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the state and notify listeners.

        Args:
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

    def update(self, new_state: Dict[str, Any]) -> None:
        """
        Update multiple state values at once.

        Args:
            new_state: Dictionary of state updates
        """
        for key, value in new_state.items():
            self.set(key, value)

    def save_to_disk(self, filepath: Optional[pathlib.Path] = None) -> None:
        """
        Save the current state to disk.

        Args:
            filepath: Optional custom filepath
        """
        if filepath is None:
            filepath = pathlib.Path.home() / ".dualgpuopt" / "app_state.json"

        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Save state
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._state, f, indent=2)
            self.logger.info(f"State saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving state to {filepath}: {e}")

    def load_from_disk(self, filepath: Optional[pathlib.Path] = None) -> None:
        """
        Load state from disk.

        Args:
            filepath: Optional custom filepath
        """
        if filepath is None:
            filepath = pathlib.Path.home() / ".dualgpuopt" / "app_state.json"

        if not filepath.exists():
            self.logger.info(f"State file {filepath} not found, using defaults")
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_state = json.load(f)
                self.update(loaded_state)
            self.logger.info(f"State loaded from {filepath}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing state file {filepath}: {e}")
        except IOError as e:
            self.logger.error(f"Error reading state file {filepath}: {e}")
<<<<<<< HEAD

    def save(self) -> None:
        """Save the current state to disk using the default path."""
        self.save_to_disk()


class StateService:
    """
    Service for managing application state with event-based updates.
    Provides a centralized way to manage state across the application.
    """

    def __init__(self) -> None:
        """Initialize the state service."""
        self.app_state = AppState()
        self.logger = logging.getLogger("dualgpuopt.services.state_service")
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}

        # Register for state change events
        event_bus.subscribe("state_changed", self._on_state_changed)

    def _on_state_changed(self, data: Dict[str, Any]) -> None:
        """Handle state change events internally."""
        key = data.get("key", "")
        value = data.get("value")

        # Notify subscribers for this key
        if key in self._subscribers:
            for callback in self._subscribers[key]:
                try:
                    callback(value)
                except Exception as e:
                    self.logger.error(f"Error in state subscriber callback: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from application state."""
        return self.app_state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in application state."""
        self.app_state.set(key, value)

    def update(self, state_updates: Dict[str, Any]) -> None:
        """Update multiple state values at once."""
        self.app_state.update(state_updates)

    def subscribe(self, key: str, callback: Callable[[Any], None]) -> None:
        """
        Subscribe to changes in a specific state key.

        Args:
            key: The state key to subscribe to
            callback: Function to call when state changes
        """
        if key not in self._subscribers:
            self._subscribers[key] = []
        self._subscribers[key].append(callback)

    def unsubscribe(self, key: str, callback: Callable[[Any], None]) -> None:
        """
        Unsubscribe from changes in a specific state key.

        Args:
            key: The state key to unsubscribe from
            callback: The callback to remove
        """
        if key in self._subscribers and callback in self._subscribers[key]:
            self._subscribers[key].remove(callback)

    def save_state(self, filepath: Optional[pathlib.Path] = None) -> None:
        """Save current state to disk."""
        self.app_state.save_to_disk(filepath)

    def load_state(self, filepath: Optional[pathlib.Path] = None) -> None:
        """Load state from disk."""
        self.app_state.load_from_disk(filepath)


# Create a global state instance
app_state = AppState()
# Create a global state service instance
state_service = StateService()
=======

# Create a global state instance
app_state = AppState()
>>>>>>> 3565cbc (Update documentation for DualGPUOptimizer to provide a comprehensive overview of GPU management, model optimization, execution management, and configuration handling. Enhanced descriptions for clarity and organized content for better readability. Adjusted glob patterns for improved file matching, ensuring accurate documentation coverage for multi-GPU setups in machine learning workloads.)
