"""
GPU discovery via NVML – no GUI, no optimisation math.
"""
from __future__ import annotations

import concurrent.futures as _fut
import dataclasses as _dc
import logging
import os
import threading
from typing import List, Optional, Dict, Any

try:
    import pynvml  # external, tiny
except ImportError as _exc:
    raise RuntimeError(
        "pynvml missing – pip install nvidia‑ml‑py3 inside your 3.13 environment"
    ) from _exc

# Configure logging
logger = logging.getLogger("dualgpuopt.gpu")


@_dc.dataclass(slots=True, frozen=True)
class GPU:
    """Enhanced GPU information container with comprehensive metrics."""
    index: int
    name: str
    mem_total: int  # MiB
    mem_free: int   # MiB

    # Additional hardware info
    architecture: str = ""  # GPU architecture (e.g., "Ampere", "Ada Lovelace")
    cuda_cores: int = 0     # Number of CUDA cores
    compute_capability: str = ""  # CUDA compute capability
    driver_version: str = ""  # NVIDIA driver version

    # Performance metrics
    temperature: int = 0     # Temperature in Celsius
    fan_speed: int = 0       # Fan speed percentage
    power_usage: float = 0.0  # Current power draw in Watts
    power_limit: float = 0.0  # Maximum power limit in Watts
    gpu_utilization: int = 0  # GPU utilization percentage
    memory_utilization: int = 0  # Memory utilization percentage

    # Clock speeds
    graphics_clock: int = 0  # Graphics clock in MHz
    memory_clock: int = 0    # Memory clock in MHz
    sm_clock: int = 0        # SM clock in MHz

    # PCIe info
    pcie_gen: str = ""      # PCIe generation
    pcie_width: int = 0     # PCIe link width

    @property
    def mem_used(self) -> int:
        """Return used memory in MiB."""
        return self.mem_total - self.mem_free

    @property
    def mem_used_percent(self) -> float:
        """Return memory usage as a percentage."""
        return (self.mem_used / self.mem_total) * 100 if self.mem_total > 0 else 0

    @property
    def mem_total_gb(self) -> float:
        """Return total memory in GB (to 1 decimal place)."""
        return round(self.mem_total / 1024, 1)

    @property
    def mem_free_gb(self) -> float:
        """Return free memory in GB (to 1 decimal place)."""
        return round(self.mem_free / 1024, 1)

    @property
    def mem_used_gb(self) -> float:
        """Return used memory in GB (to 1 decimal place)."""
        return round(self.mem_used / 1024, 1)

    @property
    def power_usage_percent(self) -> float:
        """Return power usage as a percentage of the limit."""
        return (self.power_usage / self.power_limit) * 100 if self.power_limit > 0 else 0

    @property
    def short_name(self) -> str:
        """Return a shortened version of the GPU name."""
        # Strip "NVIDIA GeForce " or similar prefixes for a cleaner display
        name = self.name
        for prefix in ["NVIDIA GeForce ", "NVIDIA ", "GeForce "]:
            if name.startswith(prefix):
                name = name[len(prefix):]
        return name


