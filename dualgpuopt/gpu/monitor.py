"""
GPU monitoring module for retrieving specific metrics
"""
from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional, Tuple, Union

from dualgpuopt.gpu.info import query
from dualgpuopt.gpu.common import GpuMetrics, ensure_float, ensure_int

def get_memory_info(gpu_id: Optional[int] = None) -> Union[Dict[str, int], List[Dict[str, int]]]:
    """Get memory information for one or all GPUs
    
    Args:
        gpu_id: Optional GPU ID to get memory info for. If None, get for all GPUs.
        
    Returns:
        Dictionary with memory info or list of dictionaries for all GPUs
    """
    gpus = query()
    
    if gpu_id is not None:
        if gpu_id >= len(gpus):
            raise ValueError(f"GPU ID {gpu_id} is out of range. Only {len(gpus)} GPUs available.")
        
        gpu = gpus[gpu_id]
        return {
            "total": ensure_int(gpu[GpuMetrics.MEMORY_TOTAL]),
            "used": ensure_int(gpu[GpuMetrics.MEMORY_USED]),
            "free": ensure_int(gpu[GpuMetrics.MEMORY_TOTAL]) - ensure_int(gpu[GpuMetrics.MEMORY_USED])
        }
    
    return [
        {
            "total": ensure_int(gpu[GpuMetrics.MEMORY_TOTAL]),
            "used": ensure_int(gpu[GpuMetrics.MEMORY_USED]),
            "free": ensure_int(gpu[GpuMetrics.MEMORY_TOTAL]) - ensure_int(gpu[GpuMetrics.MEMORY_USED])
        }
        for gpu in gpus
    ]

def get_utilization(gpu_id: Optional[int] = None) -> Union[int, List[int]]:
    """Get utilization percentage for one or all GPUs
    
    Args:
        gpu_id: Optional GPU ID to get utilization for. If None, get for all GPUs.
        
    Returns:
        Utilization percentage or list of percentages for all GPUs
    """
    gpus = query()
    
    if gpu_id is not None:
        if gpu_id >= len(gpus):
            raise ValueError(f"GPU ID {gpu_id} is out of range. Only {len(gpus)} GPUs available.")
        
        return ensure_int(gpus[gpu_id][GpuMetrics.UTILIZATION])
    
    return [ensure_int(gpu[GpuMetrics.UTILIZATION]) for gpu in gpus]

def get_temperature(gpu_id: Optional[int] = None) -> Union[float, List[float]]:
    """Get temperature for one or all GPUs
    
    Args:
        gpu_id: Optional GPU ID to get temperature for. If None, get for all GPUs.
        
    Returns:
        Temperature in Celsius or list of temperatures for all GPUs
    """
    gpus = query()
    
    if gpu_id is not None:
        if gpu_id >= len(gpus):
            raise ValueError(f"GPU ID {gpu_id} is out of range. Only {len(gpus)} GPUs available.")
        
        return ensure_float(gpus[gpu_id][GpuMetrics.TEMPERATURE])
    
    return [ensure_float(gpu[GpuMetrics.TEMPERATURE]) for gpu in gpus]

def get_power_usage(gpu_id: Optional[int] = None) -> Union[float, List[float]]:
    """Get power usage for one or all GPUs
    
    Args:
        gpu_id: Optional GPU ID to get power usage for. If None, get for all GPUs.
        
    Returns:
        Power usage in Watts or list of power usages for all GPUs
    """
    gpus = query()
    
    if gpu_id is not None:
        if gpu_id >= len(gpus):
            raise ValueError(f"GPU ID {gpu_id} is out of range. Only {len(gpus)} GPUs available.")
        
        return ensure_float(gpus[gpu_id][GpuMetrics.POWER_USAGE])
    
    return [ensure_float(gpu[GpuMetrics.POWER_USAGE]) for gpu in gpus] 