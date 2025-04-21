"""
Enhanced event bus system for component communication.

Provides typed events, priority-based dispatch, and async event handling.
"""
from __future__ import annotations

import asyncio
import dataclasses
import enum
import inspect
import logging
import threading
import time
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Type, TypeVar, Union

T = TypeVar('T')


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
class ConfigChangedEvent(Event):
    """Event fired when configuration changes."""
    config_key: str = ""
    old_value: Any = None
    new_value: Any = None


@dataclasses.dataclass
class OptimizationEvent(Event):
    """Event for optimization-related notifications."""
    split_ratio: str = ""
    tensor_fractions: List[float] = dataclasses.field(default_factory=list)
    model_path: str = ""


class EventCallback(Generic[T]):
    """Wrapper for event callbacks with priority."""

    def __init__(
        self,
        callback: Callable[[T], Any],
        priority: EventPriority = EventPriority.NORMAL,
        is_async: bool = False
    ):
        self.callback = callback
        self.priority = priority
        self.is_async = is_async

    def __lt__(self, other: EventCallback) -> bool:
        """Compare for priority sorting."""
        if not isinstance(other, EventCallback):
            return NotImplemented
        return self.priority > other.priority  # Higher priority comes first


class EnhancedEventBus:
    """
    Enhanced event bus with typed events, priorities and async support.

    Features:
    - Typed event dispatching
    - Priority-based handler execution
    - Synchronous and asynchronous event handlers
    - Fire-and-forget async dispatch
    """

    def __init__(self) -> None:
        """Initialize the event bus."""
        self._subscribers: Dict[Type[Event], List[EventCallback]] = {}
        self._string_subscribers: Dict[str, List[EventCallback]] = {}
        self._locked_types: Set[Type[Event]] = set()
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._lock = threading.RLock()
        self.logger = logging.getLogger("dualgpuopt.services.event")

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create an event loop for async dispatching."""
        if self._event_loop is None or self._event_loop.is_closed():
            try:
                self._event_loop = asyncio.get_event_loop()
            except RuntimeError:
                self._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._event_loop)
        return self._event_loop

    def subscribe_typed(
        self,
        event_type: Type[T],
        callback: Callable[[T], Any],
        priority: EventPriority = EventPriority.NORMAL,
        is_async: bool = False
    ) -> None:
        """
        Subscribe to a typed event.

        Args:
            event_type: The type of event to subscribe to
            callback: Function to call when event is published
            priority: Priority level for this handler
            is_async: Whether the callback is a coroutine function
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []

            cb = EventCallback(callback, priority, is_async or inspect.iscoroutinefunction(callback))
            self._subscribers[event_type].append(cb)
            self._subscribers[event_type].sort()  # Sort by priority

            self.logger.debug(
                f"Subscribed to event '{event_type.__name__}' with "
                f"priority={priority.name}, async={cb.is_async}"
            )

    def subscribe(
        self,
        event_type: str,
        callback: Callable[[Any], Any],
        priority: EventPriority = EventPriority.NORMAL,
        is_async: bool = False
    ) -> None:
        """
        Subscribe to a string-based event type (for backward compatibility).

        Args:
            event_type: The string name of the event
            callback: Function to call when event is published
            priority: Priority level for this handler
            is_async: Whether the callback is a coroutine function
        """
        with self._lock:
            if event_type not in self._string_subscribers:
                self._string_subscribers[event_type] = []

            cb = EventCallback(callback, priority, is_async or inspect.iscoroutinefunction(callback))
            self._string_subscribers[event_type].append(cb)
            self._string_subscribers[event_type].sort()  # Sort by priority

            self.logger.debug(
                f"Subscribed to event '{event_type}' with "
                f"priority={priority.name}, async={cb.is_async}"
            )

    def lock_event_type(self, event_type: Type[Event]) -> None:
        """
        Lock an event type to prevent further subscriptions.

        Useful for security-critical event types where late subscription
        could pose security risks.

        Args:
            event_type: Event type to lock
        """
        with self._lock:
            self._locked_types.add(event_type)
            self.logger.debug(f"Locked event type '{event_type.__name__}'")

    def publish_typed(self, event: Event) -> None:
        """
        Publish a typed event to subscribers.

        Args:
            event: The event instance to publish
        """
        event_type = type(event)
        handlers: List[EventCallback] = []

        with self._lock:
            # Find all matching handlers (exact type or parent classes)
            for cls in event_type.__mro__:
                if cls in self._subscribers:
                    handlers.extend(self._subscribers[cls])

        if not handlers:
            self.logger.debug(f"No subscribers for event '{event_type.__name__}'")
            return

        self.logger.debug(f"Publishing event '{event_type.__name__}' to {len(handlers)} subscribers")

        for handler in handlers:
            try:
                if handler.is_async:
                    # Schedule coroutine on the event loop
                    self.get_event_loop().create_task(self._execute_async_handler(handler.callback, event))
                else:
                    handler.callback(event)
            except Exception as e:
                self.logger.error(f"Error in event handler for '{event_type.__name__}': {e}")

    async def _execute_async_handler(self, callback: Callable, event: Event) -> None:
        """Execute an async handler and log errors."""
        try:
            if inspect.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)
        except Exception as e:
            self.logger.error(f"Error in async event handler: {e}")

    def publish(self, event_type: Union[str, Type[Event], Event], data: Any = None) -> None:
        """
        Universal publish method supporting typed events and string events.

        Args:
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
                if handler.is_async:
                    self.get_event_loop().create_task(self._execute_async_handler(handler.callback, data))
                else:
                    handler.callback(data)
            except Exception as e:
                self.logger.error(f"Error in event handler for '{event_name}': {e}")

    def unsubscribe_typed(self, event_type: Type[Event], callback: Callable) -> None:
        """
        Unsubscribe from a typed event.

        Args:
            event_type: Event type to unsubscribe from
            callback: Callback function to remove
        """
        with self._lock:
            if event_type not in self._subscribers:
                return

            # Find and remove the matching callback
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type]
                if h.callback != callback
            ]
            self.logger.debug(f"Unsubscribed from event '{event_type.__name__}'")

    def unsubscribe(self, event_type: Union[str, Type[Event]], callback: Callable) -> None:
        """
        Universal unsubscribe method supporting both string and typed events.

        Args:
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
                    h for h in self._string_subscribers[event_name]
                    if h.callback != callback
                ]
                self.logger.debug(f"Unsubscribed from event '{event_name}'")

    def clear_all_subscribers(self) -> None:
        """Clear all subscribers (mainly for testing purposes)."""
        with self._lock:
            self._subscribers.clear()
            self._string_subscribers.clear()
            self.logger.debug("Cleared all event subscribers")


# Create a global event bus instance
event_bus = EnhancedEventBus()