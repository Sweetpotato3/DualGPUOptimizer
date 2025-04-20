"""
GPU memory monitoring and OOM prevention system for DualGPUOptimizer.

This module provides real-time GPU memory monitoring, OOM prevention strategies,
and memory allocation optimization for dual-GPU setups.
"""

# Import public API components
from dualgpuopt.memory.monitor import MemoryMonitor, get_memory_monitor
from dualgpuopt.memory.alerts import MemoryAlert, MemoryAlertLevel
from dualgpuopt.memory.metrics import GPUMemoryStats, MemoryUnit
from dualgpuopt.memory.predictor import MemoryProfile
from dualgpuopt.memory.recovery import MemoryRecoveryStrategy

# Re-export default profiles
from dualgpuopt.memory.predictor import DEFAULT_PROFILES, initialize_memory_profiles

# For backward compatibility
from dualgpuopt.memory.compat import *

# Module version
__version__ = "1.0.0"