"""
Layer balancing module for distributing model layers across multiple GPUs
"""
from __future__ import annotations
import time, logging, json, pathlib
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger("DualGPUOpt.LayerBalance")

def profile(model: Any, dummy_ids: Any, dev: int) -> list[float]:
    """
    Profile execution time of each transformer layer on a specific GPU
    
    Args:
        model: The transformer model
        dummy_ids: Tensor with dummy token IDs for profiling
        dev: Device ID to profile on
        
    Returns:
        List of execution times (seconds) for each layer
    """
    try:
        import torch
        
        model.to(dev)
        times = []
        
        with torch.no_grad():
            for blk in model.model.layers:  # type: ignore
                t0 = time.perf_counter()
                blk(dummy_ids.to(dev))
                times.append(time.perf_counter() - t0)
                
        return times
    except ImportError:
        logger.warning("PyTorch not available for profiling, using mock data")
        # Generate mock profiling data
        import random
        return [random.uniform(0.001, 0.005) for _ in range(32)]  # Assume 32 layers
    except Exception as e:
        logger.error(f"Error during profiling: {e}")
        # Return mock data on error
        import random
        return [random.uniform(0.001, 0.005) for _ in range(32)]

def balance_layers(model: Any, 
                   dev_fast: int, 
                   dev_slow: int, 
                   reserve_ratio: float = 0.9) -> Dict[str, int]:
    """
    Balance model layers across two GPUs based on performance profiling
    
    Args:
        model: The transformer model
        dev_fast: The faster GPU device ID
        dev_slow: The slower GPU device ID
        reserve_ratio: Ratio of layers to assign to faster GPU (0.0-1.0)
        
    Returns:
        Dictionary mapping layer names to device IDs
    """
    try:
        import torch
        # Create dummy input for profiling (128 tokens)
        dummy = torch.randint(10, (1, 128))
        
        # Profile execution time on both GPUs
        lat_fast = profile(model, dummy, dev_fast)
        lat_slow = profile(model, dummy, dev_slow)
        
        # Calculate relative performance
        relative_perf = [f/s for f, s in zip(lat_fast, lat_slow)]
        
    except ImportError:
        logger.warning("PyTorch not available, using estimated performance ratio")
        # Generate estimated performance ratios (faster GPU = 0.7x the time)
        import random
        n_layers = 32  # Assume 32 layers as default
        relative_perf = [0.7 + random.uniform(-0.1, 0.1) for _ in range(n_layers)]
    
    # Create device mapping based on performance
    mapping = {}
    quota = sum(relative_perf) * reserve_ratio  # Total "weight" to assign to faster GPU
    used = 0.0
    
    # Sort by relative performance (highest first)
    # This assigns the layers where fast GPU has greatest advantage to it first
    for i, r in sorted(enumerate(relative_perf), key=lambda x: x[1], reverse=True):
        target_dev = dev_fast if used < quota else dev_slow
        mapping[f"model.layers.{i}"] = target_dev
        
        if target_dev == dev_fast:
            used += r
    
    # Save mapping to file for reference
    path = pathlib.Path("device_map.json")
    path.write_text(json.dumps(mapping, indent=2))
    logger.info(f"Saved device mapping to {path} (assigned {used:.1f}/{quota:.1f} to GPU {dev_fast})")
    
    return mapping

def get_device_map(save_path: Optional[str] = None) -> Dict[str, int]:
    """
    Get a device map for a typical dual-GPU setup without profiling
    
    Args:
        save_path: Optional path to save the device map JSON
        
    Returns:
        Dictionary mapping layer names to device IDs
    """
    # Simple heuristic - split layers evenly between GPUs
    # For a typical 32-layer model like LLaMA-2 7B
    n_layers = 32
    
    # Assign first half to GPU 0, second half to GPU 1
    mapping = {}
    for i in range(n_layers):
        mapping[f"model.layers.{i}"] = 0 if i < n_layers // 2 else 1
    
    # Add standard model components
    mapping["model.embed_tokens"] = 0
    mapping["model.norm"] = 1
    mapping["lm_head"] = 1
    
    # Save to file if requested
    if save_path:
        path = pathlib.Path(save_path)
        path.write_text(json.dumps(mapping, indent=2))
        logger.info(f"Saved simple device map to {save_path}")
    
    return mapping 