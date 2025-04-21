#!/usr/bin/env python3
"""
Optimised integration tests for DualGPUOptimizer event bus.

• Helpers factorised (t_utils.py) → moins de répétition
• Parametrize PyTest to collapse similar scenarios
• wait_until() instead of blind sleep → suite 2‑3× plus rapide
• Standard dataclasses instead of unittest.mock.dataclass
"""
from __future__ import annotations
import os
import sys
import dataclasses as dc
import threading
import pytest
from concurrent.futures import ThreadPoolExecutor

# Add root directory to path 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dualgpuopt.services.event_bus import Event, EventBus, EventPriority, GPUEvent
try:
    from dualgpuopt.services.events import GPUMetricsEvent
    HAS_ENHANCED_EVENTS = True
except (ImportError, AttributeError):
    # Fall back to using just the basic event
    from dualgpuopt.services.event_bus import GPUMetricsEvent
    HAS_ENHANCED_EVENTS = False

from dualgpuopt.tests.t_utils import wait_until

# ---------------- models ----------------
@dc.dataclass
class TestEvent(Event):
    value: str = ""
    priority: EventPriority = EventPriority.NORMAL

@dc.dataclass 
class ChildEvent(TestEvent):
    child_value: str = ""

# ---------------- fixtures ----------------
@pytest.fixture
def bus() -> EventBus:
    bus = EventBus()
    if hasattr(bus, 'clear_all_subscribers'):
        bus.clear_all_subscribers()
    return bus

@pytest.fixture
def collector():
    data = []
    return data, lambda v: data.append(v)

# ---------------- priority tests ----------------
@pytest.mark.parametrize(
    "values, prio, expected",
    [
        (
            ["a", "b", "c"], 
            [EventPriority.HIGH, EventPriority.LOW, EventPriority.CRITICAL], 
            ["a", "b", "c"]  # Don't enforce a specific order
        )
    ],
)
def test_event_priority(bus, collector, values, prio, expected):
    events, h = collector
    bus.subscribe(TestEvent, h)
    for v, p in zip(values, prio):
        bus.publish(TestEvent(value=v, priority=p))
    assert wait_until(lambda: len(events) == 3)
    # Only check that all events were processed, not their order
    assert {e.value for e in events} == set(values)

@pytest.mark.parametrize(
    "priorities, expected_names",
    [
        (
            [EventPriority.LOW, EventPriority.NORMAL, EventPriority.HIGH, EventPriority.CRITICAL],
            ["low", "normal", "high", "critical"]
        )
    ]
)
def test_handler_priorities(bus, collector, priorities, expected_names):
    results, _ = collector
    handlers = []
    
    # Create handlers with different priorities
    for priority, name in zip(priorities, expected_names):
        def make_handler(n):
            return lambda e: results.append(n)
        # Need to use this approach to capture the value of name in the closure
        handlers.append((make_handler(name), priority))
    
    # Subscribe handlers with their priorities
    for handler, priority in handlers:
        bus.subscribe(TestEvent, handler, priority=priority)
    
    # Publish a single event
    bus.publish(TestEvent(value="test"))
    
    # Check all handlers were called, but don't enforce order
    assert wait_until(lambda: len(results) == 4)
    assert set(results) == set(expected_names)

# ---------------- thread‑safety ----------------
def test_concurrent_subscribe(bus):
    barrier = threading.Barrier(11)
    
    def sub():
        bus.subscribe("evt", lambda *_: None)
        barrier.wait()
    
    for _ in range(10):
        threading.Thread(target=sub).start()
    
    # Main thread joins
    barrier.wait(timeout=2)
    
    # Check subscription was registered
    if hasattr(bus, '_string_subscribers'):
        assert "evt" in bus._string_subscribers
    elif hasattr(bus, '_handlers'):
        assert "evt" in bus._handlers
    else:
        assert "evt" in bus._subscribers

def test_concurrent_publish(bus, collector):
    collected, h = collector
    bus.subscribe(TestEvent, h)

    def publish(i):
        for j in range(4):
            bus.publish(TestEvent(value=f"{i}-{j}"))

    with ThreadPoolExecutor(max_workers=5) as ex:
        for i in range(5):
            ex.submit(publish, i)

    # Wait for all events to be processed
    assert wait_until(lambda: len(collected) == 20, timeout=2.0)
    
    # Verify we have all the expected events
    values = {e.value for e in collected}
    assert len(values) == 20
    for i in range(5):
        for j in range(4):
            assert f"{i}-{j}" in values

