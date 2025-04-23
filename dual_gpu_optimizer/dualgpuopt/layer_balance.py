"""
layer_balance.py
================

Adaptive latency‑aware layer redistribution.

Key routine
-----------
``rebalance(model, gpu_info, warm_input)``  →  dict device_map
"""
from __future__ import annotations
import json, pathlib, time
from typing import Any, Dict, List
from dualgpuopt.log import get as _log

_log = _log("layer_balance")

# Check if torch is available
try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    _log.warning("PyTorch not available - layer balancing will be disabled")


def _profile_pass(model, dummy) -> List[int]:
    if not TORCH_AVAILABLE:
        _log.error("profile_pass called but PyTorch is not available")
        return []

    times = []
    with torch.no_grad():
        for blk in model.model.layers:  # type: ignore[attr-defined]
            start = time.perf_counter_ns()
            blk(dummy)
            times.append(time.perf_counter_ns() - start)
    return times


def profile_layers(model, dummy) -> List[float]:
    """Weight two sequence lengths to account for attention scaling."""
    if not TORCH_AVAILABLE:
        _log.error("profile_layers called but PyTorch is not available")
        return []

    t_short = _profile_pass(model, dummy[:, :64])
    t_long = _profile_pass(model, dummy[:, :1024])
    return [0.2 * s + 0.8 * l for s, l in zip(t_short, t_long)]


def rebalance(
    model,
    gpus: list[Dict[str, Any]],
    dummy_input_ids,
    reserve_ratio: float = 0.9,
) -> Dict[str, int]:
    """
    Return layer→GPU mapping while respecting per‑GPU VRAM quota.

    Note: No-op if PyTorch is not available.
    """
    if not TORCH_AVAILABLE:
        _log.error("rebalance called but PyTorch is not available")
        return {}

    lat = profile_layers(model, dummy_input_ids)

    if not lat:  # Empty list means profiling failed
        _log.error("Layer profiling failed - cannot rebalance")
        return {}

    idx_fast, idx_slow = gpus[0]["idx"], gpus[1]["idx"]
    quota_fast = gpus[0]["mem_total"] * reserve_ratio
    used_fast = 0
    mapping: Dict[str, int] = {}
    for i, dur in sorted(enumerate(lat), key=lambda x: x[1], reverse=True):
        tgt = idx_fast if used_fast + dur < quota_fast else idx_slow
        mapping[f"model.layers.{i}"] = tgt
        if tgt == idx_fast:
            used_fast += dur
    pathlib.Path("device_map.json").write_text(json.dumps(mapping, indent=2))
    _log.info("Adaptive map saved → device_map.json")
    return mapping
