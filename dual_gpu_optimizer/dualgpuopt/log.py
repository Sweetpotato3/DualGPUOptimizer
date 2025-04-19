"""
Logging bootstrap used by every module.

* INFO‐level by default
* Richer formatting in dev environment
"""
from __future__ import annotations
import logging, os

FMT = "%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s"
logging.basicConfig(
    level=os.getenv("DGP_LOG_LEVEL", "INFO").upper(),
    format=FMT,
    datefmt="%H:%M:%S",
)

def get(name: str) -> logging.Logger:
    """Return package‑scoped logger."""
    return logging.getLogger(f"dualgpuopt.{name}") 