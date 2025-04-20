"""
Layer balancing module for distributing model layers across multiple GPUs
"""
from __future__ import annotations
import time, logging, json, pathlib
from typing import Dict, List, Optional, Tuple, Any
import math
import os

logger = logging.getLogger("DualGPUOpt.LayerBalance")

class LayerProfiler:
    """Profiles transformer layer performance across multiple GPUs"""
    
    def __init__(self, use_cache: bool = True, cache_dir: Optional[str] = None):
        """Initialize profiler
        
        Args:
            use_cache: Whether to use cached profiling results
            cache_dir: Directory to store profiling cache
        """
        self.use_cache = use_cache
        self.cache_dir = cache_dir or os.path.join(os.path.expanduser("~"), ".dualgpuopt")
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def profile(self, model: Any, dummy_ids: Any, dev: int, seq_lengths: List[int] = [64, 1024]) -> Dict[int, List[float]]:
        """
        Profile execution time of each transformer layer on a specific GPU with multiple sequence lengths
        
        Args:
            model: The transformer model
            dummy_ids: Tensor with dummy token IDs for profiling
            dev: Device ID to profile on
            seq_lengths: List of sequence lengths to profile with
            
        Returns:
            Dictionary mapping sequence length to list of execution times per layer
        """
        try:
            import torch
            
            # Check for cached results
            cache_file = os.path.join(self.cache_dir, f"profile_gpu{dev}_{model.__class__.__name__}.json")
            if self.use_cache and os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                    
                    # Convert string keys back to integers
                    results = {int(k): v for k, v in cached_data.items()}
                    
                    logger.info(f"Using cached profiling results from {cache_file}")
                    return results
                except Exception as e:
                    logger.warning(f"Failed to load profiling cache: {e}")
            
            # Move model to the target device
            model.to(dev)
            results = {}
            
            with torch.no_grad():
                # Profile with different sequence lengths
                for seq_len in seq_lengths:
                    # Create dummy input tensors of appropriate size
                    if seq_len != dummy_ids.shape[1]:
                        # Create new tensor with the required sequence length
                        if seq_len > dummy_ids.shape[1]:
                            # Repeat the existing tensor to reach required length
                            repeats = math.ceil(seq_len / dummy_ids.shape[1])
                            test_ids = torch.cat([dummy_ids] * repeats, dim=1)[:, :seq_len]
                        else:
                            # Slice the existing tensor
                            test_ids = dummy_ids[:, :seq_len]
                    else:
                        test_ids = dummy_ids
                    
                    # Move input to target device
                    test_ids = test_ids.to(dev)
                    
                    # Warmup
                    for _ in range(3):
                        for blk in model.model.layers:
                            blk(test_ids)
                    
                    # Actual profiling
                    times = []
                    # Measure each layer with multiple runs for stability
                    for blk in model.model.layers:
                        # Time 5 runs and take average
                        layer_times = []
                        for _ in range(5):
                            torch.cuda.synchronize(dev)
                            t0 = time.perf_counter()
                            blk(test_ids)
                            torch.cuda.synchronize(dev)
                            layer_times.append(time.perf_counter() - t0)
                        
                        # Discard highest and lowest, take mean of the rest
                        layer_times.sort()
                        avg_time = sum(layer_times[1:-1]) / len(layer_times[1:-1])
                        times.append(avg_time)
                    
                    results[seq_len] = times
            
            # Cache the results
            if self.use_cache:
                try:
                    with open(cache_file, 'w') as f:
                        json.dump(results, f, indent=2)
                    logger.info(f"Saved profiling results to {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to save profiling cache: {e}")
            
            return results
            
        except ImportError:
            logger.warning("PyTorch not available for profiling, using mock data")
            # Generate mock profiling data with a sensible pattern
            results = {}
            for seq_len in seq_lengths:
                import random
                # Create realistic mock data where:
                # - Later layers tend to be slower than earlier layers
                # - Longer sequences take more time proportionally
                n_layers = 32  # Assume 32 layers as default
                base_time = 0.001  # Base time in seconds
                seq_factor = seq_len / 64.0  # Scaling factor for sequence length
                
                times = []
                for i in range(n_layers):
                    # Apply a gradual increase for later layers
                    layer_factor = 1.0 + (i / n_layers) * 0.5
                    # Add random variation (±15%)
                    random_factor = random.uniform(0.85, 1.15)
                    times.append(base_time * seq_factor * layer_factor * random_factor)
                
                results[seq_len] = times
            
            return results
                
        except Exception as e:
            logger.error(f"Error during profiling: {e}")
            # Return mock data on error
            import random
            return {64: [random.uniform(0.001, 0.005) for _ in range(32)],
                    1024: [random.uniform(0.005, 0.015) for _ in range(32)]}

