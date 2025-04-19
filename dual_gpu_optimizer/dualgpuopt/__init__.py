"""DualGPUOptimizer - Optimize LLM workloads across multiple GPUs."""

# Version information
VERSION = "0.2.0"

# Define __all__ first
__all__ = [
    "VERSION",
    "run_app",
    "get_logger",
    "ctx_size",
    "layer_balance",
    "mpolicy",
    "batch",
]

# Delay these imports to avoid circular imports
def _setup_imports():
    """Import modules on demand to avoid circular imports."""
    global run_app, get_logger, ctx_size, layer_balance, mpolicy, batch
    
    # Convenience imports
    from dualgpuopt.log import get as get_logger
    from dualgpuopt import ctx_size, layer_balance, mpolicy, batch
    
    try:
        # This can be imported later to avoid circular imports
        from dualgpuopt.gui import run_app
    except ImportError:
        # Define a fallback if GUI module not available
        def run_app():
            """Fallback implementation for run_app."""
            print("GUI module not available")
            return None 