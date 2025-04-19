"""
GPU discovery via NVML – no GUI, no optimisation math.
"""
from __future__ import annotations

import concurrent.futures as _fut
import dataclasses as _dc
import logging
import os
from typing import List, Optional

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
    """GPU information container."""
    index: int
    name: str
    mem_total: int  # MiB
    mem_free: int   # MiB
    
    @property
    def mem_used(self) -> int:
        """Return used memory in MiB."""
        return self.mem_total - self.mem_free
    
    @property
    def mem_total_gb(self) -> int:
        """Return total memory in GB (rounded)."""
        return round(self.mem_total / 1024)


def _query_gpu(index: int) -> GPU:
    """Query a specific GPU by index, returning a dataclass with info."""
    handle = pynvml.nvmlDeviceGetHandleByIndex(index)
    
    # Get device name (decode from bytes)
    name = pynvml.nvmlDeviceGetName(handle).decode("utf-8")
    
    # Get memory info
    mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
    mem_total = int(mem.total / 1024 / 1024)  # Convert to MiB
    mem_free = int(mem.free / 1024 / 1024)
    
    return GPU(index, name, mem_total, mem_free)


def _mock_gpus() -> List[GPU]:
    """Create mock GPU objects for testing or demo purposes."""
    return [
        GPU(0, "NVIDIA GeForce RTX 3090", 24576, 20480),  # 24GB
        GPU(1, "NVIDIA GeForce RTX 3080", 10240, 8192),   # 10GB
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
        logger.info("Using mock GPU data instead of real hardware")
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