def rebalance(model: Any, dev_fast: int, dev_slow: int, reserve_ratio: float = 0.9) -> Dict[str, int]:
    """
    Alias for balance_layers with the same signature for backward compatibility
    """
    return balance_layers(model, dev_fast, dev_slow, reserve_ratio)

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
        
        # Enhanced profiling with multiple sequence lengths
        profiler = LayerProfiler()
        fast_profiles = profiler.profile(model, dummy, dev_fast)
        slow_profiles = profiler.profile(model, dummy, dev_slow)
        
        # Calculate weighted performance ratio
        # We weight long sequences more heavily as they have more impact on inference performance
        weights = {
            64: 0.2,    # Short sequences get 20% weight
            1024: 0.8   # Long sequences get 80% weight
        }
        
        weighted_perf_ratio = []
        layer_count = len(fast_profiles[64])  # Use first profile to get layer count
        
        for i in range(layer_count):
            ratio_sum = 0.0
            weight_sum = 0.0
            
            for seq_len, weight in weights.items():
                if seq_len in fast_profiles and seq_len in slow_profiles:
                    fast_time = fast_profiles[seq_len][i]
                    slow_time = slow_profiles[seq_len][i]
                    
                    # Calculate ratio (faster GPU typically has lower time)
                    if slow_time > 0:
                        ratio = fast_time / slow_time
                        ratio_sum += ratio * weight
                        weight_sum += weight
            
            # Compute weighted average if we have valid measurements
            if weight_sum > 0:
                weighted_perf_ratio.append(ratio_sum / weight_sum)
            else:
                # Fallback to default ratio if profiling failed
                weighted_perf_ratio.append(0.7)
        
        logger.info(f"Computed weighted performance ratio across {len(weighted_perf_ratio)} layers")
        
    except ImportError:
        logger.warning("PyTorch not available, using estimated performance ratio")
        # Generate estimated performance ratios
        import random
        n_layers = 32  # Assume 32 layers as default
        
        # Create a more realistic pattern where ratio tends to vary by layer position
        weighted_perf_ratio = []
        for i in range(n_layers):
            # Base ratio around 0.7 (faster GPU takes 70% of time)
            base_ratio = 0.7
            # Early and late layers often have different characteristics
            position_factor = 1.0 + 0.2 * abs((i / n_layers) - 0.5)
            # Add some randomness
            random_factor = random.uniform(0.9, 1.1)
            
            weighted_perf_ratio.append(base_ratio * position_factor * random_factor)
    
    # Create device mapping based on performance
    mapping = {}
    
    # Get layer count from profiling or use default
    n_layers = len(weighted_perf_ratio)
    
    # Calculate quota based on weighted performance ratios
    quota = sum(weighted_perf_ratio) * reserve_ratio
    used = 0.0
    
    # Sort layers by relative performance advantage (highest first)
    # This assigns the layers where fast GPU has greatest advantage to it first
    layer_indices_by_performance = sorted(
        range(n_layers), 
        key=lambda i: weighted_perf_ratio[i], 
        reverse=True
    )
    
    # First pass: assign layers with highest performance differential
    for i in layer_indices_by_performance:
        perf_ratio = weighted_perf_ratio[i]
        target_dev = dev_fast if used < quota else dev_slow
        mapping[f"model.layers.{i}"] = target_dev
        
        if target_dev == dev_fast:
            used += perf_ratio
    
    # Second pass: optimize for contiguous blocks where possible
    optimized_mapping = optimize_contiguous_blocks(mapping, n_layers)
    
    # Map other model components
    # Input embeddings typically go on first GPU
    optimized_mapping["model.embed_tokens"] = dev_fast
    
    # Output components typically go on last GPU
    optimized_mapping["model.norm"] = dev_slow
    optimized_mapping["lm_head"] = dev_slow
    
    # Save mapping to file for reference
    path = pathlib.Path("device_map.json")
    path.write_text(json.dumps(optimized_mapping, indent=2))
    
    # Log layer distribution
    fast_layers = sum(1 for dev in optimized_mapping.values() if dev == dev_fast)
    slow_layers = sum(1 for dev in optimized_mapping.values() if dev == dev_slow)
    logger.info(f"Layer balance: {fast_layers} layers on GPU {dev_fast}, {slow_layers} layers on GPU {dev_slow}")
    logger.info(f"Saved device mapping to {path} (assigned {used:.1f}/{quota:.1f} to GPU {dev_fast})")
    
    return optimized_mapping

