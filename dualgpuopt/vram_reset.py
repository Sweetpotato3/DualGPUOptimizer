"""
VRAM Reset helper for GPU memory reclamation
Provides functions to reclaim GPU memory through NVML
"""
from typing import Dict, List, Optional, Tuple, Union
import logging

# Initialize logger
logger = logging.getLogger("DualGPUOpt.VRAMReset")

try:
    import torch
    import pynvml
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    logger.warning("Dependencies not available (torch/pynvml), using mock functionality")
    DEPENDENCIES_AVAILABLE = False


def reset_vram(device_id: Optional[int] = None) -> Tuple[int, str]:
    """Reset VRAM for specified GPU or all GPUs
    
    Args:
        device_id: GPU device ID to reset, or None for all GPUs
        
    Returns:
        Tuple of (MB reclaimed, status message)
    """
    if not DEPENDENCIES_AVAILABLE:
        logger.warning("Cannot reset VRAM - dependencies not available")
        return 0, "Dependencies not available"
    
    try:
        # Initialize NVML
        pynvml.nvmlInit()
        
        # Get used memory before reset
        before_free = get_free_memory(device_id)
        
        # Empty CUDA cache first
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("CUDA cache cleared")
        
        # Try device reset if specific device specified
        if device_id is not None:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
                pynvml.nvmlDeviceResetGpuLockedClocks(handle)
                pynvml.nvmlDeviceResetApplicationsClocks(handle)
                logger.info(f"Reset clocks for GPU {device_id}")
            except Exception as e:
                logger.warning(f"Could not reset clocks for GPU {device_id}: {e}")
        
        # Check memory after reset
        after_free = get_free_memory(device_id)
        
        # Calculate reclaimed memory
        reclaimed = calculate_reclaimed(before_free, after_free)
        
        # Shutdown NVML
        pynvml.nvmlShutdown()
        
        # Format message
        if sum(reclaimed.values()) > 0:
            msg = f"Successfully reclaimed {sum(reclaimed.values())} MB across {len(reclaimed)} GPUs"
        else:
            msg = "No memory reclaimed"
            
        return sum(reclaimed.values()), msg
        
    except Exception as e:
        logger.error(f"Error resetting VRAM: {e}")
        return 0, f"Error: {e}"


def get_free_memory(device_id: Optional[int] = None) -> Dict[int, int]:
    """Get free memory for specified GPU or all GPUs
    
    Args:
        device_id: GPU device ID or None for all GPUs
        
    Returns:
        Dictionary mapping GPU ID to free memory in MB
    """
    result = {}
    
    if not DEPENDENCIES_AVAILABLE:
        return result
    
    try:
        device_count = pynvml.nvmlDeviceGetCount()
        
        # Process specific device or all devices
        devices = [device_id] if device_id is not None else range(device_count)
        
        for idx in devices:
            if idx < 0 or idx >= device_count:
                continue
                
            handle = pynvml.nvmlDeviceGetHandleByIndex(idx)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            free_mb = mem_info.free // (1024 * 1024)  # Convert to MB
            
            result[idx] = free_mb
            
    except Exception as e:
        logger.error(f"Error getting free memory: {e}")
        
    return result


def calculate_reclaimed(before: Dict[int, int], after: Dict[int, int]) -> Dict[int, int]:
    """Calculate reclaimed memory
    
    Args:
        before: Dictionary of free memory before reset
        after: Dictionary of free memory after reset
        
    Returns:
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