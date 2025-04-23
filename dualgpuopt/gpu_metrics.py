"""
GPU metrics data class for the DualGPUOptimizer.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class GPUMetrics:
    """Container for GPU metrics"""

    # Basic information
    id: int = 0
    name: str = "Unknown GPU"
    
    # Utilization metrics
    utilization: int = 0
    memory_used: int = 0
    memory_total: int = 0
    memory_percent: float = 0.0
    
    # Thermal metrics
    temperature: int = 0
    
    # Power metrics
    power_usage: int = 0
    power_limit: int = 0
    power_percent: float = 0.0
    
    # Clock speeds
    clock_sm: int = 0
    clock_memory: int = 0
    
    # PCIe throughput
    pcie_tx: int = 0
    pcie_rx: int = 0 