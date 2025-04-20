"""
Common GPU module functionality
"""
from __future__ import annotations
import platform
import logging
from typing import Dict, Any, List, Optional

# Configure logger
logger = logging.getLogger("DualGPUOpt.GPU")

# Platform detection
IS_MAC = platform.system() == "Darwin"
IS_NVIDIA = not IS_MAC

# Global flag for mock mode
MOCK_MODE = False

# NVML initialization
try:
    if IS_NVIDIA:
        import pynvml
        pynvml.nvmlInit()
        NVML_INITIALIZED = True
except (ImportError, Exception) as e:
    logger.warning(f"Failed to initialize NVML: {e}")
    MOCK_MODE = True
    NVML_INITIALIZED = False

# GPU metrics
class GpuMetrics:
    """Constants for GPU metrics"""
    UTILIZATION = "util"
    MEMORY_TOTAL = "mem_total"
    MEMORY_USED = "mem_used"
    TEMPERATURE = "temperature"
    POWER_USAGE = "power_usage"
    CLOCK_SM = "clock_sm"
    CLOCK_MEMORY = "clock_memory"
    
# Helper functions for type conversion
def ensure_float(value: Any) -> float:
    """Ensure a value is a float, converting if necessary"""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert {value} to float, using 0.0")
        return 0.0
        
def ensure_int(value: Any) -> int:
    """Ensure a value is an int, converting if necessary"""
    if value is None:
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert {value} to int, using 0")
        return 0 