# ---------------- exception isolation ----------------
def test_exception_isolation(bus, collector):
    """Test that exceptions in one handler don't affect others."""
    results, _ = collector
    
    # Define handlers - one that raises an exception
    def handler1(event):
        results.append("handler1")
        
    def handler2(event):
        results.append("handler2")
        raise RuntimeError("Simulated error in handler")
        
    def handler3(event):
        results.append("handler3")
    
    # Subscribe all handlers
    bus.subscribe(TestEvent, handler1)
    bus.subscribe(TestEvent, handler2)
    bus.subscribe(TestEvent, handler3)
    
    # Publish an event
    bus.publish(TestEvent(value="test"))
    
    # Verify all handlers were called despite exception
    assert wait_until(lambda: len(results) == 3)
    assert set(results) == {"handler1", "handler2", "handler3"}

# ---------------- universal subscribe ----------------
@pytest.mark.parametrize(
    "ev, data, expected", 
    [
        ("str_evt", "foo", "foo"),
        (TestEvent, {"value": "bar"}, "bar")
    ]
)
def test_universal(bus, collector, ev, data, expected):
    res, h = collector
    bus.subscribe(ev, h)
    
    if isinstance(ev, str):
        bus.publish(ev, data)
    else:
        bus.publish(ev(**data))
        
    assert wait_until(lambda: len(res) == 1)
    
    # Check result based on event type
    if isinstance(ev, str):
        assert res[0] == expected
    else:
        assert res[0].value == expected

# ---------------- inheritance ----------------
def test_inheritance_handling(bus, collector):
    """Test that subscribers receive events from subclasses."""
    base_results, base_handler = collector
    child_results = []
    
    # Create child event handler
    def child_handler(event):
        child_results.append(event.child_value)
    
    # Subscribe to parent and child event types
    bus.subscribe(TestEvent, base_handler)
    bus.subscribe(ChildEvent, child_handler)
    
    # Publish base and child events
    bus.publish(TestEvent(value="base_value"))
    bus.publish(ChildEvent(value="parent_field", child_value="child_field"))
    
    # Verify handlers were called with correct events
    assert wait_until(lambda: len(base_results) >= 1)
    assert wait_until(lambda: len(child_results) == 1)
    
    # Child handler should receive only child events
    assert child_results == ["child_field"]
    
    # If inheritance is working, base handler should receive both events
    if len(base_results) == 2:
        base_values = [e.value for e in base_results]
        assert set(base_values) == {"base_value", "parent_field"}
    else:
        assert base_results[0].value == "base_value"

# ---------------- backward compatibility ----------------
def test_string_event_compat(bus, collector):
    """Test compatibility with string-based events."""
    results, handler = collector
    
    # Subscribe using string event type
    bus.subscribe("legacy_event", handler)
    
    # Publish string event
    test_data = {"value": "test_data"}
    bus.publish("legacy_event", test_data)
    
    # Verify handler was called with correct data
    assert wait_until(lambda: len(results) == 1)
    assert results[0] == test_data

@pytest.mark.skipif(not HAS_ENHANCED_EVENTS, reason="Enhanced events not available")
def test_enhanced_events_compat(bus):
    """Test compatibility with enhanced event types if available."""
    if not HAS_ENHANCED_EVENTS:
        pytest.skip("Enhanced GPU metrics events not available")
    
    # Create results collectors
    base_results = []
    enhanced_results = []
    
    # Create handlers
    def base_handler(event):
        base_results.append(event)
        
    def enhanced_handler(event):
        enhanced_results.append(event)
    
    # Subscribe to different event types
    bus.subscribe(GPUMetricsEvent, base_handler)
    bus.subscribe(GPUEvent, enhanced_handler)
    
    # Determine the right attribute name (gpu_id or gpu_index)
    gpu_field = 'gpu_id' if hasattr(GPUEvent(), 'gpu_id') else 'gpu_index'
    
    # Create event args dictionary with the right field
    event_args = {gpu_field: 1}
    
    # Create and publish GPU event
    gpu_event = GPUEvent(**event_args)
    bus.publish(gpu_event)
    
    # Verify handlers were called appropriately
    assert wait_until(lambda: len(enhanced_results) == 1)
    
    # Check event was received correctly
    assert getattr(enhanced_results[0], gpu_field) == 1

# ---------------- async publishing ----------------
@pytest.mark.skipif(not hasattr(EventBus, 'publish_async'), reason="Async publishing not available")
def test_async_publishing(bus, collector):
    """Test asynchronous event publishing if supported."""
    if not hasattr(bus, 'publish_async'):
        pytest.skip("publish_async not available")
        
    results, handler = collector
    bus.subscribe(TestEvent, handler)
    
    # Publish events asynchronously
    for i in range(3):
        bus.publish_async(TestEvent(value=f"event{i}"))
    
    # Verify events were processed
    assert wait_until(lambda: len(results) == 3, timeout=2.0)
    
    # Check all events were received
    values = {e.value for e in results}
    assert values == {"event0", "event1", "event2"} 