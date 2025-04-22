"""
GPU memory planning for optimal model distribution.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default constants (can be overridden through environment variables)
SYSTEM_OVERHEAD_MB = int(os.getenv("DUALGPUOPT_SYSTEM_OVERHEAD", "2048"))  # System memory overhead
SAFETY_MARGIN = float(os.getenv("DUALGPUOPT_SAFETY_MARGIN", "0.1"))  # 10% safety margin
TP_OVERHEAD = float(os.getenv("DUALGPUOPT_TP_OVERHEAD", "0.2"))  # 20% tensor parallelism overhead
KV_CACHE_FACTOR = float(os.getenv("DUALGPUOPT_KV_CACHE_FACTOR", "2.0"))  # KV cache size multiplier
MIN_CONTEXT_SIZE = int(os.getenv("DUALGPUOPT_MIN_CONTEXT", "128"))  # Minimum context size to consider

def calculate_gpu_split(
    model_bytes: int,
    gpu_info: List[Dict[str, int]],
    safety_margin: float = SAFETY_MARGIN
) -> Tuple[List[float], Dict[str, Any]]:
    """
    Calculate optimal split ratios for model across available GPUs.
    
    Args:
        model_bytes: Model size in bytes
        gpu_info: List of GPU info dictionaries with memory_total (in MB)
        safety_margin: Safety margin as a fraction of total memory
        
    Returns:
        Tuple containing:
        - List of split ratios (e.g. [0.6, 0.4] for 60%/40% split)
        - Dictionary with additional information (total memory, etc.)
    """
    if not gpu_info:
        raise ValueError("No GPU information provided")
    
    # Convert model size from bytes to MB for easier calculations
    model_size_mb = model_bytes / (1024 * 1024)
    logger.info(f"Model size: {model_size_mb:.2f} MB")
    
    # Calculate available memory for each GPU (applying safety margin)
    gpu_available_mb = []
    for gpu in gpu_info:
        total_mb = gpu["memory_total"]
        available_mb = total_mb * (1.0 - safety_margin)
        gpu_available_mb.append(available_mb)
    
    total_available_mb = sum(gpu_available_mb)
    logger.info(f"Total available memory: {total_available_mb:.2f} MB")
    
    # Calculate if model fits in available memory
    if model_size_mb > total_available_mb:
        logger.warning(f"Model size ({model_size_mb:.2f} MB) exceeds available memory ({total_available_mb:.2f} MB)")
        
    # Calculate optimal split ratios based on available memory
    split_ratios = [gpu_mb / total_available_mb for gpu_mb in gpu_available_mb]
    
    # Calculate actual memory usage on each GPU
    memory_usage = [ratio * model_size_mb for ratio in split_ratios]
    
    # Create result dictionary with additional information
    result_info = {
        "model_size_mb": model_size_mb,
        "total_available_mb": total_available_mb,
        "gpu_available_mb": gpu_available_mb,
        "memory_usage_mb": memory_usage,
        "fits_in_memory": model_size_mb <= total_available_mb
    }
    
    return split_ratios, result_info

def calculate_max_context_size(
    model_bytes: int,
    gpu_info: List[Dict[str, int]],
    kv_cache_bytes_per_token: int,
    batch_size: int = 1,
    safety_margin: float = SAFETY_MARGIN
) -> int:
    """
    Calculate maximum context size based on model size and available memory.
    
    Args:
        model_bytes: Model size in bytes
        gpu_info: List of GPU info dictionaries with memory_total (in MB)
        kv_cache_bytes_per_token: Bytes per token in KV cache
        batch_size: Batch size for inference
        safety_margin: Safety margin as a fraction of total memory
        
    Returns:
        Maximum context size in tokens
    """
    # First calculate split ratios
    split_ratios, info = calculate_gpu_split(model_bytes, gpu_info, safety_margin)
    
    # If model doesn't fit, return minimum context size
    if not info["fits_in_memory"]:
        logger.warning("Model doesn't fit in available memory, returning minimum context size")
        return MIN_CONTEXT_SIZE
    
    # Calculate remaining memory on each GPU after loading model
    remaining_memory_mb = []
    for i, gpu in enumerate(gpu_info):
        total_mb = gpu["memory_total"]
        used_mb = info["memory_usage_mb"][i]
        remaining_mb = (total_mb * (1.0 - safety_margin)) - used_mb
        remaining_memory_mb.append(remaining_mb)
    
    # Calculate bytes per token in KV cache with batch size
    kv_cache_bytes_per_batch_token = kv_cache_bytes_per_token * batch_size
    
    # Convert to MB for consistency
    kv_cache_mb_per_token = kv_cache_bytes_per_batch_token / (1024 * 1024)
    
    # Use the most constrained GPU to determine max context
    min_remaining_mb = min(remaining_memory_mb)
    
    # Calculate max tokens based on remaining memory and KV cache size
    max_tokens = int(min_remaining_mb / kv_cache_mb_per_token)
    
    # Apply minimum context size constraint
    max_tokens = max(max_tokens, MIN_CONTEXT_SIZE)
    
    logger.info(f"Calculated max context size: {max_tokens} tokens")
    return max_tokens

def fit_plan(
    model_bytes: int, 
    gpus: Optional[List[Dict[str, int]]] = None
) -> Dict[str, Any]:
    """
    Create a complete fitting plan for the model.
    
    Args:
        model_bytes: Model size in bytes
        gpus: Optional list of GPU info dictionaries (if None, will use detected GPUs)
        
    Returns:
        Dictionary with the complete fitting plan
    """
    # If GPUs not provided, use environment default
    if gpus is None:
        # This is a placeholder - in a real implementation you would
        # detect GPUs or use a mock if none available
        gpus = [{"memory_total": 8192}]  # Default to one 8GB GPU
    
    logger.info(f"Planning for {len(gpus)} GPUs with {model_bytes} byte model")
    
    # Calculate GPU split ratios
    split_ratios, split_info = calculate_gpu_split(model_bytes, gpus)
    
    # Estimate KV cache size for this model (based on model size heuristic)
    # This is a simplified estimate - real implementation would use model specifics
    hidden_size = (model_bytes / 5e9) * 2048  # Rough estimate of hidden size based on model size
    layers = (model_bytes / 5e9) * 32  # Rough estimate of layers based on model size
    
    kv_bytes_per_token = int(2 * hidden_size * layers * 2)  # q,k,v projections for each layer
    
    # Calculate context sizes for different batch sizes
    context_sizes = {}
    for batch_size in [1, 4, 8]:
        context_sizes[str(batch_size)] = calculate_max_context_size(
            model_bytes, 
            gpus, 
            kv_bytes_per_token,
            batch_size
        )
    
    # Format GPU split string for llama.cpp (if multiple GPUs)
    llama_cpp_split = None
    if len(gpus) > 1:
        # Format as "0:ratio0,1:ratio1,..."
        # Ensure ratios are scaled to add up to 1.0
        total_ratio = sum(split_ratios)
        normalized_ratios = [r / total_ratio for r in split_ratios]
        llama_cpp_split = ",".join([f"{i}:{ratio:.2f}" for i, ratio in enumerate(normalized_ratios)])
    
    # Create the complete plan
    plan = {
        "model_size_mb": int(model_bytes / (1024 * 1024)),
        "gpus": [{"id": i, **gpu} for i, gpu in enumerate(gpus)],
        "split_ratios": split_ratios,
        "memory_usage": split_info["memory_usage_mb"],
        "context_sizes": context_sizes,
        "recommended_batch_size": 1 if len(gpus) == 1 else 4,
        "tensor_parallel_size": len(gpus),
        "llama_cpp_split": llama_cpp_split,
        "vllm_gpu_memory_utilization": 0.8 if split_info["fits_in_memory"] else 0.5,
        "fits_in_memory": split_info["fits_in_memory"]
    }
    
    return plan

# Example usage if run directly
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate GPU memory plan for model")
    parser.add_argument("--model-size", type=int, required=True, help="Model size in bytes")
    parser.add_argument("--gpu-memory", type=str, required=True, 
                      help="Comma-separated list of GPU memory sizes in MB")
    parser.add_argument("--output", type=str, help="Output JSON file path")
    
    args = parser.parse_args()
    
    # Parse GPU memory sizes
    gpu_memory_sizes = [int(size.strip()) for size in args.gpu_memory.split(",")]
    gpus = [{"memory_total": size} for size in gpu_memory_sizes]
    
    # Generate plan
    plan = fit_plan(args.model_size, gpus)
    
    # Print or save plan
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(plan, f, indent=2)
        print(f"Plan saved to {args.output}")
    else:
        print(json.dumps(plan, indent=2))
