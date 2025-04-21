"""
Pluggable batching heuristics.
"""
from __future__ import annotations
import typing as _t

class BucketPolicy(_t.Protocol):
    """Return bucket ID for a given sequence length."""
    def __call__(self, seq_len: int) -> int: ...

def pow2_bucket(step: int = 32) -> BucketPolicy:  # noqa: D401
    """power‑of‑two bucketing (default llama.cpp style)."""
    def _inner(l: int) -> int:
        return step if l <= step else 1 << (l - 1).bit_length()
    return _inner

def token_ratio_bucket(ratio: float = 1.5) -> BucketPolicy:
    """
    Keep bucket sizes within *ratio* of each other:
    eg. ratio 1.5 groups 128‑192, 192‑288, etc.
    """
    def _inner(l: int) -> int:
        base = 32
        while l > base * ratio:
            base *= 2
        return base
    return _inner