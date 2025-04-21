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
import contextlib, typing as _t
from dualgpuopt.log import get as _log

_log = _log("mpolicy")

# Check if torch is available
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    _log.warning("PyTorch not available - mixed precision operations will be disabled")

@contextlib.contextmanager
def autocast(dtype=None):
    """
    Activate autocast and override default matmul dtype.

    Notes
    -----
    * LayerNorm, softmax, residual adds remain FP32 automatically.
    * Works on PyTorch ≥ 2.2; falls back to private API on older builds.
    * No-op if PyTorch is not available.
    """
    if not TORCH_AVAILABLE:
        _log.warning("autocast called but PyTorch is not available")
        yield
        return

    setter = getattr(torch, "set_default_dtype", torch._C._set_default_dtype)  # type: ignore[attr-defined]
    prev = torch.get_default_dtype()
    if dtype is None:
        dtype = torch.float16
    setter(dtype)
    try:
        with torch.autocast("cuda", dtype=dtype):
            yield
    finally:
        setter(prev)
        _log.debug("Restored default dtype → %s", prev)


def scaler(enabled: bool = True) -> _t.Any:
    """
    Return a GradScaler that follows mpolicy's dtype.

    No-op if PyTorch is not available.
    """
    if not TORCH_AVAILABLE:
        _log.warning("scaler called but PyTorch is not available")
        return None

    return torch.cuda.amp.GradScaler(enabled=enabled)