def optimize_contiguous_blocks(mapping: Dict[str, int], n_layers: int) -> Dict[str, int]:
    """
    Optimize mapping to create more contiguous blocks of layers on the same GPU
    
    Args:
        mapping: Original mapping from layer names to device IDs
        n_layers: Total number of layers
        
    Returns:
        Optimized mapping with more contiguous blocks
    """
    # Extract the original device assignments
    devices = [mapping.get(f"model.layers.{i}", 0) for i in range(n_layers)]
    
    # Find boundaries where device changes
    boundaries = []
    for i in range(1, n_layers):
        if devices[i] != devices[i-1]:
            boundaries.append(i)
    
    # No boundaries or just one transition? Mapping is already optimal
    if len(boundaries) <= 1:
        return mapping
    
    # Look for small isolated blocks (1-2 layers) and merge them with neighbors
    changes_made = True
    while changes_made and len(boundaries) > 1:
        changes_made = False
        
        # Calculate block sizes
        blocks = []
        start = 0
        for b in boundaries:
            blocks.append((start, b-1))
            start = b
        blocks.append((start, n_layers-1))
        
        # Check for small blocks
        for i, (start, end) in enumerate(blocks):
            block_size = end - start + 1
            
            # Small block - try to merge with neighbors
            if 1 <= block_size <= 2:
                # Determine which neighbor to merge with
                if i == 0:
                    # First block - merge with second
                    target_device = devices[blocks[1][0]]
                    for j in range(start, end+1):
                        devices[j] = target_device
                elif i == len(blocks) - 1:
                    # Last block - merge with previous
                    target_device = devices[blocks[-2][1]]
                    for j in range(start, end+1):
                        devices[j] = target_device
                else:
                    # Middle block - merge with larger neighbor
                    prev_size = blocks[i-1][1] - blocks[i-1][0] + 1
                    next_size = blocks[i+1][1] - blocks[i+1][0] + 1
                    
                    if prev_size >= next_size:
                        target_device = devices[blocks[i-1][0]]
                    else:
                        target_device = devices[blocks[i+1][0]]
                    
                    for j in range(start, end+1):
                        devices[j] = target_device
                
                changes_made = True
                break
        
        # Recalculate boundaries if changes were made
        if changes_made:
            boundaries = []
            for i in range(1, n_layers):
                if devices[i] != devices[i-1]:
                    boundaries.append(i)
    
    # Create new mapping
    optimized = {}
    for i in range(n_layers):
        optimized[f"model.layers.{i}"] = devices[i]
    
    # Add any other keys from the original mapping
    for key, value in mapping.items():
        if not key.startswith("model.layers."):
            optimized[key] = value
    
    return optimized

def get_device_map(save_path: Optional[str] = None, gpu_ratios: Optional[List[float]] = None) -> Dict[str, int]:
    """
    Get a device map for a typical dual-GPU setup without profiling
    
    Args:
        save_path: Optional path to save the device map JSON
        gpu_ratios: Optional ratio for layer distribution, like [0.6, 0.4]
        
    Returns:
        Dictionary mapping layer names to device IDs
    """
    # Simple heuristic - split layers based on ratios or evenly
    n_layers = 32  # Assume 32 layers for a typical model like LLaMA-2 7B
    
    if gpu_ratios and len(gpu_ratios) >= 2:
        # Normalize ratios
        total = sum(gpu_ratios[:2])
        if total <= 0:
            # Invalid ratios, use even split
            ratio_0 = 0.5
        else:
            ratio_0 = gpu_ratios[0] / total
    else:
        # Default to even split
        ratio_0 = 0.5
    
    # Calculate split point
    split_point = round(n_layers * ratio_0)
    
    # Create mapping
    mapping = {}
    for i in range(n_layers):
        mapping[f"model.layers.{i}"] = 0 if i < split_point else 1
    
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