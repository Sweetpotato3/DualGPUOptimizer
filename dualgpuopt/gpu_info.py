"""
GPU info module with platform-independent GPU detection
(Compatibility layer for refactored gpu module)
"""
from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional

# Set up the logger
logger = logging.getLogger("DualGPUOpt.GPUInfo")

# Import from refactored GPU module
try:
    # Import the core functionality from the refactored modules
    from dualgpuopt.gpu.common import IS_NVIDIA, IS_MAC, MOCK_MODE, NVML_INITIALIZED
    from dualgpuopt.gpu.info import query, get_gpu_count, get_gpu_names
    from dualgpuopt.gpu.mock import set_mock_mode, get_mock_mode, generate_mock_gpus
    from dualgpuopt.gpu.monitor import get_memory_info, get_utilization, get_temperature, get_power_usage
    
    logger.info("Successfully imported refactored GPU module")
except ImportError as e:
    logger.error(f"Failed to import refactored GPU module: {e}")
    # Keep basic functionality working if refactored modules fail to import
    IS_NVIDIA = True
    IS_MAC = False
    MOCK_MODE = True
    NVML_INITIALIZED = False
    
    def query() -> List[Dict[str, Any]]:
        """Fallback query function that returns mock data"""
        return _generate_mock_gpus()
        
    def get_gpu_count() -> int:
        """Fallback GPU count function"""
        return len(query())
        
    def get_gpu_names() -> List[str]:
        """Fallback GPU names function"""
        return [gpu["name"] for gpu in query()]
        
    def set_mock_mode(enabled: bool) -> None:
        """Fallback to enable/disable mock mode"""
        global MOCK_MODE
        MOCK_MODE = enabled
        logger.info(f"Mock GPU mode {'enabled' if enabled else 'disabled'}")
        
    def get_mock_mode() -> bool:
        """Get current mock mode status"""
        return MOCK_MODE
        
    def get_memory_info(gpu_id: int = 0) -> Dict[str, int]:
        """Fallback memory info function"""
        gpus = query()
        if gpu_id < len(gpus):
            gpu = gpus[gpu_id]
            return {
                "total": gpu["mem_total"],
                "used": gpu["mem_used"],
                "free": gpu["mem_total"] - gpu["mem_used"]
            }
        return {"total": 0, "used": 0, "free": 0}
        
    def get_utilization(gpu_id: int = 0) -> int:
        """Fallback utilization function"""
        gpus = query()
        if gpu_id < len(gpus):
            return gpus[gpu_id]["util"]
        return 0
        
    def get_temperature(gpu_id: int = 0) -> float:
        """Fallback temperature function"""
        gpus = query()
        if gpu_id < len(gpus):
            return gpus[gpu_id]["temperature"]
        return 0.0
        
    def get_power_usage(gpu_id: int = 0) -> float:
        """Fallback power usage function"""
        gpus = query()
        if gpu_id < len(gpus):
            return gpus[gpu_id]["power_usage"]
        return 0.0

# Compatibility function for code expecting get_gpu_info
def get_gpu_info() -> List[Dict[str, Any]]:
    """Get GPU information (compatibility function)"""
    return query()

# Mock GPU class for compatibility
class GPU:
    """GPU class for backward compatibility"""
    def __init__(self, gpu_data: Dict[str, Any]):
        self.id = gpu_data.get("id", 0)
        self.name = gpu_data.get("name", "Unknown GPU")
        self.type = gpu_data.get("type", "unknown")
        self.mem_total = gpu_data.get("mem_total", 0)
        self.mem_used = gpu_data.get("mem_used", 0)
        self.util = gpu_data.get("util", 0)
        self.temperature = gpu_data.get("temperature", 0.0)
        self.power_usage = gpu_data.get("power_usage", 0.0)
        self.clock_sm = gpu_data.get("clock_sm", 0)
        self.clock_memory = gpu_data.get("clock_memory", 0)
    
    @property
    def mem_free(self) -> int:
        """Get free memory in MB"""
        return self.mem_total - self.mem_used
    
    def get_memory_info(self) -> Dict[str, int]:
        """Get memory information"""
        return {
            "total": self.mem_total,
            "used": self.mem_used,
            "free": self.mem_free
        }
    
    def get_utilization(self) -> int:
        """Get GPU utilization"""
        return self.util
    
    def get_temperature(self) -> float:
        """Get GPU temperature"""
        return self.temperature
    
    def get_power_usage(self) -> float:
        """Get power usage in watts"""
        return self.power_usage
    
    @classmethod
    def get_gpus(cls) -> List["GPU"]:
        """Get list of GPU objects"""
        return [cls(gpu_data) for gpu_data in query()]
    
    @classmethod
    def get_gpu_count(cls) -> int:
        """Get number of GPUs"""
        return get_gpu_count()
    
    @classmethod
    def get_gpu_names(cls) -> List[str]:
        """Get list of GPU names"""
        return get_gpu_names()

# For backward compatibility - re-export the _generate_mock_gpus function
_generate_mock_gpus = generate_mock_gpus 