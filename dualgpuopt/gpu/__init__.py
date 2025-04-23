"""
GPU Module for DualGPUOptimizer

Provides GPU information and monitoring functionality.
"""
from __future__ import annotations

# Import public functions from submodules
from dualgpuopt.gpu.info import get_gpu_count, get_gpu_names, query
from dualgpuopt.gpu.mock import generate_mock_gpus, get_mock_mode, set_mock_mode
from dualgpuopt.gpu.monitor import (
    get_memory_info,
    get_power_usage,
    get_temperature,
    get_utilization,
)

# Public API
__all__ = [
    "query",
    "get_gpu_count",
    "get_gpu_names",
    "set_mock_mode",
    "get_mock_mode",
    "generate_mock_gpus",
    "get_memory_info",
    "get_utilization",
    "get_temperature",
    "get_power_usage",
]
