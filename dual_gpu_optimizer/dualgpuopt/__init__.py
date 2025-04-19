"""DualGPUOptimizer - Optimize LLM workloads across multiple GPUs."""

from dualgpuopt.gui import run_app

__all__ = [
    "run_app",
    "get_logger",
    "ctx_size",
    "layer_balance",
    "mpolicy",
    "batch",
]

# Convenience imports
from dualgpuopt.log import get as get_logger
from dualgpuopt import ctx_size, layer_balance, mpolicy, batch 