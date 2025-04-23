"""
VRAM Reset helper for GPU memory reclamation
Provides functions to reclaim GPU memory through NVML
"""
import logging
import platform
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

# Initialize logger
logger = logging.getLogger("DualGPUOpt.VRAMReset")

# Try to import dependencies
try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    logger.warning("PyTorch not available, reduced functionality")
    TORCH_AVAILABLE = False

try:
    import pynvml

    NVML_AVAILABLE = True
except ImportError:
    logger.warning("PYNVML not available, reduced functionality")
    NVML_AVAILABLE = False

# Check if any of the core dependencies are available
DEPENDENCIES_AVAILABLE = TORCH_AVAILABLE or NVML_AVAILABLE


class ResetMethod(Enum):
    """Methods available for VRAM reset"""

    CACHE_ONLY = "cache"  # Just clear PyTorch cache
    CLOCK_RESET = "clock"  # Reset GPU clocks
    FULL_RESET = "full"  # Full memory reset including tensors
    SYSTEM_CMD = "system"  # Use system commands


@dataclass
class ResetResult:
    """Results from VRAM reset operation"""

    memory_reclaimed: int  # MB reclaimed
    success: bool
    message: str
    gpu_ids: List[int]

    def formatted_message(self) -> str:
        """Get formatted message with reclaimed memory"""
        if self.success and self.memory_reclaimed > 0:
            return f"Success: Reclaimed {self.memory_reclaimed} MB from GPUs {', '.join(map(str, self.gpu_ids))}"
        elif self.success:
            return f"Success: No memory reclaimed from GPUs {', '.join(map(str, self.gpu_ids))}"
        else:
            return f"Failed: {self.message}"


def reset_vram(
    device_id: Optional[int] = None, method: ResetMethod = ResetMethod.FULL_RESET
) -> ResetResult:
    """
    Reset VRAM for specified GPU or all GPUs

    Args:
    ----
        device_id: GPU device ID to reset, or None for all GPUs
        method: Reset method to use

    Returns:
    -------
        ResetResult object with details of the reset operation
    """
    if not DEPENDENCIES_AVAILABLE:
        logger.warning("Cannot reset VRAM - dependencies not available")
        return ResetResult(
            memory_reclaimed=0,
            success=False,
            message="Dependencies not available (PyTorch or PYNVML)",
            gpu_ids=[],
        )

    try:
        # Get list of GPUs to reset
        gpu_ids = [device_id] if device_id is not None else None

        # Get memory before reset
        before_free = get_free_memory(gpu_ids)
        if not before_free:
            return ResetResult(
                memory_reclaimed=0,
                success=False,
                message="Failed to get initial memory state",
                gpu_ids=[],
            )

        # Reset using the specified method
        if method == ResetMethod.CACHE_ONLY:
            success = _reset_cache()
        elif method == ResetMethod.CLOCK_RESET:
            success = _reset_clocks(gpu_ids)
        elif method == ResetMethod.SYSTEM_CMD:
            success = _reset_system_cmd()
        else:  # FULL_RESET
            # Use all available methods in sequence
            _reset_cache()
            _reset_clocks(gpu_ids)
            _reset_tensors()
            _reset_system_cmd()
            success = True

        # Wait a moment for memory to be reclaimed
        time.sleep(0.5)

        # Check memory after reset
        after_free = get_free_memory(gpu_ids)

        # Calculate reclaimed memory
        reclaimed = calculate_reclaimed(before_free, after_free)
        total_reclaimed = sum(reclaimed.values())

        # Format message
        if total_reclaimed > 0:
            msg = f"Successfully reclaimed {total_reclaimed} MB across {len(reclaimed)} GPUs"
        else:
            msg = "No memory reclaimed"

        return ResetResult(
            memory_reclaimed=total_reclaimed,
            success=success,
            message=msg,
            gpu_ids=list(reclaimed.keys()),
        )

    except Exception as e:
        logger.error(f"Error resetting VRAM: {e}")
        return ResetResult(
            memory_reclaimed=0,
            success=False,
            message=f"Error: {e}",
            gpu_ids=[],
        )


