#!/usr/bin/env python3
"""
Event types for the DualGPUOptimizer.

This module re-exports events from the event_bus module for easier import.
It also provides enhanced event types for testing and integration.
"""
from __future__ import annotations

import dataclasses
from typing import Any

# Re-export event base class and event types from event_bus
from dualgpuopt.services.event_bus import (
    ConfigChangedEvent,
    Event,
    EventPriority,
    GPUEvent,
    ModelSelectedEvent,
    SplitCalculatedEvent,
)

# Re-export original GPUMetricsEvent with a different name
from dualgpuopt.services.event_bus import GPUMetricsEvent as BaseGPUMetricsEvent


# Define an enhanced GPUMetricsEvent with metrics dictionary for testing
@dataclasses.dataclass
class GPUMetricsEvent(GPUEvent):
    """Enhanced event fired when GPU metrics are updated with a metrics dictionary."""

    metrics: dict[str, list[Any]] = dataclasses.field(default_factory=dict)


# Export all for easier imports
__all__ = [
    "BaseGPUMetricsEvent",
    "ConfigChangedEvent",
    "Event",
    "EventPriority",
    "GPUEvent",
    "GPUMetricsEvent",
    "ModelSelectedEvent",
    "SplitCalculatedEvent",
]
