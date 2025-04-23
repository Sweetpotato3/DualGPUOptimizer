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
    "generate_mock_gpus",
    "get_gpu_count",
    "get_gpu_names",
    "get_memory_info",
    "get_mock_mode",
    "get_power_usage",
    "get_temperature",
    "get_utilization",
    "query",
    "set_mock_mode",
]
