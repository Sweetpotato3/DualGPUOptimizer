"""
Layer balance optimization for multi-GPU model distribution
Optimally distributes model layers across available GPUs
"""
import json
import pathlib
import time
from typing import Dict, List, Any, Optional
import logging

# Initialize logger
logger = logging.getLogger("DualGPUOpt.LayerBalance")

# Check for PyTorch dependency
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    logger.warning("PyTorch not available - layer balancing will be disabled")
    TORCH_AVAILABLE = False


def profile_layers(model: Any, dummy_input: Any) -> List[float]:
    """Profile each model layer with both short and long sequences
    
    Args:
        model: PyTorch model to profile
        dummy_input: Dummy input tensor for profiling
        
    Returns:
        List of timing measurements for each layer
    """
    if not TORCH_AVAILABLE:
        logger.error("profile_layers called but PyTorch is not available")
        return []
    
    try:
        # Get short sequence timings (64 tokens)
        short_times = _profile_pass(model, dummy_input[:, :64])
        
        # Get long sequence timings (1024 tokens)
        long_times = _profile_pass(model, dummy_input[:, :1024])
        
        # Weight both timings (20% short, 80% long)
        return [0.2 * s + 0.8 * l for s, l in zip(short_times, long_times)]
    except Exception as e:
        logger.error(f"Error profiling layers: {e}")
        return []


def _profile_pass(model: Any, dummy_input: Any) -> List[int]:
    """Profile a single pass through the model
    
    Args:
        model: PyTorch model to profile
        dummy_input: Input tensor
        
    Returns:
        List of timing measurements in nanoseconds
    """
    times = []
    
    try:
        with torch.no_grad():
            for blk in model.model.layers:
                start = time.perf_counter_ns()
                blk(dummy_input)
                times.append(time.perf_counter_ns() - start)
    except Exception as e:
        logger.error(f"Error in profile pass: {e}")
    
    return times


def rebalance(
    model: Any,
    gpus: List[Dict[str, Any]],
    dummy_input: Any,
    reserve_ratio: float = 0.9,
    output_path: Optional[pathlib.Path] = None
) -> Dict[str, int]:
    """Calculate optimal layer-to-GPU mapping respecting memory quotas
    
    Args:
        model: PyTorch model to rebalance
        gpus: List of GPU dictionaries with 'idx' and 'mem_total' keys
        dummy_input: Dummy input tensor for profiling
        reserve_ratio: Ratio of GPU memory to reserve for operations
        output_path: Optional path to save the device map
        
    Returns:
        Dictionary mapping layer names to GPU indices
    """
    if not TORCH_AVAILABLE:
        logger.error("rebalance called but PyTorch is not available")
        return {}
    
    # Get layer timings
    lat = profile_layers(model, dummy_input)
    
    if not lat:
        logger.error("Layer profiling failed - cannot rebalance")
        return {}
    
    # Get GPU indices and memory quotas
    idx_fast, idx_slow = gpus[0]["idx"], gpus[1]["idx"]
    quota_fast = gpus[0]["mem_total"] * reserve_ratio
    used_fast = 0
    mapping = {}
    
    # Sort layers by timing (slowest first)
    for i, duration in sorted(enumerate(lat), key=lambda x: x[1], reverse=True):
        # Assign to fast GPU if within quota, otherwise to slow GPU
        target = idx_fast if used_fast + duration < quota_fast else idx_slow
        mapping[f"model.layers.{i}"] = target
        
        # Track fast GPU usage
        if target == idx_fast:
            used_fast += duration
    
    # Save mapping to disk
    if output_path:
        output_path.write_text(json.dumps(mapping, indent=2))
        logger.info(f"Saved device map to {output_path}")
    else:
        # Use default path
        default_path = pathlib.Path("device_map.json")
        default_path.write_text(json.dumps(mapping, indent=2))
        logger.info("Saved device map to device_map.json")
    
    return mapping 