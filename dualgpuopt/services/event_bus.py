#!/usr/bin/env python3
"""
Enhanced event bus system for component communication.

Provides typed events, priority-based dispatch, and event handling.
"""
from __future__ import annotations

import dataclasses
import enum
import logging
import threading
import time
from typing import Any, Callable, Generic, TypeVar, Union

T = TypeVar("T")


class EventPriority(enum.IntEnum):
    """Priority levels for event handlers."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclasses.dataclass
class Event:
    """Base class for all typed events."""

    timestamp: float = dataclasses.field(default_factory=time.time)
    source: str = "system"


@dataclasses.dataclass
class GPUEvent(Event):
    """Base class for GPU-related events."""

    gpu_index: int = 0


@dataclasses.dataclass
class GPUMetricsEvent(GPUEvent):
    """Event fired when GPU metrics are updated."""

    utilization: float = 0.0
    memory_used: int = 0
    memory_total: int = 0
    temperature: float = 0.0
    power_draw: float = 0.0
    fan_speed: int = 0


@dataclasses.dataclass
class ModelSelectedEvent(Event):
    """Event fired when a model is selected."""

    model_name: str = ""
    model_path: str = ""
    context_length: int = 0


@dataclasses.dataclass
class SplitCalculatedEvent(Event):
    """Event fired when GPU split is calculated."""

    split_ratio: list[float] = dataclasses.field(default_factory=list)
    gpu_indexes: list[int] = dataclasses.field(default_factory=list)
    context_length: int = 0


@dataclasses.dataclass
class ConfigChangedEvent(Event):
    """Event fired when configuration changes."""

    config_key: str = ""
    new_value: Any = None
    old_value: Any = None


class EventCallback(Generic[T]):
    """Wrapper for event callbacks with priority."""

    def __init__(
        self,
        callback: Callable[[T], Any],
        priority: EventPriority = EventPriority.NORMAL,
    ):
        self.callback = callback
        self.priority = priority

    def __lt__(self, other: EventCallback) -> bool:
        """Compare for priority sorting."""
        if not isinstance(other, EventCallback):
            return NotImplemented
        return self.priority > other.priority  # Higher priority comes first


class EventBus:
    """
    Event bus with typed events and priorities.

    Features:
    - Typed event dispatching
    - Priority-based handler execution
    """

    def __init__(self) -> None:
        """Initialize the event bus."""
        self._subscribers: dict[type[Event], list[EventCallback]] = {}
        self._string_subscribers: dict[str, list[EventCallback]] = {}
        self._locked_types: set[type[Event]] = set()
        self._lock = threading.RLock()
        self.logger = logging.getLogger("DualGPUOpt.Services.Event")

    def subscribe_typed(
        self,
        event_type: type[T],
        callback: Callable[[T], Any],
        priority: EventPriority = EventPriority.NORMAL,
    ) -> None:
        """
        Subscribe to a typed event.

        Args:
        ----
            event_type: The type of event to subscribe to
            callback: Function to call when event is published
            priority: Priority level for this handler
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []

            cb = EventCallback(callback, priority)
            self._subscribers[event_type].append(cb)
            self._subscribers[event_type].sort()  # Sort by priority

            self.logger.debug(
                f"Subscribed to event '{event_type.__name__}' with " f"priority={priority.name}",
            )

    def subscribe(
        self,
        event_type: Union[str, type[Event]],
        callback: Callable[[Any], Any],
        priority: EventPriority = EventPriority.NORMAL,
    ) -> None:
        """
        Universal subscribe method supporting both string and typed events.

        Args:
        ----
            event_type: String event name or event type class
            callback: Function to call when event is published
            priority: Priority level for this handler
        """
        # Handle class types
        if isinstance(event_type, type) and issubclass(event_type, Event):
            self.subscribe_typed(event_type, callback, priority)
            return

        # Handle string types
        event_name = str(event_type)
        with self._lock:
            if event_name not in self._string_subscribers:
                self._string_subscribers[event_name] = []

            cb = EventCallback(callback, priority)
            self._string_subscribers[event_name].append(cb)
            self._string_subscribers[event_name].sort()  # Sort by priority

            self.logger.debug(
                f"Subscribed to event '{event_name}' with " f"priority={priority.name}",
            )

    def publish_typed(self, event: Event) -> None:
        """
        Publish a typed event to subscribers.

        Args:
        ----
            event: The event instance to publish
        """
        event_type = type(event)
        handlers: list[EventCallback] = []

        with self._lock:
            # Find all matching handlers (exact type or parent classes)
            for cls in event_type.__mro__:
                if cls in self._subscribers:
                    handlers.extend(self._subscribers[cls])

        if not handlers:
            self.logger.debug(f"No subscribers for event '{event_type.__name__}'")
            return

        self.logger.debug(
            f"Publishing event '{event_type.__name__}' to {len(handlers)} subscribers"
        )

        for handler in handlers:
            try:
                handler.callback(event)
            except Exception as e:
                self.logger.error(f"Error in event handler for '{event_type.__name__}': {e}")

    def publish(self, event_type: Union[str, type[Event], Event], data: Any = None) -> None:
        """
        Universal publish method supporting typed events and string events.

        Args:
        ----
            event_type: Either an event type, event instance, or string event name
            data: Optional data for string events
        """
        # Case 1: It's an Event instance
        if isinstance(event_type, Event):
            self.publish_typed(event_type)
            return

        # Case 2: It's an Event subclass
        if isinstance(event_type, type) and issubclass(event_type, Event):
            if data is None:
                data = {}
            self.publish_typed(event_type(**data))
            return

        # Case 3: It's a string event type
        event_name = str(event_type)
        if event_name not in self._string_subscribers:
            self.logger.debug(f"No subscribers for event '{event_name}'")
            return

        handlers = self._string_subscribers[event_name]
        self.logger.debug(f"Publishing event '{event_name}' to {len(handlers)} subscribers")

        for handler in handlers:
            try:
                handler.callback(data)
            except Exception as e:
                self.logger.error(f"Error in event handler for '{event_name}': {e}")

    def unsubscribe_typed(self, event_type: type[Event], callback: Callable) -> None:
        """
        Unsubscribe from a typed event.

        Args:
        ----
            event_type: Event type to unsubscribe from
            callback: Callback function to remove
        """
        with self._lock:
            if event_type not in self._subscribers:
                return

            # Find and remove the matching callback
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h.callback != callback
            ]
            self.logger.debug(f"Unsubscribed from event '{event_type.__name__}'")

    def unsubscribe(self, event_type: Union[str, type[Event]], callback: Callable) -> None:
        """
        Universal unsubscribe method supporting both string and typed events.

        Args:
        ----
            event_type: String event name or event type class
            callback: Callback to unsubscribe
        """
        if isinstance(event_type, type) and issubclass(event_type, Event):
            self.unsubscribe_typed(event_type, callback)
        else:
            event_name = str(event_type)
            with self._lock:
                if event_name not in self._string_subscribers:
                    return

                self._string_subscribers[event_name] = [
                    h for h in self._string_subscribers[event_name] if h.callback != callback
                ]
                self.logger.debug(f"Unsubscribed from event '{event_name}'")

    def publish_async(self, event: Event) -> None:
        """
        Publish an event asynchronously in a separate thread.

        Args:
        ----
            event: The event instance to publish
        """
        threading.Thread(
            target=self.publish_typed,
            args=(event,),
            daemon=True,
            name=f"EventThread-{type(event).__name__}",
        ).start()
        self.logger.debug(f"Started async thread for event '{type(event).__name__}'")

    def clear_all_subscribers(self) -> None:
        """Clear all subscribers (mainly for testing purposes)."""
        with self._lock:
            self._subscribers.clear()
            self._string_subscribers.clear()
            self.logger.debug("Cleared all event subscribers")


# Create a global event bus instance
event_bus = EventBus()
