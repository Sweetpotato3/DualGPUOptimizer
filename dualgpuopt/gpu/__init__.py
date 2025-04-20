"""
GPU Module for DualGPUOptimizer

Provides GPU information and monitoring functionality.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional

# Import public functions from submodules
from dualgpuopt.gpu.info import query, get_gpu_count, get_gpu_names
from dualgpuopt.gpu.mock import set_mock_mode, get_mock_mode, generate_mock_gpus
from dualgpuopt.gpu.monitor import get_memory_info, get_utilization, get_temperature, get_power_usage

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