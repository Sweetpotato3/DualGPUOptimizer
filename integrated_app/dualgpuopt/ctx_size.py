"""
ctx_size.py
===========

Heuristic for maximum safe context length.
"""
from __future__ import annotations

import logging

from dualgpuopt.gpu_info import GPU

logger = logging.getLogger("dualgpuopt.ctx_size")


def calc_max_ctx(
    gpus: list[GPU],
    *,
    n_layers: int,
    n_kv_heads: int,
    head_dim: int,
    precision_bits: int = 16,
    moe_factor: float = 1.0,
    reserve_gb: int = 2,
) -> int:
    """
    Calculate the maximum safe context size based on GPU parameters.

    Parameters
    ----------
    gpus
        List of GPU objects to use for context calculation
    n_layers
        Number of model layers
    n_kv_heads
        Number of key-value heads
    head_dim
        Dimension per head
    precision_bits
        16 for fp16, 8 for 8‑bit QLoRA, 4 for GPTQ Q4_0
    moe_factor
        > 1.0 for Mixtral gating cache (~1.05)
    reserve_gb
        Amount of memory in GB to reserve for other operations

    Returns
    -------
    int
        Maximum safe context size
    """
    bytes_per_tok = n_layers * n_kv_heads * head_dim * (precision_bits // 8) * 2 * moe_factor
    free_mib = sum(g.mem_free for g in gpus) - reserve_gb * 1024

    if free_mib <= 0:
        logger.warning("Not enough free memory, defaulting to 2048 context size")
        return 2048

    return int((free_mib * 1024**2) // bytes_per_tok)


def model_params_from_name(model_name: str) -> tuple[int, int, int, float]:
    """
    Estimate model parameters from a model name.

    Args:
    ----
        model_name: Name of the model file

    Returns:
    -------
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

    return n_layers, n_kv_heads, head_dim, moe_factor
