"""
CPU-based implementation of the event bus.

This implementation ensures all event processing happens on CPU threads
to preserve GPU memory for model inference.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union

# Import the base event classes and types
from dualgpuopt.services.event_bus import (
    Event, EventCallback, EventPriority, GPUMetricsEvent
)

# Import resource manager
try:
    from dualgpuopt.services.resource_manager import get_resource_manager
    resource_manager = get_resource_manager()
    resource_manager_available = True
except ImportError:
    resource_manager_available = False

# Setup logger
logger = logging.getLogger("DualGPUOpt.Services.CPUEventBus")

# Type variable for generic event types
T = TypeVar('T', bound=Event)


class CPUEventBus:
    """
    Event bus implementation that processes all events on CPU threads.
    
    This implementation is designed to ensure that event handling does not
    consume GPU resources, preserving VRAM for model inference.
    """
    
    def __init__(self) -> None:
        """Initialize the CPU-based event bus."""
        self._subscribers: Dict[Type[Event], List[EventCallback]] = {}
        self._string_subscribers: Dict[str, List[EventCallback]] = {}
        self._locked_types: Set[Type[Event]] = set()
        self._lock = threading.RLock()
        self.logger = logging.getLogger("DualGPUOpt.Services.CPUEventBus")
        self.logger.info("Initialized CPU-based event bus")
        
    def subscribe_typed(
        self,
        event_type: Type[T],
        callback: Callable[[T], Any],
        priority: EventPriority = EventPriority.NORMAL
    ) -> None:
        """
        Subscribe to a typed event.
        
        Args:
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
                f"Subscribed to event '{event_type.__name__}' with "
                f"priority={priority.name}"
            )
            
    def subscribe(
        self,
        event_type: str,
        callback: Callable[[Any], Any],
        priority: EventPriority = EventPriority.NORMAL
    ) -> None:
        """
        Subscribe to a string-based event type.
        
        Args:
            event_type: The string name of the event
            callback: Function to call when event is published
            priority: Priority level for this handler
        """
        with self._lock:
            if event_type not in self._string_subscribers:
                self._string_subscribers[event_type] = []
                
            cb = EventCallback(callback, priority)
            self._string_subscribers[event_type].append(cb)
            self._string_subscribers[event_type].sort()  # Sort by priority
            
            self.logger.debug(
                f"Subscribed to event '{event_type}' with "
                f"priority={priority.name}"
            )
            
    def _process_typed_event(self, event: Event) -> None:
        """
        Process a typed event by calling all subscribers.
        This method runs on a CPU thread.
        
        Args:
            event: The event instance to process
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
            
        self.logger.debug(f"Processing event '{event_type.__name__}' with {len(handlers)} subscribers")
        
        for handler in handlers:
            try:
                handler.callback(event)
            except Exception as e:
                self.logger.error(f"Error in event handler for '{event_type.__name__}': {e}")
                
    def _process_string_event(self, event_name: str, data: Any) -> None:
        """
        Process a string event by calling all subscribers.
        This method runs on a CPU thread.
        
        Args:
            event_name: The name of the event
            data: The event data
        """
        if event_name not in self._string_subscribers:
            self.logger.debug(f"No subscribers for event '{event_name}'")
            return
            
        handlers = self._string_subscribers[event_name]
        self.logger.debug(f"Processing event '{event_name}' with {len(handlers)} subscribers")
        
        for handler in handlers:
            try:
                handler.callback(data)
            except Exception as e:
                self.logger.error(f"Error in event handler for '{event_name}': {e}")
    
    def publish_typed(self, event: Event) -> None:
        """
        Publish a typed event to subscribers.
        Processing will happen on a CPU thread.
        
        Args:
            event: The event instance to publish
        """
        # Run event processing on CPU thread
        if resource_manager_available:
            resource_manager.run_on_cpu(self._process_typed_event, event)
        else:
            # Fallback if resource manager isn't available
            self._process_typed_event(event)
    
    def publish(self, event_type: Union[str, Type[Event], Event], data: Any = None) -> None:
        """
        Universal publish method supporting typed events and string events.
        All processing happens on CPU threads.
        
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
        
        # Run event processing on CPU thread
        if resource_manager_available:
            resource_manager.run_on_cpu(self._process_string_event, event_name, data)
        else:
            # Fallback if resource manager isn't available
            self._process_string_event(event_name, data)
            

# Create a singleton instance
_cpu_event_bus: Optional[CPUEventBus] = None


def get_cpu_event_bus() -> CPUEventBus:
    """
    Get the singleton CPU event bus instance.
    
    Returns:
        The CPU event bus instance
    """
    global _cpu_event_bus
    if _cpu_event_bus is None:
        _cpu_event_bus = CPUEventBus()
    return _cpu_event_bus 