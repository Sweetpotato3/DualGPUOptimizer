"""
Services package for core application services.
"""
from dualgpuopt.services.event_bus import event_bus, Event, GPUEvent, GPUMetricsEvent, ConfigChangedEvent, OptimizationEvent, EventPriority 