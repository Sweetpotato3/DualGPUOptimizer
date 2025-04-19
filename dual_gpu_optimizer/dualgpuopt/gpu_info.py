"""
GPU discovery via NVML – no GUI, no optimisation math.
"""
from __future__ import annotations

import concurrent.futures as _fut
import dataclasses as _dc
import logging
from typing import List, Optional

try:
    import pynvml  # external, tiny
except ImportError as _exc:
    raise RuntimeError(
        "pynvml missing – pip install nvidia‑ml‑py3 inside your 3.13 environment"
    ) from _exc

# Configure logging
logger = logging.getLogger("dualgpuopt.gpu_info")


@_dc.dataclass(slots=True, frozen=True)
class GPU:
    index: int
    name: str
    mem_total: int  # MiB
    mem_free: int   # MiB

    @property
    def mem_total_gb(self) -> int:
        return self.mem_total // 1024


def _grab_single(idx: int) -> Optional[GPU]:
    """Safely retrieve information for a single GPU."""
    try:
        h = pynvml.nvmlDeviceGetHandleByIndex(idx)
        info = pynvml.nvmlDeviceGetMemoryInfo(h)
        return GPU(
            index=idx,
            name=pynvml.nvmlDeviceGetName(h).decode(),
            mem_total=info.total // 1024 ** 2,
            mem_free=info.free // 1024 ** 2,
        )
    except pynvml.NVMLError as err:
        logger.warning(f"Failed to query GPU {idx}: {err}")
        return None


def probe_gpus() -> List[GPU]:
    """
    Discover available NVIDIA GPUs using NVML.
    
    Returns:
        List of GPU objects sorted by index
        
    Raises:
        RuntimeError: If NVML initialization fails
    """
    try:
        pynvml.nvmlInit()
        try:
            cnt = pynvml.nvmlDeviceGetCount()
            if cnt == 0:
                logger.warning("No NVIDIA GPUs detected")
                return []
                
            with _fut.ThreadPoolExecutor(max_workers=cnt) as pool:
                gpu_results = list(pool.map(_grab_single, range(cnt)))
            
            # Filter out None values (failed queries)
            gpus = [gpu for gpu in gpu_results if gpu is not None]
            return sorted(gpus, key=lambda g: g.index)
        finally:
            pynvml.nvmlShutdown()
    except pynvml.NVMLError as err:
        logger.error(f"NVML initialization failed: {err}")
        raise RuntimeError(f"GPU detection failed: {err}") 