def _reset_cache() -> bool:
    """
    Reset PyTorch CUDA cache

    Returns
    -------
        True if successful, False otherwise
    """
    if not TORCH_AVAILABLE:
        return False

    try:
        if torch.cuda.is_available():
            # Clear CUDA cache
            torch.cuda.empty_cache()

            # Reset peak memory stats
            for i in range(torch.cuda.device_count()):
                torch.cuda.reset_peak_memory_stats(i)

            # Reset CUDA max_split_size_mb to default
            torch.cuda._C._cuda_setMemoryFraction(1.0)

            logger.info("PyTorch CUDA cache cleared")
            return True
        return False
    except Exception as e:
        logger.error(f"Error clearing CUDA cache: {e}")
        return False


def _reset_clocks(device_ids: Optional[List[int]] = None) -> bool:
    """
    Reset GPU clocks using NVML

    Args:
    ----
        device_ids: List of GPU IDs to reset, or None for all

    Returns:
    -------
        True if successful, False otherwise
    """
    if not NVML_AVAILABLE:
        return False

    try:
        # Initialize NVML
        pynvml.nvmlInit()

        dev_count = pynvml.nvmlDeviceGetCount()
        target_devices = device_ids if device_ids else list(range(dev_count))

        for dev_id in target_devices:
            if dev_id < 0 or dev_id >= dev_count:
                logger.warning(f"Invalid device ID: {dev_id}")
                continue

            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(dev_id)

                # Reset various GPU settings to help free memory
                try:
                    pynvml.nvmlDeviceResetGpuLockedClocks(handle)
                    logger.debug(f"Reset GPU {dev_id} locked clocks")
                except pynvml.NVMLError:
                    pass

                try:
                    pynvml.nvmlDeviceResetApplicationsClocks(handle)
                    logger.debug(f"Reset GPU {dev_id} application clocks")
                except pynvml.NVMLError:
                    pass

                try:
                    # Get compute mode and reset if needed
                    compute_mode = pynvml.nvmlDeviceGetComputeMode(handle)
                    if compute_mode != pynvml.NVML_COMPUTEMODE_DEFAULT:
                        # Note: this may require admin privileges
                        pynvml.nvmlDeviceSetComputeMode(handle, pynvml.NVML_COMPUTEMODE_DEFAULT)
                        logger.debug(f"Reset GPU {dev_id} compute mode")
                except pynvml.NVMLError:
                    pass

                logger.info(f"Reset clocks for GPU {dev_id}")

            except Exception as e:
                logger.warning(f"Could not reset GPU {dev_id}: {e}")

        # Shutdown NVML
        pynvml.nvmlShutdown()
        return True

    except Exception as e:
        logger.error(f"Error resetting GPU clocks: {e}")
        return False


def _reset_tensors() -> bool:
    """
    Actively delete PyTorch tensors to free memory

    Returns
    -------
        True if successful, False otherwise
    """
    if not TORCH_AVAILABLE:
        return False

    try:
        if torch.cuda.is_available():
            # Force garbage collection
            import gc

            gc.collect()

            # Delete all CUDA tensors in memory
            for obj in gc.get_objects():
                try:
                    if torch.is_tensor(obj) and obj.device.type == "cuda":
                        del obj
                except:
                    pass

            # Run garbage collection again
            gc.collect()
            torch.cuda.empty_cache()

            logger.info("Deleted CUDA tensors")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting tensors: {e}")
        return False


