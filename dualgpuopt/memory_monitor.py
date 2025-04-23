"""
GPU memory monitoring and OOM prevention system for DualGPUOptimizer.

This module provides real-time GPU memory monitoring, OOM prevention strategies,
and memory allocation optimization for dual-GPU setups.

Note: This file is a compatibility layer for the refactored memory monitoring system.
      New code should import directly from dualgpuopt.memory.
"""

import logging
import warnings

# Configure logger
logger = logging.getLogger("DualGPUOpt.MemoryMonitor")

# Show deprecation warning for direct imports
warnings.warn(
    "Importing directly from memory_monitor.py is deprecated. "
    "Please import from dualgpuopt.memory instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export all components from the memory module
from dualgpuopt.memory import (
    DEFAULT_PROFILES,
    GPUMemoryStats,
    MemoryAlert,
    MemoryAlertCallback,
    MemoryAlertLevel,
    MemoryMonitor,
    MemoryProfile,
    MemoryRecoveryStrategy,
    MemoryUnit,
    get_memory_monitor,
    initialize_memory_profiles,
)

# Maintain backward compatibility
__all__ = [
    "MemoryUnit",
    "MemoryAlertLevel",
    "GPUMemoryStats",
    "MemoryAlert",
    "MemoryAlertCallback",
    "MemoryProfile",
    "MemoryRecoveryStrategy",
    "MemoryMonitor",
    "get_memory_monitor",
    "DEFAULT_PROFILES",
    "initialize_memory_profiles",
]
