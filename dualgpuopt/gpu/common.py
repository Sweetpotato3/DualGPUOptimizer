"""
Common GPU module functionality
"""
from __future__ import annotations
import platform
import logging
import sys
from typing import Dict, Any, List, Optional

# Configure logger
logger = logging.getLogger("DualGPUOpt.GPU")

# Create a local GpuMetrics class to avoid circular imports with telemetry
class GpuMetrics:
    """Local GpuMetrics class that matches the structure in telemetry.py"""
    def __init__(self,
                 gpu_id: int,
                 name: str,
                 utilization: int,
                 memory_used: int,
                 memory_total: int,
                 temperature: int,
                 power_usage: float,
                 power_limit: float,
                 fan_speed: int,
                 clock_sm: int,
                 clock_memory: int,
                 pcie_tx: int,
                 pcie_rx: int,
                 timestamp: float,
                 error_state: bool = False):
        self.gpu_id = gpu_id
        self.name = name
        self.utilization = utilization
        self.memory_used = memory_used
        self.memory_total = memory_total
        self.temperature = temperature
        self.power_usage = power_usage
        self.power_limit = power_limit
        self.fan_speed = fan_speed
        self.clock_sm = clock_sm
        self.clock_memory = clock_memory
        self.pcie_tx = pcie_tx
        self.pcie_rx = pcie_rx
        self.timestamp = timestamp
        self.error_state = error_state

    @property
    def memory_percent(self) -> float:
        """Return memory usage as percentage"""
        if self.memory_total == 0:
            return 0.0
        return (self.memory_used / self.memory_total) * 100.0

    @property
    def power_percent(self) -> float:
        """Return power usage as percentage of limit"""
        if self.power_limit == 0:
            return 0.0
        return (self.power_usage / self.power_limit) * 100.0

    @property
    def formatted_memory(self) -> str:
        """Return formatted memory usage string"""
        return f"{self.memory_used}/{self.memory_total} MB ({self.memory_percent:.1f}%)"

    @property
    def formatted_pcie(self) -> str:
        """Return formatted PCIe bandwidth usage"""
        return f"TX: {self.pcie_tx/1024:.1f} MB/s, RX: {self.pcie_rx/1024:.1f} MB/s"

# Try to import our compatibility layer
try:
    from .compat import (
        IS_MAC, IS_NVIDIA, MOCK_MODE, NVML_INITIALIZED,
        DEPENDENCIES, GpuMetric, set_mock_mode, is_mock_mode,
        generate_mock_gpus, reinit_nvml
    )
    logger.info("Imported GPU compatibility layer")

    # Get pynvml module if available
    pynvml = DEPENDENCIES["pynvml"]["module"] if DEPENDENCIES["pynvml"]["available"] else None

except ImportError as e:
    logger.error(f"Failed to import GPU compatibility layer: {e}")
    # Fall back to local implementations

    # Platform detection
    IS_MAC = platform.system() == "Darwin"
    IS_NVIDIA = not IS_MAC

    # Global flag for mock mode
    MOCK_MODE = False
    NVML_INITIALIZED = False

    # Try to initialize NVML
    try:
        if IS_NVIDIA:
            import pynvml
            pynvml.nvmlInit()
            NVML_INITIALIZED = True
            logger.info("NVML initialized directly")
    except (ImportError, Exception) as e:
        logger.warning(f"Failed to initialize NVML: {e}")
        MOCK_MODE = True
        NVML_INITIALIZED = False
        pynvml = None

    # GPU metrics
    class GpuMetric:
        """Constants for GPU metrics"""
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
        def get_all_metrics(cls) -> List[str]:
            """Get list of all available metrics"""
            return [cls.UTILIZATION, cls.MEMORY_TOTAL, cls.MEMORY_USED,
                    cls.TEMPERATURE, cls.POWER_USAGE, cls.CLOCK_SM,
                    cls.CLOCK_MEMORY, cls.PCIE_TX, cls.PCIE_RX]

    def set_mock_mode(enabled: bool = True) -> None:
        """Enable or disable mock mode"""
        global MOCK_MODE
        MOCK_MODE = enabled
        logger.info(f"Mock GPU mode {'enabled' if enabled else 'disabled'}")

    def is_mock_mode() -> bool:
        """Get the current state of mock mode"""
        return MOCK_MODE

    def generate_mock_gpus(count: int = 2) -> List[Dict[str, Any]]:
        """Generate mock GPU data"""
        mock_gpus = []

        for i in range(count):
            if i % 2 == 0:
                mem_total = 24576  # 24GB
                name = "GeForce RTX 4090 (Mock)"
                util = 35
                mem_used = 8192
            else:
                mem_total = 12288  # 12GB
                name = "GeForce RTX 3070 (Mock)"
                util = 85
                mem_used = 10240

            gpu = {
                "id": i,
                "name": name,
                "type": "NVIDIA",
                "mem_total": mem_total,
                "mem_used": mem_used,
                "util": util,
                "temperature": 65.0 + (i * 5),
                "power_usage": 180.0 - (i * 20),
                "clock_sm": 1725 + (i * 100),
                "clock_memory": 9000 - (i * 500),
                "pcie_tx": 12.5,
                "pcie_rx": 8.2,
            }

            mock_gpus.append(gpu)

        return mock_gpus

    def reinit_nvml() -> bool:
        """Reinitialize NVML"""
        global NVML_INITIALIZED

        if MOCK_MODE or pynvml is None:
            return False

        try:
            if NVML_INITIALIZED:
                try:
                    pynvml.nvmlShutdown()
                except Exception:
                    pass

            pynvml.nvmlInit()
            NVML_INITIALIZED = True
            logger.info("NVML reinitialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to reinitialize NVML: {e}")
            NVML_INITIALIZED = False
            return False

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

# Utility function to format memory sizes
def format_memory(bytes_or_mb: int, use_mb: bool = True) -> str:
    """Format memory size in human-readable form

    Args:
        bytes_or_mb: Memory size in bytes or MB
        use_mb: Whether the input is in MB (True) or bytes (False)

    Returns:
        Formatted memory string
    """
    if use_mb:
        # Input is already in MB
        mb = bytes_or_mb
    else:
        # Convert bytes to MB
        mb = bytes_or_mb / (1024 * 1024)

    if mb < 1024:
        return f"{mb:.0f} MB"
    else:
        gb = mb / 1024
        return f"{gb:.1f} GB"