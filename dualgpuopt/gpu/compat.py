"""
GPU compatibility module for DualGPUOptimizer
Provides graceful fallbacks when pynvml or other dependencies are missing
"""
from __future__ import annotations

import logging
import platform
from typing import Any

# Configure logger
logger = logging.getLogger("DualGPUOpt.GPU.Compat")

# Track dependency status
DEPENDENCIES = {
    "pynvml": {"available": False, "module": None},
}

# Try to import pynvml
try:
    import pynvml

    pynvml.nvmlInit()
    DEPENDENCIES["pynvml"]["available"] = True
    DEPENDENCIES["pynvml"]["module"] = pynvml
    logger.info("pynvml initialized successfully")
    NVML_INITIALIZED = True
except ImportError:
    logger.warning("pynvml not installed - GPU monitoring will be limited")
    NVML_INITIALIZED = False
except Exception as e:
    logger.warning(f"Failed to initialize pynvml: {e}")
    NVML_INITIALIZED = False

# Platform detection
IS_MAC = platform.system() == "Darwin"
IS_NVIDIA = not IS_MAC and DEPENDENCIES["pynvml"]["available"]

# Expose if mock mode is active - default to True if pynvml is not available
MOCK_MODE = not NVML_INITIALIZED


# GPU mock data generation for fallback
def generate_mock_gpus(count: int = 2) -> list[dict[str, Any]]:
    """
    Generate mock GPU data for testing or when real data is unavailable

    Args:
    ----
        count: Number of mock GPUs to generate

    Returns:
    -------
        List of dictionaries with mock GPU data
    """
    mock_gpus = []

    # Create the specified number of mock GPUs
    for i in range(count):
        # Alternate between high and low memory GPUs for testing multi-GPU scenarios
        if i % 2 == 0:
            mem_total = 24576  # 24GB
            name = "GeForce RTX 4090"
            util = 35
            mem_used = 8192
            clock_sm = 1950
            clock_memory = 9500
        else:
            mem_total = 12288  # 12GB
            name = "GeForce RTX 3070"
            util = 85
            mem_used = 10240
            clock_sm = 1725
            clock_memory = 7000

        # Create the mock GPU entry
        gpu = {
            "id": i,
            "name": name,
            "type": "NVIDIA",
            "mem_total": mem_total,
            "mem_used": mem_used,
            "util": util,
            "temperature": 65.0 + (i * 5),
            "power_usage": 180.0 - (i * 20),
            "clock_sm": clock_sm,
            "clock_memory": clock_memory,
            "pcie_tx": 12.5,
            "pcie_rx": 8.2,
        }

        mock_gpus.append(gpu)

    return mock_gpus


# GPU Metric class for type hints
class GpuMetric:
    """Common metrics for GPU monitoring"""

    UTILIZATION = "util"
    MEMORY_TOTAL = "mem_total"
    MEMORY_USED = "mem_used"
    TEMPERATURE = "temperature"
    POWER_USAGE = "power_usage"
    CLOCK_SM = "clock_sm"
    CLOCK_MEMORY = "clock_memory"
    PCIE_TX = "pcie_tx"
    PCIE_RX = "pcie_rx"

    @classmethod
    def get_all_metrics(cls) -> list[str]:
        """
        Get list of all available metrics

        Returns
        -------
            List of metric names
        """
        return [
            cls.UTILIZATION,
            cls.MEMORY_TOTAL,
            cls.MEMORY_USED,
            cls.TEMPERATURE,
            cls.POWER_USAGE,
            cls.CLOCK_SM,
            cls.CLOCK_MEMORY,
            cls.PCIE_TX,
            cls.PCIE_RX,
        ]


# Function to get whether mock mode is active
def is_mock_mode() -> bool:
    """
    Get the current state of mock mode

    Returns
    -------
        True if mock mode is active
    """
    return MOCK_MODE


# Function to set mock mode
def set_mock_mode(enabled: bool = True) -> None:
    """
    Enable or disable mock mode

    Args:
    ----
        enabled: Whether to enable mock mode
    """
    global MOCK_MODE
    MOCK_MODE = enabled
    logger.info(f"Mock GPU mode {'enabled' if enabled else 'disabled'}")


# Re-initialize NVML (useful after changing mock mode)
def reinit_nvml() -> bool:
    """
    Reinitialize NVML

    Returns
    -------
        True if initialization was successful
    """
    global NVML_INITIALIZED

    # Skip if in mock mode or pynvml is not available
    if MOCK_MODE or not DEPENDENCIES["pynvml"]["available"]:
        return False

    try:
        # Shutdown if already initialized
        if NVML_INITIALIZED:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass

        # Initialize NVML
        pynvml.nvmlInit()
        NVML_INITIALIZED = True
        logger.info("NVML reinitialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to reinitialize NVML: {e}")
        NVML_INITIALIZED = False
        return False
