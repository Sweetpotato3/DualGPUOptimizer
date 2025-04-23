# Services Package

The services package contains core application services that provide centralized functionality across components.

## Enhanced Event Bus System

The event bus system provides a powerful way for components to communicate without direct coupling. It acts as a central message broker that components can publish to and subscribe from.

### Key Features

- **Typed Events**: Define structured event data using Python dataclasses
- **Priority-based Dispatch**: Control the order of event handler execution
- **Asynchronous Handlers**: Support for async event handlers
- **Inheritance-based Handlers**: Subscribe to base event types to receive all derived events
- **Fire-and-forget Async Dispatch**: Non-blocking event publishing
- **Security Controls**: Lock event types to prevent further subscriptions

### Available Events

- `Event`: Base class for all events
- `GPUEvent`: Base class for GPU-related events
- `GPUMetricsEvent`: Event containing GPU metrics (utilization, memory, temperature, etc.)
- `ConfigChangedEvent`: Event for configuration changes
- `OptimizationEvent`: Event for optimization-related notifications

### Usage Examples

#### Publishing Events

```python
# Import the event bus and events
from dualgpuopt.services import event_bus, GPUMetricsEvent

# Create and publish a typed event
event = GPUMetricsEvent(
    gpu_index=0,
    utilization=75.5,
    memory_used=4096,
    memory_total=8192,
    temperature=65.0,
    power_draw=180.5,
    fan_speed=70
)
event_bus.publish_typed(event)

# Alternative simple publishing (will create the event internally)
event_bus.publish(GPUMetricsEvent, {
    "gpu_index": 0,
    "utilization": 75.5,
    "memory_used": 4096,
    "memory_total": 8192,
    "temperature": 65.0,
    "power_draw": 180.5,
    "fan_speed": 70
})
```

#### Subscribing to Events

```python
# Import the event bus and events
from dualgpuopt.services import event_bus, GPUMetricsEvent, EventPriority

# Define a handler function
def handle_gpu_metrics(event: GPUMetricsEvent) -> None:
    print(f"GPU {event.gpu_index} utilization: {event.utilization}%")

# Subscribe with normal priority (synchronous)
event_bus.subscribe_typed(GPUMetricsEvent, handle_gpu_metrics)

# Subscribe with high priority
event_bus.subscribe_typed(
    GPUMetricsEvent,
    handle_gpu_metrics,
    priority=EventPriority.HIGH
)

# Subscribe with an async handler
async def async_handler(event: GPUMetricsEvent) -> None:
    await some_async_operation(event)

event_bus.subscribe_typed(
    GPUMetricsEvent,
    async_handler,
    is_async=True
)
```

#### Unsubscribing

```python
# Unsubscribe when no longer needed
event_bus.unsubscribe(GPUMetricsEvent, handle_gpu_metrics)
```

### Backward Compatibility

The event bus maintains backward compatibility with string-based event types:

```python
# Legacy string-based event subscription
event_bus.subscribe("gpu_metrics", handle_data)

# Legacy string-based event publishing
event_bus.publish("gpu_metrics", {"gpu": 0, "load": 75})
```

## Creating Custom Events

To create custom events, subclass the `Event` base class:

```python
from dataclasses import dataclass, field
from dualgpuopt.services import Event

@dataclass
class MyCustomEvent(Event):
    """Custom event for my specific use case."""
    data_value: int = 0
    message: str = ""
    timestamp: float = field(default_factory=time.time)
```

## Middleware System

The services package works with a middleware system that allows service modules to be extended with additional functionality. See the telemetry module for an example of middleware implementation.
