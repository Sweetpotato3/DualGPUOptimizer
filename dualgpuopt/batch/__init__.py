"""
Batch processing module for optimizing inference workloads.
"""

# Re-export key components
try:
    from .smart_batch import optimize_batch_size

    __all__ = ["optimize_batch_size"]
except ImportError:
    __all__ = []
