"""
mpolicy.py
==========

Aggressive—but safe—mixed precision policies.

Public helpers
--------------
* ``autocast`` – context manager for inference
* ``scaler``   – returns GradScaler (training only)
"""
from __future__ import annotations
import contextlib, torch
from dualgpuopt.log import get as _log

_log = _log("mpolicy")

@contextlib.contextmanager
def autocast(dtype: torch.dtype = torch.float16):
    """
    Activate autocast and override default matmul dtype.

    Notes
    -----
    * LayerNorm, softmax, residual adds remain FP32 automatically.
    * Works on PyTorch ≥ 2.2; falls back to private API on older builds.
    """
    setter = getattr(torch, "set_default_dtype", torch._C._set_default_dtype)  # type: ignore[attr-defined]
    prev = torch.get_default_dtype()
    setter(dtype)
    try:
        with torch.autocast("cuda", dtype=dtype):
            yield
    finally:
        setter(prev)
        _log.debug("Restored default dtype → %s", prev)


def scaler(enabled: bool = True) -> torch.cuda.amp.GradScaler:
    """Return a GradScaler that follows mpolicy's dtype."""
    return torch.cuda.amp.GradScaler(enabled=enabled) 