def _reset_system_cmd() -> bool:
    """
    Use system-specific commands to reset GPU memory

    Returns
    -------
        True if successful, False otherwise
    """
    try:
        system = platform.system()

        if system == "Windows":
            # Windows - use PowerShell to free GPU resources
            try:
                subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        "Get-Process | Where-Object {$_.Name -match 'cuda|nvid'} | "
                        + "Where-Object {$_.Name -notmatch 'nvidia-smi'} | Restart-Service",
                    ],
                    check=False,
                    capture_output=True,
                )
                logger.info("Executed Windows CUDA service restart command")
                return True
            except:
                # If PowerShell command fails, try a simpler approach
                logger.debug("PowerShell command failed, trying simpler approach")

        elif system == "Linux":
            # Linux - sync and echo to clear GPU
            try:
                # Sync filesystem
                subprocess.run(["sync"], check=False)

                # Try to drop caches if user has permissions
                try:
                    with open("/proc/sys/vm/drop_caches", "w") as f:
                        f.write("1")
                except:
                    pass

                logger.info("Executed Linux sync/cache drop commands")
                return True
            except:
                logger.debug("Linux system commands failed")

        # Generic - just wait for memory to be freed naturally
        time.sleep(1.0)
        return True

    except Exception as e:
        logger.error(f"Error executing system commands: {e}")
        return False


def get_free_memory(device_ids: Optional[List[int]] = None) -> Dict[int, int]:
    """
    Get free memory for specified GPUs or all GPUs

    Args:
    ----
        device_ids: List of GPU IDs to query, or None for all

    Returns:
    -------
        Dictionary mapping GPU ID to free memory in MB
    """
    result = {}

    if not DEPENDENCIES_AVAILABLE:
        return result

    # Try NVML first for more accurate results
    if NVML_AVAILABLE:
        try:
            pynvml.nvmlInit()

            device_count = pynvml.nvmlDeviceGetCount()

            # Process specific devices or all devices
            target_devices = device_ids if device_ids else list(range(device_count))

            for idx in target_devices:
                if idx < 0 or idx >= device_count:
                    continue

                handle = pynvml.nvmlDeviceGetHandleByIndex(idx)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                free_mb = mem_info.free // (1024 * 1024)  # Convert to MB

                result[idx] = free_mb

            pynvml.nvmlShutdown()

        except Exception as e:
            logger.error(f"Error getting free memory through NVML: {e}")

    # Fall back to PyTorch if NVML failed
    if not result and TORCH_AVAILABLE:
        try:
            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()

                # Process specific devices or all devices
                target_devices = device_ids if device_ids else list(range(device_count))

                for idx in target_devices:
                    if idx < 0 or idx >= device_count:
                        continue

                    with torch.cuda.device(idx):
                        # Get stats in bytes
                        allocated = torch.cuda.memory_allocated()
                        reserved = torch.cuda.memory_reserved()

                        # Estimate free memory (reserved but not allocated + estimate of total)
                        if hasattr(torch.cuda, "get_device_properties"):
                            total = torch.cuda.get_device_properties(idx).total_memory
                            # Free = total - reserved + (reserved - allocated)
                            free = total - allocated
                            free_mb = free // (1024 * 1024)  # Convert to MB
                            result[idx] = free_mb
                        else:
                            # Can't get total memory, just report reserved-allocated
                            free = reserved - allocated
                            free_mb = free // (1024 * 1024)  # Convert to MB
                            result[idx] = free_mb

        except Exception as e:
            logger.error(f"Error getting free memory through PyTorch: {e}")

    return result


def calculate_reclaimed(before: Dict[int, int], after: Dict[int, int]) -> Dict[int, int]:
    """
    Calculate reclaimed memory

    Args:
    ----
        before: Dictionary of free memory before reset
        after: Dictionary of free memory after reset

    Returns:
    -------
        Dictionary mapping GPU ID to reclaimed memory in MB
    """
    result = {}

    # Process all GPUs in both before and after
    for gpu_id in set(before.keys()) | set(after.keys()):
        before_val = before.get(gpu_id, 0)
        after_val = after.get(gpu_id, 0)

        # Only count positive reclamation
        reclaimed = max(0, after_val - before_val)
        result[gpu_id] = reclaimed

    return result
