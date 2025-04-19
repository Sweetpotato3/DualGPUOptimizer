"""
Mixed precision policies for accelerated inference and training
Provides utilities for controlling precision of tensor operations
"""
import contextlib
from typing import Any, Optional
import logging

# Initialize logger
logger = logging.getLogger("DualGPUOpt.MixedPrecision")

# Check for PyTorch dependency
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    logger.warning("PyTorch not available - mixed precision operations will be disabled")
    TORCH_AVAILABLE = False


@contextlib.contextmanager
def autocast(dtype: Optional[Any] = None):
    """Context manager for automatic mixed precision
    
    Args:
        dtype: Optional torch data type (defaults to float16 if None)
        
    Notes:
        - LayerNorm, softmax, residual adds remain in FP32 automatically
        - Works with PyTorch 2.0+ for best performance
        - No-op if PyTorch is not available
    """
    if not TORCH_AVAILABLE:
        logger.warning("autocast called but PyTorch is not available")
        yield
        return
    
    # Get the current default dtype
    prev_dtype = torch.get_default_dtype()
    
    # Use setter to change dtype - fallback to _C version if needed
    setter = getattr(torch, "set_default_dtype", 
                    getattr(torch._C, "_set_default_dtype", None))
    
    if setter is None:
        # Can't change dtype, just yield and return
        yield
        return
    
    # Set the requested dtype or default to float16
    if dtype is None:
        dtype = torch.float16
    
    # Change the default dtype
    setter(dtype)
    
    try:
        # Use torch.autocast if available (PyTorch 1.10+)
        with torch.autocast("cuda", dtype=dtype):
            yield
    finally:
        # Restore the previous dtype
        setter(prev_dtype)
        logger.debug(f"Restored default dtype to {prev_dtype}")


def scaler(enabled: bool = True) -> Any:
    """Create a GradScaler for mixed precision training
    
    Args:
        enabled: Whether to enable the scaler
        
    Returns:
        GradScaler object or None if PyTorch not available
        
    Notes:
        - Used during training to prevent underflow in FP16
        - No-op if PyTorch is not available
    """
    if not TORCH_AVAILABLE:
        logger.warning("scaler called but PyTorch is not available")
        return None
    
    return torch.cuda.amp.GradScaler(enabled=enabled) 