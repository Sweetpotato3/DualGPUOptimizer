from __future__ import annotations

import math
import os
import pathlib
from typing import Dict, List

import psutil

_COEF = {"fp16": 0.48, "fp8": 0.27, "awq": 0.18, "gguf": 0.15}
_OFFROOT = pathlib.Path(
    os.getenv("DUALGPUOPT_OFFLOAD_DIR", pathlib.Path.home() / ".dualgpuopt" / "offload")
)


def _need(params_b: float, quant: str) -> float:
    return _COEF[quant] * params_b  # GiB


def fit_plan(size_bytes: int, gpus: List[Dict], safety=0.85) -> Dict:
    params_b = size_bytes / 1e9 / _COEF["fp16"]
    vram = min(g["memory_total"] for g in gpus) / 1024
    ram = psutil.virtual_memory().available / 1.073e9
    # 1 full GPU
    for q in ("awq", "gguf", "fp8", "fp16"):
        if _need(params_b, q) < vram * safety:
            return {"quant": q, "disk": False}
    # 2 llama.cpp split
    layers = int(vram * safety / _COEF["gguf"] * 32)
    if layers > 0 and (_need(params_b, "gguf") - layers / 32 * _COEF["gguf"]) < ram * safety:
        return {"quant": "gguf", "gpu_layers": layers, "disk": False}
    # 3 host RAM off‑load
    if _need(params_b, "fp16") < ram * safety:
        _OFFROOT.mkdir(parents=True, exist_ok=True)
        return {
            "quant": "fp16",
            "device_map": "balanced_low_0",
            "offload_dir": str(_OFFROOT),
            "disk": False,
        }
    # 4 SSD spill
    swap = math.ceil(_need(params_b, "fp16") - ram) + 2
    _OFFROOT.mkdir(parents=True, exist_ok=True)
    return {
        "quant": "fp16",
        "device_map": "balanced_low_0",
        "offload_dir": str(_OFFROOT),
        "swap": swap,
        "gpu_util": 0.70,
        "disk": True,
    }
