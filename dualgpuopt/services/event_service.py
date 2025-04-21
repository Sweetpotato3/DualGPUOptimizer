"""
Event service for application-wide event handling.
Enables communication between components without direct coupling.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Dict, List, Any, Callable, Optional

logger = logging.getLogger("DualGPUOpt.EventService")

class EventBus:
    """Central event bus for application-wide events."""
    
    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()
        self._event_history: Dict[str, Dict[str, Any]] = {}
        self._max_history = 10
        logger.debug("Event bus initialized")
    
    def subscribe(self, event_name: str, callback: Callable) -> None:
        """
        Subscribe to an event.
        
        Args:
            event_name: Name of the event to subscribe to
            callback: Function to call when event is published
        """
        with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            
            if callback not in self._subscribers[event_name]:
                self._subscribers[event_name].append(callback)
                logger.debug(f"Subscribed to event: {event_name}")
    
    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        """
        Unsubscribe from an event.
        
        Args:
            event_name: Name of the event to unsubscribe from
            callback: Function to remove from subscribers
        """
        with self._lock:
            if event_name in self._subscribers and callback in self._subscribers[event_name]:
                self._subscribers[event_name].remove(callback)
                logger.debug(f"Unsubscribed from event: {event_name}")
    
    def publish(self, event_name: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Publish an event.
        
        Args:
            event_name: Name of the event to publish
            data: Event data to publish
        """
        if data is None:
            data = {}
        
        with self._lock:
            # Store in history
            self._event_history[event_name] = {
                "data": data, 
                "timestamp": time.time()
            }
            
            # Trim history if needed
            if len(self._event_history) > self._max_history:
                oldest = min(self._event_history.items(), key=lambda x: x[1]["timestamp"])[0]
                del self._event_history[oldest]
            
            # Get subscribers
            subscribers = self._subscribers.get(event_name, []).copy()
        
        # Call subscribers without holding the lock
        for callback in subscribers:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_name}: {e}")
        
        logger.debug(f"Published event: {event_name} with {len(subscribers)} subscribers")
    
    def get_last_event(self, event_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the data from the last occurrence of an event.
        
        Args:
            event_name: Name of the event
            
        Returns:
            Event data or None if no event found
        """
        with self._lock:
            if event_name in self._event_history:
                return self._event_history[event_name]["data"]
        return None

# Create global event bus instance
event_bus = EventBus()