"""
GPU memory monitoring and OOM prevention system for DualGPUOptimizer.

This module provides real-time GPU memory monitoring, OOM prevention strategies,
and memory allocation optimization for dual-GPU setups.
"""

from dualgpuopt.memory.alerts import MemoryAlert, MemoryAlertLevel

# For backward compatibility
from dualgpuopt.memory.compat import *
from dualgpuopt.memory.metrics import GPUMemoryStats, MemoryUnit

# Import public API components
from dualgpuopt.memory.monitor import MemoryMonitor, get_memory_monitor

# Re-export default profiles
from dualgpuopt.memory.predictor import (
    DEFAULT_PROFILES,
    MemoryProfile,
    initialize_memory_profiles,
)
from dualgpuopt.memory.profiler import (
    MemoryEventType,
    MemoryProfiler,
    get_memory_profiler,
)
from dualgpuopt.memory.recovery import MemoryRecoveryStrategy

# Module version
__version__ = "1.1.0"
