#!/usr/bin/env python3
"""
Event types for the DualGPUOptimizer.

This module re-exports events from the event_bus module for easier import.
It also provides enhanced event types for testing and integration.
"""
from __future__ import annotations
import dataclasses
from typing import Dict, List, Any

# Re-export event base class and event types from event_bus
from dualgpuopt.services.event_bus import (
    Event,
    EventPriority,
    GPUEvent,
    ModelSelectedEvent,
    SplitCalculatedEvent,
    ConfigChangedEvent,
)

# Re-export original GPUMetricsEvent with a different name
from dualgpuopt.services.event_bus import GPUMetricsEvent as BaseGPUMetricsEvent

# Define an enhanced GPUMetricsEvent with metrics dictionary for testing
@dataclasses.dataclass
class GPUMetricsEvent(GPUEvent):
    """Enhanced event fired when GPU metrics are updated with a metrics dictionary."""
    metrics: Dict[str, List[Any]] = dataclasses.field(default_factory=dict)


# Export all for easier imports
__all__ = [
    "Event",
    "EventPriority",
    "GPUEvent",
    "GPUMetricsEvent",
    "BaseGPUMetricsEvent",
    "ModelSelectedEvent",
    "SplitCalculatedEvent",
    "ConfigChangedEvent",
] 