"""
Context size calculator for large language models
Provides functions to calculate optimal context sizes based on GPU memory
"""
import logging
from typing import Tuple, Optional

logger = logging.getLogger("DualGPUOpt.CtxSize")

# Constants for different models
KV_OVERHEAD_FACTOR = 2  # KV cache overhead factor
MQA_FACTOR = 0.25  # Multi-query attention reduction factor
GQA_FACTOR = 0.5  # Grouped-query attention reduction factor

def calc_max_ctx(
    gpu_vram_mb: int,
    model_params_b: float,
    kv_heads: int = None,
    heads: int = None,
    layers: int = None,
    hidden_size: int = None,
    moe_expert_count: int = 1,
    dtype_size: int = 2,  # Default to fp16/bf16
    safety_margin: float = 0.9,
) -> int:
    """Calculate maximum context size based on GPU memory and model parameters

    Args:
        gpu_vram_mb: Available GPU VRAM in MB
        model_params_b: Model size in billions of parameters
        kv_heads: Number of KV heads (for MQA/GQA models)
        heads: Total number of attention heads
        layers: Number of transformer layers
        hidden_size: Model's hidden dimension size
        moe_expert_count: Number of experts for MoE models (default: 1 for non-MoE)
        dtype_size: Size of data type in bytes (default: 2 for fp16/bf16)
        safety_margin: Safety margin to prevent OOM (0.0-1.0)

    Returns:
        Maximum context size
    """
    try:
        # Convert GPU VRAM to bytes
        gpu_vram_bytes = gpu_vram_mb * 1024 * 1024

        # Apply safety margin
        gpu_vram_bytes *= safety_margin

        # If we have detailed model architecture, use precise calculation
        if all([kv_heads, heads, layers, hidden_size]):
            # Calculate attention type factor (MQA, GQA, or standard)
            if kv_heads == 1:
                attn_factor = MQA_FACTOR  # MQA
            elif kv_heads < heads:
                attn_factor = GQA_FACTOR  # GQA
            else:
                attn_factor = 1.0  # Standard attention

            # Calculate bytes per token in KV cache
            bytes_per_token = (
                KV_OVERHEAD_FACTOR *  # KV cache overhead
                layers *  # Number of layers
                kv_heads *  # Number of KV heads
                (hidden_size // heads) *  # Head dimension
                dtype_size *  # Size of data type in bytes
                moe_expert_count *  # Expert count for MoE models
                attn_factor  # Attention type factor (MQA/GQA/standard)
            )

            # Maximum context size calculation
            max_ctx = int(gpu_vram_bytes / bytes_per_token)

        else:
            # Fallback to simplified heuristic based on model size
            # Approximation: 2.5 bytes per token per billion params at context 4K
            base_ctx = 4096
            approx_bytes_per_token_per_b = 2.5 * 1024 * 1024  # 2.5 MB per token per billion params

            # Estimate max context based on available memory and model size
            max_ctx = int((gpu_vram_bytes / (model_params_b * approx_bytes_per_token_per_b)) * base_ctx)

        # Clamp to reasonable values (minimum 256, maximum 128K)
        max_ctx = max(256, min(max_ctx, 131072))

        # Round to nearest power of 2 or multiple of 128 for efficiency
        if max_ctx >= 4096:
            # Round to nearest power of 2 for large contexts
            power = 2 ** (max_ctx.bit_length() - 1)
            if max_ctx - power < power * 2 - max_ctx:
                max_ctx = power
            else:
                max_ctx = power * 2
        else:
            # Round to nearest multiple of 128 for small contexts
            max_ctx = (max_ctx // 128) * 128

        logger.info(f"Calculated max context: {max_ctx} tokens for {model_params_b}B model on {gpu_vram_mb}MB GPU")
        return max_ctx

    except Exception as e:
        logger.error(f"Error calculating max context size: {e}")
        # Return a conservative default if calculation fails
        return 2048

def model_params_from_name(model_name: str) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[int], Optional[float]]:
    """Extract model parameters from a model name

    Args:
        model_name: Name of the model, can include path

    Returns:
        Tuple of (layers, heads, kv_heads, hidden_size, moe_factor)
    """
    # Default values
    layers = None
    heads = None
    kv_heads = None
    hidden_size = None
    moe_factor = 1.0

    # Extract base name from path
    import os
    basename = os.path.basename(model_name).lower()

    # Common model patterns
    model_configs = {
        "llama-2-7b": (32, 32, 32, 4096, 1.0),
        "llama-2-13b": (40, 40, 40, 5120, 1.0),
        "llama-2-70b": (80, 64, 8, 8192, 1.0),  # GQA
        "llama-3-8b": (32, 32, 8, 4096, 1.0),   # GQA
        "llama-3-70b": (80, 64, 8, 8192, 1.0),  # GQA
        "mistral-7b": (32, 32, 8, 4096, 1.0),   # GQA
        "mixtral-8x7b": (32, 32, 8, 4096, 1.5), # MoE
        "phi-2": (32, 32, 32, 2560, 1.0),
        "qwen": (32, 32, 32, 4096, 1.0),
    }

    # Try to match the model name with known configurations
    for key, config in model_configs.items():
        if key in basename:
            layers, heads, kv_heads, hidden_size, moe_factor = config
            logger.info(f"Found model parameters for {key}: {config}")
            return layers, heads, kv_heads, hidden_size, moe_factor

    # Special case for detecting model size from name if not matched above
    for size_marker in ["7b", "13b", "70b", "8b"]:
        if size_marker in basename:
            if "70b" in basename:
                return 80, 64, 8, 8192, 1.0  # Large model with GQA
            elif "13b" in basename:
                return 40, 40, 40, 5120, 1.0  # Medium model
            elif "8x7b" in basename or "mixtral" in basename:
                return 32, 32, 8, 4096, 1.5   # MoE model
            else:  # 7b or 8b
                return 32, 32, 8, 4096, 1.0   # Small model with GQA

    # If no match found, log warning and return None values
    logger.warning(f"Unable to determine model parameters from name: {model_name}")
    return layers, heads, kv_heads, hidden_size, moe_factor

def estimate_vram_usage(
    context_size: int,
    model_params_b: float,
    batch_size: int = 1
) -> float:
    """Estimate VRAM usage for a given context size and model

    Args:
        context_size: Context size in tokens
        model_params_b: Model size in billions of parameters
        batch_size: Batch size for inference

    Returns:
        Estimated VRAM usage in MB
    """
    try:
        # Base model memory (simplified estimation)
        base_model_mb = model_params_b * 1024  # ~1GB per billion parameters when optimized

        # KV cache memory
        # Roughly: 2 bytes per token per billion parameters for context tracking
        kv_cache_mb = (context_size * model_params_b * 2) * batch_size

        # Additional overhead for activations, buffers, etc. (roughly 20%)
        overhead_mb = (base_model_mb + kv_cache_mb) * 0.2

        total_mb = base_model_mb + kv_cache_mb + overhead_mb

        return total_mb
    except Exception as e:
        logger.error(f"Error estimating VRAM usage: {e}")
        # Return a conservative estimate if calculation fails
        return model_params_b * 1024 * 2  # 2x model size as fallback