"""
Memory-aware context size calculator for LLMs
Provides functions to calculate maximum safe context size based on GPU memory
"""
from typing import List, Tuple
import logging

# Initialize logger
logger = logging.getLogger("DualGPUOpt.CtxSize")

# Try to import core dependencies
try:
    from .gpu_info import GPU
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    logger.warning("GPU info module not available")
    DEPENDENCIES_AVAILABLE = False


def calc_max_ctx(
    gpus: List['GPU'],
    *,
    n_layers: int,
    n_kv_heads: int,
    head_dim: int,
    precision_bits: int = 16,
    moe_factor: float = 1.0,
    reserve_gb: int = 2,
) -> int:
    """Calculate maximum safe context size based on GPU parameters
    
    Args:
        gpus: List of GPU objects
        n_layers: Number of model layers
        n_kv_heads: Number of key-value heads
        head_dim: Dimension per head
        precision_bits: Precision in bits (16 for FP16, 8 for INT8, etc.)
        moe_factor: MoE overhead factor (1.05 for Mixtral)
        reserve_gb: Amount of memory to reserve in GB
        
    Returns:
        Maximum safe context length
    """
    if not DEPENDENCIES_AVAILABLE:
        # Return a conservative default if dependencies aren't available
        return 4096
    
    # Calculate bytes per token
    bytes_per_token = (
        n_layers * n_kv_heads * head_dim * (precision_bits // 8) * 2 * moe_factor
    )
    
    # Calculate free memory
    free_mib = sum(g.mem_free for g in gpus) - reserve_gb * 1024
    
    # Check if we have enough memory
    if free_mib <= 0:
        logger.warning("Not enough free memory for context calculation")
        return 2048
    
    # Calculate maximum context length
    max_ctx = int((free_mib * 1024**2) // bytes_per_token)
    
    # Apply a safety margin of 10%
    max_ctx = int(max_ctx * 0.9)
    
    return max_ctx


def model_params_from_name(model_name: str) -> Tuple[int, int, int, float]:
    """Estimate model parameters from model name
    
    Args:
        model_name: Name of the model file
        
    Returns:
        Tuple of (n_layers, n_kv_heads, head_dim, moe_factor)
    """
    model_name = model_name.lower()
    
    # Default values
    n_layers = 32
    n_kv_heads = 8
    head_dim = 128
    moe_factor = 1.0
    
    # Mixtral parameters
    if "mixtral" in model_name:
        n_layers = 32
        n_kv_heads = 8
        head_dim = 128
        moe_factor = 1.05
    
    # Llama 2 parameters
    elif "llama-2" in model_name or "llama2" in model_name:
        if "7b" in model_name:
            n_layers = 32
            n_kv_heads = 32
            head_dim = 128
        elif "13b" in model_name:
            n_layers = 40
            n_kv_heads = 40
            head_dim = 128
        elif "70b" in model_name:
            n_layers = 80
            n_kv_heads = 8
            head_dim = 128
    
    # Mistral parameters
    elif "mistral" in model_name:
        n_layers = 32
        n_kv_heads = 8
        head_dim = 128
    
    # Phi-2 parameters
    elif "phi-2" in model_name or "phi2" in model_name:
        n_layers = 32
        n_kv_heads = 32
        head_dim = 80
    
    return n_layers, n_kv_heads, head_dim, moe_factor 