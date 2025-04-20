"""
Event service for application-wide event handling
"""
from __future__ import annotations

import logging
from typing import Dict, List, Callable, Any

logger = logging.getLogger("DualGPUOpt.EventService")

class EventBus:
    """
    Central event bus for application-wide event handling
    Allows components to subscribe to events and publish events to subscribers
    """
    
    def __init__(self) -> None:
        """Initialize the event bus"""
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}
        self.logger = logging.getLogger("DualGPUOpt.EventService")
    
    def subscribe(self, event_name: str, callback: Callable[[Any], None]) -> None:
        """
        Subscribe to an event
        
        Args:
            event_name: Name of the event to subscribe to
            callback: Function to call when the event is published
        """
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        
        if callback not in self._subscribers[event_name]:
            self._subscribers[event_name].append(callback)
            self.logger.debug(f"Subscribed to event: {event_name}")
    
    def unsubscribe(self, event_name: str, callback: Callable[[Any], None]) -> None:
        """
        Unsubscribe from an event
        
        Args:
            event_name: Name of the event to unsubscribe from
            callback: Function to remove from subscribers
        """
        if event_name in self._subscribers and callback in self._subscribers[event_name]:
            self._subscribers[event_name].remove(callback)
            self.logger.debug(f"Unsubscribed from event: {event_name}")
    
    def publish(self, event_name: str, data: Any = None) -> None:
        """
        Publish an event to all subscribers
        
        Args:
            event_name: Name of the event to publish
            data: Data to pass to subscribers
        """
        if event_name in self._subscribers:
            for callback in self._subscribers[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"Error in event callback for {event_name}: {e}")
            
            self.logger.debug(f"Published event: {event_name} to {len(self._subscribers[event_name])} subscribers")

# Global event bus instance
event_bus = EventBus() 