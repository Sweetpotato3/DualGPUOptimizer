"""
Context size calculator for determining maximum safe token window size
"""
from __future__ import annotations
import logging
from typing import Optional, Tuple

from . import gpu_info

logger = logging.getLogger("DualGPUOpt.CtxSize")

def calc(n_layers: int, n_kv: int, dim: int, bits: int = 16,
         moe: float = 1.0, reserve_mib: int = 2048) -> int:
    """
    Calculate maximum context length that fits in available GPU memory
    
    Args:
        n_layers: Number of transformer layers
        n_kv: Number of key-value heads
        dim: Hidden dimension size
        bits: Precision in bits (default: 16)
        moe: Mixture of Experts factor (default: 1.0)
        reserve_mib: Reserved memory in MiB (default: 2048)
        
    Returns:
        Maximum context length in tokens
    """
    # Calculate bytes per token = 2 * layers * KV heads * dimensions * (bits/8) * moe
    # 2 because we store both K and V
    bytes_per_token = 2 * n_layers * n_kv * dim * (bits // 8) * moe
    
    # Get total available memory across all GPUs
    gpus = gpu_info.query()
    if not gpus:
        logger.warning("No GPUs found, using fallback context size")
        return 2048  # Fallback size
    
    # Calculate total free memory in bytes
    total_free = sum(g["mem_total"] - g["mem_used"] for g in gpus) * 1024 * 1024
    
    # Subtract reserved memory
    total_free -= reserve_mib * 1024 * 1024
    
    if total_free <= 0:
        logger.warning("Insufficient free memory, using fallback context size")
        return 2048  # Fallback if no usable memory
    
    # Calculate maximum tokens that can fit
    max_tokens = int(total_free / bytes_per_token)
    
    # Apply constraints - round down to nearest 256 for alignment
    max_tokens = (max_tokens // 256) * 256
    
    logger.info(f"Calculated max context size: {max_tokens} tokens " +
               f"(using {n_layers} layers, {n_kv} KV heads, {dim} dim, {bits} bits)")
    
    return max_tokens

def get_max_context_for_model(model_name: str, reserve_mib: int = 2048) -> int:
    """
    Get maximum context size for a known model preset
    
    Args:
        model_name: Name of model (e.g., "Llama-2 7B", "Mistral 7B")
        reserve_mib: Reserved memory in MiB
        
    Returns:
        Maximum context length in tokens
    """
    model_params = {
        "llama-2 7b": (32, 32, 4096),   # layers, kv_heads, dim
        "llama-2 13b": (40, 40, 5120),
        "llama-2 70b": (80, 8, 8192),   # Grouped query attention
        "mistral 7b": (32, 8, 4096),    # Grouped query attention
        "mixtral 8x7b": (32, 8, 4096, 1.5),  # MoE factor 1.5
        "phi-2": (32, 32, 2560),
    }
    
    # Normalize model name for lookup
    norm_name = model_name.lower().replace("-", " ").replace("_", " ")
    
    if norm_name in model_params:
        params = model_params[norm_name]
        moe_factor = 1.0 if len(params) < 4 else params[3]
        return calc(params[0], params[1], params[2], 16, moe_factor, reserve_mib)
    else:
        logger.warning(f"Unknown model '{model_name}', using base LLaMA-2 7B parameters")
        return calc(32, 32, 4096, 16, 1.0, reserve_mib)  # Default LLaMA-2 7B 