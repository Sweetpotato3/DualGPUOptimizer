"""
layer_balance.py
================

Adaptive latency‑aware layer redistribution.

Key routine
-----------
``rebalance(model, gpu_info, warm_input)``  →  dict device_map
"""
from __future__ import annotations

import json
import logging
import pathlib
import time
from typing import Any, Optional

logger = logging.getLogger("dualgpuopt.layer_balance")

# Check if torch is available
try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available - layer balancing will be disabled")


def _profile_pass(model: Any, dummy: Any) -> list[int]:
    """
    Profile a single forward pass through all layers of the model.

    Args:
    ----
        model: PyTorch model
        dummy: Input tensor

    Returns:
    -------
        List of execution times in nanoseconds for each layer
    """
    if not TORCH_AVAILABLE:
        logger.error("profile_pass called but PyTorch is not available")
        return []

    times = []
    with torch.no_grad():
        for blk in model.model.layers:  # type: ignore[attr-defined]
            start = time.perf_counter_ns()
            blk(dummy)
            times.append(time.perf_counter_ns() - start)
    return times


def profile_layers(model: Any, dummy: Any) -> list[float]:
    """
    Weight two sequence lengths to account for attention scaling.

    Args:
    ----
        model: PyTorch model
        dummy: Input tensor

    Returns:
    -------
        List of weighted execution times
    """
    if not TORCH_AVAILABLE:
        logger.error("profile_layers called but PyTorch is not available")
        return []

    t_short = _profile_pass(model, dummy[:, :64])
    t_long = _profile_pass(model, dummy[:, :1024])
    return [0.2 * s + 0.8 * l for s, l in zip(t_short, t_long)]


def rebalance(
    model: Any,
    gpus: list[dict[str, Any]],
    dummy_input_ids: Any,
    reserve_ratio: float = 0.9,
    output_path: Optional[pathlib.Path] = None,
) -> dict[str, int]:
    """
    Return layer→GPU mapping while respecting per‑GPU VRAM quota.

    Args:
    ----
        model: PyTorch model
        gpus: List of GPU dictionaries with 'idx' and 'mem_total' keys
        dummy_input_ids: Input tensor for profiling
        reserve_ratio: Ratio of GPU memory to reserve for other operations
        output_path: Optional path to save the device map

    Returns:
    -------
        Dictionary mapping layer names to GPU indices

    Note: No-op if PyTorch is not available.
    """
    if not TORCH_AVAILABLE:
        logger.error("rebalance called but PyTorch is not available")
        return {}

    lat = profile_layers(model, dummy_input_ids)

    if not lat:  # Empty list means profiling failed
        logger.error("Layer profiling failed - cannot rebalance")
        return {}

    idx_fast, idx_slow = gpus[0]["idx"], gpus[1]["idx"]
    quota_fast = gpus[0]["mem_total"] * reserve_ratio
    used_fast = 0
    mapping: dict[str, int] = {}

    for i, dur in sorted(enumerate(lat), key=lambda x: x[1], reverse=True):
        tgt = idx_fast if used_fast + dur < quota_fast else idx_slow
        mapping[f"model.layers.{i}"] = tgt
        if tgt == idx_fast:
            used_fast += dur

    # Save to disk if path provided
    if output_path:
        output_path.write_text(json.dumps(mapping, indent=2))
        logger.info(f"Adaptive map saved → {output_path}")
    else:
        # Default path
        default_path = pathlib.Path("device_map.json")
        default_path.write_text(json.dumps(mapping, indent=2))
        logger.info("Adaptive map saved → device_map.json")

    return mapping


def convert_gpu_format(gpus: list[Any]) -> list[dict[str, Any]]:
    """
    Convert GPU objects to the format expected by rebalance.

    Args:
    ----
        gpus: List of GPU objects

    Returns:
    -------
        List of dictionaries with 'idx' and 'mem_total' keys
    """
    return [{"idx": gpu.index, "mem_total": gpu.mem_total} for gpu in gpus]