class GpuInfo:
    """GPU information service that provides access to GPU data and events."""

    def __init__(self, mock_mode: bool = False, update_interval: float = 5.0):
        """
        Initialize the GPU information service.

        Args:
            mock_mode: Whether to use mock GPU data instead of real hardware
            update_interval: How often to update GPU data in seconds
        """
        self.logger = logging.getLogger("dualgpuopt.gpu_info")
        self.mock_mode = mock_mode
        self.update_interval = update_interval
        self._gpus: List[GPU] = []
        self._lock = threading.RLock()

        # Enable mock mode if environment variable is set
        if os.environ.get("DGPUOPT_MOCK_GPUS") == "1":
            self.mock_mode = True
            self.logger.info("Mock GPU mode enabled by environment variable")

        # Force mock mode if explicitly requested
        if mock_mode:
            self.logger.info("Mock GPU mode enabled by parameter")
            os.environ["DGPUOPT_MOCK_GPUS"] = "1"

        # Initial GPU probe
        self.refresh()

        # Start background update thread
        self._stop_event = threading.Event()
        self._update_thread = threading.Thread(
            target=self._update_loop,
            daemon=True,
            name="GpuInfoUpdateThread"
        )
        self._update_thread.start()

    def __del__(self):
        """Clean up resources when the object is deleted."""
        self.shutdown()

    def shutdown(self):
        """Stop the background update thread."""
        if hasattr(self, '_stop_event'):
            self._stop_event.set()
            if hasattr(self, '_update_thread') and self._update_thread.is_alive():
                self._update_thread.join(timeout=1.0)

    def _update_loop(self):
        """Background loop to update GPU information periodically."""
        while not self._stop_event.is_set():
            try:
                self.refresh()
            except Exception as e:
                self.logger.error(f"Error updating GPU information: {e}")

            # Wait for the specified interval or until stopped
            self._stop_event.wait(self.update_interval)

    def refresh(self):
        """Refresh GPU information."""
        try:
            with self._lock:
                self._gpus = probe_gpus()
            self.logger.debug(f"Refreshed information for {len(self._gpus)} GPUs")
        except Exception as e:
            self.logger.error(f"Failed to refresh GPU information: {e}")
            if self.mock_mode or os.environ.get("DGPUOPT_MOCK_GPUS") == "1":
                # Use mock data as fallback
                with self._lock:
                    self._gpus = _mock_gpus()
                self.logger.info("Using mock GPU data as fallback")
            else:
                # Re-raise if not in mock mode
                raise

    def get_gpus(self) -> List[GPU]:
        """
        Get the list of available GPUs.

        Returns:
            List of GPU objects
        """
        with self._lock:
            return self._gpus.copy()

    def get_gpu(self, index: int) -> Optional[GPU]:
        """
        Get information for a specific GPU by index.

        Args:
            index: GPU index

        Returns:
            GPU object if found, None otherwise
        """
        with self._lock:
            for gpu in self._gpus:
                if gpu.index == index:
                    return gpu
        return None

    def get_gpu_count(self) -> int:
        """
        Get the number of available GPUs.

        Returns:
            Number of GPUs
        """
        with self._lock:
            return len(self._gpus)

    def has_multiple_gpus(self) -> bool:
        """
        Check if multiple GPUs are available.

        Returns:
            True if multiple GPUs are available, False otherwise
        """
        return self.get_gpu_count() >= 2

    def get_total_memory(self) -> int:
        """
        Get the total memory of all GPUs in MiB.

        Returns:
            Total memory in MiB
        """
        with self._lock:
            return sum(gpu.mem_total for gpu in self._gpus)

    def get_free_memory(self) -> int:
        """
        Get the free memory of all GPUs in MiB.

        Returns:
            Free memory in MiB
        """
        with self._lock:
            return sum(gpu.mem_free for gpu in self._gpus)

    def get_memory_ratio(self) -> List[float]:
        """
        Get the memory ratios between GPUs.

        Returns:
            List of memory ratios (relative to the total)
        """
        with self._lock:
            if not self._gpus:
                return []

            total_memory = sum(gpu.mem_total for gpu in self._gpus)
            if total_memory == 0:
                return [1.0 / len(self._gpus)] * len(self._gpus)

            return [gpu.mem_total / total_memory for gpu in self._gpus]

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of GPU information.

        Returns:
            Dictionary with summary information
        """
        with self._lock:
            return {
                "count": len(self._gpus),
                "total_memory": self.get_total_memory(),
                "free_memory": self.get_free_memory(),
                "gpus": [
                    {
                        "index": gpu.index,
                        "name": gpu.name,
                        "memory": {
                            "total": gpu.mem_total,
                            "free": gpu.mem_free,
                            "used": gpu.mem_used,
                            "used_percent": gpu.mem_used_percent
                        },
                        "utilization": {
                            "gpu": gpu.gpu_utilization,
                            "memory": gpu.memory_utilization
                        },
                        "temperature": gpu.temperature,
                        "power": {
                            "usage": gpu.power_usage,
                            "limit": gpu.power_limit,
                            "percent": gpu.power_usage_percent
                        }
                    }
                    for gpu in self._gpus
                ]
            }


def _query_gpu(index: int) -> GPU:
    """Query a specific GPU by index, returning a dataclass with comprehensive info."""
    handle = pynvml.nvmlDeviceGetHandleByIndex(index)

    # Basic info
    name = pynvml.nvmlDeviceGetName(handle)

    # Memory info
    mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
    mem_total = int(mem.total / 1024 / 1024)  # Convert to MiB
    mem_free = int(mem.free / 1024 / 1024)

    # Create a default GPU object with required fields
    gpu = GPU(index, name, mem_total, mem_free)

    # We'll use a dictionary to collect additional fields
    # This allows us to handle exceptions for each metric separately
    additional_info = {}

    try:
        # Driver version
        additional_info["driver_version"] = pynvml.nvmlSystemGetDriverVersion().decode("utf-8")
    except Exception as e:
        logger.debug(f"Could not get driver version: {e}")

    try:
        # Temperature
        additional_info["temperature"] = pynvml.nvmlDeviceGetTemperature(
            handle, pynvml.NVML_TEMPERATURE_GPU
        )
    except Exception as e:
        logger.debug(f"Could not get temperature for GPU {index}: {e}")

    try:
        # Utilization rates
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        additional_info["gpu_utilization"] = util.gpu
        additional_info["memory_utilization"] = util.memory
    except Exception as e:
        logger.debug(f"Could not get utilization for GPU {index}: {e}")

    try:
        # Power usage
        power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert from mW to W
        additional_info["power_usage"] = power_usage
    except Exception as e:
        logger.debug(f"Could not get power usage for GPU {index}: {e}")

    try:
        # Power limit
        power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000.0  # Convert from mW to W
        additional_info["power_limit"] = power_limit
    except Exception as e:
        logger.debug(f"Could not get power limit for GPU {index}: {e}")

    try:
        # Fan speed
        fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
        additional_info["fan_speed"] = fan_speed
    except Exception as e:
        logger.debug(f"Could not get fan speed for GPU {index}: {e}")

    try:
        # Clock speeds
        graphics_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
        additional_info["graphics_clock"] = graphics_clock

        memory_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
        additional_info["memory_clock"] = memory_clock

        sm_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
        additional_info["sm_clock"] = sm_clock
    except Exception as e:
        logger.debug(f"Could not get clock speeds for GPU {index}: {e}")

    try:
        # Compute capability
        major, minor = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
        additional_info["compute_capability"] = f"{major}.{minor}"

        # Determine architecture based on compute capability
        arch_map = {
            "5": "Maxwell",
            "6": "Pascal",
            "7": "Volta/Turing",
            "8": "Ampere",
            "9": "Hopper/Ada Lovelace"
        }
        additional_info["architecture"] = arch_map.get(str(major), "Unknown")
    except Exception as e:
        logger.debug(f"Could not get compute capability for GPU {index}: {e}")

    try:
        # PCIe info
        pcie_info = pynvml.nvmlDeviceGetMaxPcieLinkGeneration(handle)
        additional_info["pcie_gen"] = f"Gen {pcie_info}"

        pcie_width = pynvml.nvmlDeviceGetMaxPcieLinkWidth(handle)
        additional_info["pcie_width"] = pcie_width
    except Exception as e:
        logger.debug(f"Could not get PCIe info for GPU {index}: {e}")

    try:
        # CUDA cores - this is an estimate based on compute capability and multiprocessor count
        multiprocessor_count = pynvml.nvmlDeviceGetNumGpuCores(handle)
        cuda_cores_per_mp = {
            "5": 128,   # Maxwell
            "6": 64,    # Pascal
            "7": 64,    # Volta/Turing
            "8": 64,    # Ampere
            "9": 128    # Hopper/Ada Lovelace
        }
        if "compute_capability" in additional_info:
            major = additional_info["compute_capability"].split(".")[0]
            if major in cuda_cores_per_mp:
                additional_info["cuda_cores"] = multiprocessor_count * cuda_cores_per_mp[major]
    except Exception as e:
        logger.debug(f"Could not calculate CUDA cores for GPU {index}: {e}")

    # Create a new GPU object with all the collected information
    # We use _dc.replace to update the existing GPU instance with the additional fields
    return _dc.replace(gpu, **additional_info)


def _mock_gpus() -> List[GPU]:
    """Create detailed mock GPU objects for testing or demo purposes."""
    return [
        GPU(
            index=0,
            name="NVIDIA GeForce RTX 5070 Ti",
            mem_total=16384,
            mem_free=12288,
            architecture="Blackwell",
            cuda_cores=7680,
            compute_capability="9.0",
            driver_version="550.23",
            temperature=65,
            fan_speed=45,
            power_usage=220.5,
            power_limit=290.0,
            gpu_utilization=25,
            memory_utilization=18,
            graphics_clock=1850,
            memory_clock=9000,
            sm_clock=1900,
            pcie_gen="Gen 4",
            pcie_width=16
        ),
        GPU(
            index=1,
            name="NVIDIA GeForce RTX 4060 Ti",
            mem_total=8192,
            mem_free=6144,
            architecture="Ada Lovelace",
            cuda_cores=4352,
            compute_capability="8.9",
            driver_version="550.23",
            temperature=58,
            fan_speed=40,
            power_usage=135.2,
            power_limit=180.0,
            gpu_utilization=10,
            memory_utilization=15,
            graphics_clock=1750,
            memory_clock=8500,
            sm_clock=1800,
            pcie_gen="Gen 4",
            pcie_width=8
        )
    ]


def probe_gpus(max_workers: int = 4) -> List[GPU]:
    """
    Probe for NVIDIA GPUs using NVML.

    Args:
        max_workers: Maximum number of worker threads for parallel probing

    Returns:
        List of GPU objects with device information

    Raises:
        RuntimeError: If GPU detection fails
    """
    # Check if mock mode is enabled
    if os.environ.get("DGPUOPT_MOCK_GPUS") == "1":
        logger.debug("Using mock GPU data instead of real hardware")
        return _mock_gpus()

    try:
        pynvml.nvmlInit()
        try:
            gpu_count = pynvml.nvmlDeviceGetCount()
            if gpu_count == 0:
                logger.warning("No GPUs detected")
                error_msg = (
                    "No NVIDIA GPUs were detected on your system.\n"
                    "If you have NVIDIA GPUs installed, please ensure:\n"
                    "1. Your NVIDIA drivers are correctly installed\n"
                    "2. The CUDA toolkit is installed (if required)\n\n"
                    "You can run in mock mode for testing by setting the DGPUOPT_MOCK_GPUS=1 environment variable."
                )
                raise RuntimeError(error_msg)

            # Query GPUs in parallel
            with _fut.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(_query_gpu, i) for i in range(gpu_count)]
                gpus = [future.result() for future in _fut.as_completed(futures)]

            # Sort by index
            gpus.sort(key=lambda g: g.index)

            # Check if we have at least 2 GPUs for dual optimization
            if len(gpus) < 2:
                logger.warning(f"Only {len(gpus)} GPU detected, at least 2 are recommended for optimal use")

            return gpus

        finally:
            pynvml.nvmlShutdown()

    except pynvml.NVMLError_LibraryNotFound:
        error_msg = (
            "NVIDIA Management Library (NVML) not found.\n"
            "This usually means NVIDIA drivers are not installed or not detected.\n"
            "Please install the latest NVIDIA drivers for your graphics card.\n\n"
            "You can run in mock mode for testing by setting the DGPUOPT_MOCK_GPUS=1 environment variable."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except pynvml.NVMLError as err:
        error_msg = f"NVIDIA GPU detection error: {err}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as err:
        error_msg = f"GPU detection failed: {err}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)