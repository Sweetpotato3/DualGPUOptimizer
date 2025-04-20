"""
Backward compatibility layer for memory monitoring system.

This module provides backward compatibility with the original memory_monitor.py
to ensure existing code continues to work with the refactored implementation.
"""

import logging
from typing import Dict, Optional, Union

from dualgpuopt.memory.alerts import MemoryAlert, MemoryAlertCallback, MemoryAlertLevel
from dualgpuopt.memory.metrics import GPUMemoryStats, MemoryUnit
from dualgpuopt.memory.monitor import MemoryMonitor, get_memory_monitor
from dualgpuopt.memory.predictor import MemoryProfile, DEFAULT_PROFILES, initialize_memory_profiles
from dualgpuopt.memory.recovery import MemoryRecoveryStrategy, RecoveryManager

logger = logging.getLogger("DualGPUOpt.MemoryMonitor")

# Re-export all public classes and functions from the original module
__all__ = [
    'MemoryUnit',
    'MemoryAlertLevel',
    'GPUMemoryStats',
    'MemoryAlert',
    'MemoryAlertCallback',
    'MemoryProfile',
    'MemoryRecoveryStrategy',
    'MemoryMonitor',
    'get_memory_monitor',
    'DEFAULT_PROFILES',
    'initialize_memory_profiles'
]