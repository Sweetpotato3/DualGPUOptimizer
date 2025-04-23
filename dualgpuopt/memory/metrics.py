"""
Memory metrics collection and processing for GPU monitoring.

This module provides classes for representing and processing GPU memory metrics.
"""

import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict


class MemoryUnit(Enum):
    """Memory units for reporting and calculations"""

    BYTES = auto()
    KB = auto()
    MB = auto()
    GB = auto()


@dataclass
class GPUMemoryStats:
    """Container for GPU memory statistics"""

    gpu_id: int  # GPU device ID
    total_memory: int  # Total memory in bytes
    used_memory: int  # Used memory in bytes
    free_memory: int  # Free memory in bytes
    reserved_memory: int = 0  # Memory reserved by the system but not used
    cached_memory: int = 0  # Memory used for caching
    process_memory: Dict[int, int] = None  # Memory used by each process
    timestamp: float = None  # When stats were collected

    def __post_init__(self):
        """Initialize optional fields if not provided"""
        if self.process_memory is None:
            self.process_memory = {}
        if self.timestamp is None:
            self.timestamp = time.time()

    def usage_percent(self) -> float:
        """Calculate memory usage as percentage"""
        return (self.used_memory / self.total_memory) * 100 if self.total_memory > 0 else 0

    def get_memory(self, unit: MemoryUnit = MemoryUnit.GB) -> Dict[str, float]:
        """Get memory values in specified unit"""
        divisor = {
            MemoryUnit.BYTES: 1,
            MemoryUnit.KB: 1024,
            MemoryUnit.MB: 1024 * 1024,
            MemoryUnit.GB: 1024 * 1024 * 1024,
        }[unit]

        return {
            "total": self.total_memory / divisor,
            "used": self.used_memory / divisor,
            "free": self.free_memory / divisor,
            "reserved": self.reserved_memory / divisor,
            "cached": self.cached_memory / divisor,
        }

    def as_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "gpu_id": self.gpu_id,
            "total_memory_bytes": self.total_memory,
            "used_memory_bytes": self.used_memory,
            "free_memory_bytes": self.free_memory,
            "reserved_memory_bytes": self.reserved_memory,
            "cached_memory_bytes": self.cached_memory,
            "usage_percent": self.usage_percent(),
            "process_memory": self.process_memory,
            "timestamp": self.timestamp,
        }
