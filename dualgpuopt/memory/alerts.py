"""
Memory alert definitions and handling for GPU monitoring.

This module provides classes for representing and handling memory alerts
based on GPU usage thresholds.
"""

import time
from enum import Enum, auto
from typing import Any, Callable, Dict, List


class MemoryAlertLevel(Enum):
    """Alert levels for memory monitoring"""

    NORMAL = auto()  # Memory usage normal
    WARNING = auto()  # Memory usage high but acceptable
    CRITICAL = auto()  # Memory usage approaching danger zone
    EMERGENCY = auto()  # Memory usage extremely high, OOM likely


class MemoryAlert:
    """Memory alert notification with context and recommendations"""

    def __init__(
        self,
        level: MemoryAlertLevel,
        gpu_id: int,
        message: str,
        current_usage: float,
        threshold: float,
        timestamp: float = None,
        recommendations: List[str] = None,
        context: Dict[str, Any] = None,
    ):
        """
        Initialize memory alert

        Args:
        ----
            level: Alert severity level
            gpu_id: GPU device ID
            message: Alert message
            current_usage: Current memory usage percentage
            threshold: Threshold percentage that triggered the alert
            timestamp: Alert timestamp
            recommendations: List of recommended actions
            context: Additional context information

        """
        self.level = level
        self.gpu_id = gpu_id
        self.message = message
        self.current_usage = current_usage
        self.threshold = threshold
        self.timestamp = timestamp or time.time()
        self.recommendations = recommendations or []
        self.context = context or {}

    def __str__(self) -> str:
        """String representation of the alert"""
        return f"[GPU {self.gpu_id}] {self.level.name}: {self.message} ({self.current_usage:.1f}% > {self.threshold:.1f}%)"


# Type for memory alert callbacks
MemoryAlertCallback = Callable[[MemoryAlert], None]
