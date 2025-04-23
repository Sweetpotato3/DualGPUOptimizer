"""
Event service for DualGPUOptimizer.
Provides event bus for component communication.
"""
import logging
from typing import Any, Callable, Dict, List, TypeVar

logger = logging.getLogger("DualGPUOpt.EventService")

# Type for event handlers
T = TypeVar("T")
EventHandler = Callable[[Any], None]
TypedEventHandler = Callable[[T], None]


class EventBus:
    """Simple event bus to facilitate communication between components"""

    def __init__(self):
        """Initialize event bus"""
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._typed_handlers: Dict[type, List[TypedEventHandler]] = {}
        logger.info("Event bus initialized")

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Subscribe to an event

        Args:
        ----
            event_type: Event type identifier
            handler: Function to call when event is published

        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.debug(f"Handler {handler.__name__} subscribed to {event_type}")

    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """
        Unsubscribe from an event

        Args:
        ----
            event_type: Event type identifier
            handler: Handler to remove

        Returns:
        -------
            True if handler was removed, False if not found

        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug(f"Handler {handler.__name__} unsubscribed from {event_type}")
            return True
        return False

    def publish(self, event_type: str, event_data: Any = None) -> None:
        """
        Publish an event

        Args:
        ----
            event_type: Event type identifier
            event_data: Data to pass to handlers

        """
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(event_data)
                except Exception as e:
                    logger.error(f"Error in event handler {handler.__name__} for {event_type}: {e}")

    def subscribe_typed(self, event_class: type, handler: TypedEventHandler) -> None:
        """
        Subscribe to events of a specific class

        Args:
        ----
            event_class: Event class to subscribe to
            handler: Function to call when event is published

        """
        if event_class not in self._typed_handlers:
            self._typed_handlers[event_class] = []

        if handler not in self._typed_handlers[event_class]:
            self._typed_handlers[event_class].append(handler)
            logger.debug(f"Handler {handler.__name__} subscribed to {event_class.__name__}")

    def unsubscribe_typed(self, event_class: type, handler: TypedEventHandler) -> bool:
        """
        Unsubscribe from events of a specific class

        Args:
        ----
            event_class: Event class to unsubscribe from
            handler: Handler to remove

        Returns:
        -------
            True if handler was removed, False if not found

        """
        if event_class in self._typed_handlers and handler in self._typed_handlers[event_class]:
            self._typed_handlers[event_class].remove(handler)
            logger.debug(f"Handler {handler.__name__} unsubscribed from {event_class.__name__}")
            return True
        return False

    def publish_typed(self, event: Any) -> None:
        """
        Publish a typed event

        Args:
        ----
            event: Event object to publish

        """
        event_class = event.__class__

        # Call handlers for this exact class
        if event_class in self._typed_handlers:
            for handler in self._typed_handlers[event_class]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in typed event handler for {event_class.__name__}: {e}")

        # Call handlers for parent classes (for inheritance)
        for cls in event_class.__mro__[1:]:  # Skip the class itself
            if cls in self._typed_handlers:
                for handler in self._typed_handlers[cls]:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Error in parent typed event handler for {cls.__name__}: {e}")


# Typed event classes
class GPUMetricsEvent:
    """Event for GPU metrics updates"""

    def __init__(
        self,
        gpu_index: int,
        utilization: int,
        memory_used: int,
        memory_total: int,
        temperature: int,
        power_draw: float,
        fan_speed: int,
    ):
        """
        Initialize GPU metrics event

        Args:
        ----
            gpu_index: GPU index (0-based)
            utilization: GPU utilization percentage
            memory_used: Used memory in MB
            memory_total: Total memory in MB
            temperature: Temperature in Celsius
            power_draw: Power usage in watts
            fan_speed: Fan speed percentage

        """
        self.gpu_index = gpu_index
        self.utilization = utilization
        self.memory_used = memory_used
        self.memory_total = memory_total
        self.temperature = temperature
        self.power_draw = power_draw
        self.fan_speed = fan_speed

    @property
    def memory_percent(self) -> float:
        """
        Get memory usage percentage

        Returns
        -------
            Memory usage percentage

        """
        if self.memory_total == 0:
            return 0.0
        return (self.memory_used / self.memory_total) * 100.0


# Singleton instance
event_bus = EventBus()
