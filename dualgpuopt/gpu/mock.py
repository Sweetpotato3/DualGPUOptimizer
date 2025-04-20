"""
Mock GPU module for testing without actual hardware
"""
from __future__ import annotations
import random
import logging
import sys
from typing import Dict, Any, List, Optional

from dualgpuopt.gpu.common import MOCK_MODE, logger

def set_mock_mode(enabled: bool) -> None:
    """Enable or disable mock GPU mode"""
    global MOCK_MODE
    from dualgpuopt.gpu.common import MOCK_MODE as COMMON_MOCK_MODE
    
    # Update in both modules to maintain consistency
    MOCK_MODE = enabled
    vars(sys.modules['dualgpuopt.gpu.common'])['MOCK_MODE'] = enabled
    
    logger.info(f"Mock GPU mode {'enabled' if enabled else 'disabled'}")

def get_mock_mode() -> bool:
    """Get current mock mode status"""
    from dualgpuopt.gpu.common import MOCK_MODE
    return MOCK_MODE

def generate_mock_gpus(gpu_count: int = 2) -> List[Dict[str, Any]]:
    """Generate mock GPU data for testing
    
    Args:
        gpu_count: Number of mock GPUs to generate (default: 2)
        
    Returns:
        List of dictionaries with mock GPU data
    """
    # Generate realistic GPU data for testing
    gpu_templates = [
        {
            "name": "NVIDIA GeForce RTX 4090",
            "mem_total": 24576,  # 24 GB
            "mem_base_used": 1024,  # Base memory usage (1 GB)
            "max_util": 98,
            "max_temp": 85,
            "power_range": (30, 450),  # Min/max power in W
        },
        {
            "name": "NVIDIA GeForce RTX 4080",
            "mem_total": 16384,  # 16 GB
            "mem_base_used": 768,  # Base memory usage
            "max_util": 98,
            "max_temp": 83,
            "power_range": (25, 320),  # Min/max power in W
        },
    ]
    
    # Set a fixed seed for deterministic results when testing
    random.seed(42)
    
    mock_gpus = []
    
    for i in range(gpu_count):
        # Use the template for this index, or repeat the last one if out of templates
        template_idx = min(i, len(gpu_templates) - 1)
        template = gpu_templates[template_idx]
        
        # Random utilization between 1-max_util
        util = random.randint(1, template["max_util"])
        
        # Memory usage correlates somewhat with utilization
        mem_used = template["mem_base_used"] + int(util / 100 * (template["mem_total"] * 0.4))
        
        # Temperature correlates with utilization
        temp_base = 35.0
        temp_range = template["max_temp"] - temp_base
        temp = temp_base + (util / 100 * temp_range)
        
        # Power usage correlates with utilization
        pmin, pmax = template["power_range"]
        power = pmin + (util / 100 * (pmax - pmin))
        
        # Clock speeds correlate with utilization
        clock_base = 500
        clock_max = 2500
        clock = clock_base + (util / 100 * (clock_max - clock_base))
        
        mock_gpus.append({
            "id": i,
            "name": template["name"],
            "type": "nvidia",
            "util": util,
            "mem_total": template["mem_total"],
            "mem_used": mem_used,
            "temperature": float(temp),  # Ensure temperature is a float
            "power_usage": float(power),  # Ensure power is a float
            "clock_sm": int(clock),
            "clock_memory": int(clock * 0.75),  # Memory clock is typically lower
        })
    
    # Reset the random seed
    random.seed(None)
    
    return mock_gpus 