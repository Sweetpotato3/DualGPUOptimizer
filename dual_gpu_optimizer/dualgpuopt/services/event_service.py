"""
Event bus system for component communication.
"""
from __future__ import annotations

import logging
from typing import Dict, Callable, List, Any

class EventBus:
    """Central event manager for component communication."""

    def __init__(self) -> None:
        """Initialize the event bus."""
        self._subscribers: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger("dualgpuopt.services.event")

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: The type of event to subscribe to
            callback: Function to call when the event is published
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        self.logger.debug(f"Subscribed to event '{event_type}'")

    def publish(self, event_type: str, data: Any = None) -> None:
        """
        Publish an event with optional data.

        Args:
            event_type: The type of event to publish
            data: Optional data to pass to subscribers
        """
        if event_type not in self._subscribers:
            self.logger.debug(f"No subscribers for event '{event_type}'")
            return

        self.logger.debug(f"Publishing event '{event_type}' to {len(self._subscribers[event_type])} subscribers")
        for callback in self._subscribers[event_type]:
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Error in event handler for '{event_type}': {e}")

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: The type of event to unsubscribe from
            callback: Function to remove from subscribers
        """
        if event_type in self._subscribers and callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
            self.logger.debug(f"Unsubscribed from event '{event_type}'")

# Create a global event bus
event_bus = EventBus()