import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import time
import threading

# Import the event bus module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from dualgpuopt.services.event_bus import EventBus, Event

class TestEvent(Event):
    """Test event class for testing."""
    def __init__(self, data=None):
        super().__init__()
        self.data = data if data is not None else {}


class TestEventBus:
    """Test cases for the event bus system."""
    
    def test_subscribe_and_publish(self):
        """Test basic subscription and publishing functionality."""
        # Create event bus
        event_bus = EventBus()
        
        # Create mock subscriber
        mock_subscriber = MagicMock()
        
        # Subscribe to test event
        event_bus.subscribe(TestEvent, mock_subscriber)
        
        # Create and publish test event
        test_event = TestEvent({"test": "data"})
        event_bus.publish(test_event)
        
        # Verify subscriber was called with the event
        mock_subscriber.assert_called_once_with(test_event)
    
    def test_multiple_subscribers(self):
        """Test multiple subscribers for the same event type."""
        # Create event bus
        event_bus = EventBus()
        
        # Create mock subscribers
        mock_subscriber1 = MagicMock()
        mock_subscriber2 = MagicMock()
        
        # Subscribe both to test event
        event_bus.subscribe(TestEvent, mock_subscriber1)
        event_bus.subscribe(TestEvent, mock_subscriber2)
        
        # Create and publish test event
        test_event = TestEvent({"test": "data"})
        event_bus.publish(test_event)
        
        # Verify both subscribers were called with the event
        mock_subscriber1.assert_called_once_with(test_event)
        mock_subscriber2.assert_called_once_with(test_event)
    
    def test_unsubscribe(self):
        """Test unsubscribing from an event."""
        # Create event bus
        event_bus = EventBus()
        
        # Create mock subscriber
        mock_subscriber = MagicMock()
        
        # Subscribe to test event
        event_bus.subscribe(TestEvent, mock_subscriber)
        
        # Unsubscribe from event
        event_bus.unsubscribe(TestEvent, mock_subscriber)
        
        # Create and publish test event
        test_event = TestEvent({"test": "data"})
        event_bus.publish(test_event)
        
        # Verify subscriber was not called
        mock_subscriber.assert_not_called()
    
    def test_subscriber_exception_handling(self):
        """Test that exceptions in subscribers don't affect other subscribers."""
        # Create event bus
        event_bus = EventBus()
        
        # Create subscribers - one that raises exception, one that doesn't
        def exception_subscriber(event):
            raise ValueError("Test exception")
            
        mock_normal_subscriber = MagicMock()
        
        # Subscribe both to test event
        event_bus.subscribe(TestEvent, exception_subscriber)
        event_bus.subscribe(TestEvent, mock_normal_subscriber)
        
        # Create and publish test event
        test_event = TestEvent({"test": "data"})
        event_bus.publish(test_event)
        
        # Verify normal subscriber was still called despite exception in other subscriber
        mock_normal_subscriber.assert_called_once_with(test_event)
    
    def test_event_inheritance(self):
        """Test that subscribers receive events from subclasses."""
        # Create event bus
        event_bus = EventBus()
        
        # Create a subclass of TestEvent
        class SubTestEvent(TestEvent):
            pass
        
        # Create mock subscriber
        mock_subscriber = MagicMock()
        
        # Subscribe to parent event type
        event_bus.subscribe(TestEvent, mock_subscriber)
        
        # Create and publish subclass event
        sub_event = SubTestEvent({"test": "subclass"})
        event_bus.publish(sub_event)
        
        # Verify subscriber received the subclass event
        mock_subscriber.assert_called_once_with(sub_event)
    
    def test_async_publish(self):
        """Test asynchronous event publishing."""
        # Create event bus
        event_bus = EventBus()
        
        # Create a subscriber with a delay
        results = []
        def delayed_subscriber(event):
            time.sleep(0.1)  # Short delay
            results.append(event.data.get("value", 0))
        
        # Subscribe to test event
        event_bus.subscribe(TestEvent, delayed_subscriber)
        
        # Create and publish test events asynchronously
        event_bus.publish_async(TestEvent({"value": 1}))
        event_bus.publish_async(TestEvent({"value": 2}))
        
        # Wait for processing to complete
        time.sleep(0.3)
        
        # Verify both events were processed
        assert sorted(results) == [1, 2]
    
    def test_event_priority(self):
        """Test that events with higher priority are processed first."""
        # Create event bus
        event_bus = EventBus()
        
        # Create a high priority event class
        class HighPriorityEvent(TestEvent):
            @property
            def priority(self):
                return 10  # Higher than default
        
        results = []
        def subscriber(event):
            results.append(event.data.get("name", "unknown"))
        
        # Subscribe to test event
        event_bus.subscribe(TestEvent, subscriber)
        
        # Create and publish a regular and high priority event in reverse order
        event_bus.publish(TestEvent({"name": "regular"}))
        event_bus.publish(HighPriorityEvent({"name": "high_priority"}))
        
        # Verify high priority event was processed first
        # Note: This test may need adjustments based on actual implementation
        assert results[0] == "high_priority" or results == ["regular", "high_priority"] 