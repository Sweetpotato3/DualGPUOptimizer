"""
ctx_size.py
===========

Heuristic for maximum safe context length.
"""
from __future__ import annotations
from dualgpuopt.gpu_info import GPU

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
    Parameters
    ----------
    precision_bits
        16 for fp16, 8 for 8‑bit QLoRA, 4 for GPTQ Q4_0.
    moe_factor
        > 1.0 for Mixtral gating cache (~1.05).
    """
    bytes_per_tok = (
        n_layers * n_kv_heads * head_dim * (precision_bits // 8) * 2 * moe_factor
    )
    free_mib = sum(g.mem_free for g in gpus) - reserve_gb * 1024
    if free_mib <= 0:
        return 2048
    return int((free_mib * 1024**2) // bytes_per_tok)