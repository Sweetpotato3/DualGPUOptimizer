"""
Backward compatibility layer for memory monitoring system.

This module provides backward compatibility with the original memory_monitor.py
to ensure existing code continues to work with the refactored implementation.
"""

import logging

from dualgpuopt.memory.alerts import MemoryAlert, MemoryAlertCallback, MemoryAlertLevel
from dualgpuopt.memory.metrics import GPUMemoryStats, MemoryUnit
from dualgpuopt.memory.monitor import MemoryMonitor, get_memory_monitor
from dualgpuopt.memory.predictor import DEFAULT_PROFILES, MemoryProfile, initialize_memory_profiles
from dualgpuopt.memory.recovery import MemoryRecoveryStrategy

logger = logging.getLogger("DualGPUOpt.MemoryMonitor")

# Re-export all public classes and functions from the original module
__all__ = [
    "DEFAULT_PROFILES",
    "GPUMemoryStats",
    "MemoryAlert",
    "MemoryAlertCallback",
    "MemoryAlertLevel",
    "MemoryMonitor",
    "MemoryProfile",
    "MemoryRecoveryStrategy",
    "MemoryUnit",
    "get_memory_monitor",
    "initialize_memory_profiles",
]
