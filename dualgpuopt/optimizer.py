"""
Optimizer module for dual GPU setups
Calculates optimal memory splits and context sizes for LLM inference
"""
import functools
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Import our core functionality
from . import gpu_info
from .commands.gpu_commands import generate_llama_cpp_cmd, generate_vllm_cmd

# Initialize logger
logger = logging.getLogger("DualGPUOpt.Optimizer")

# Environment variable configuration
ENV_SYSTEM_OVERHEAD = int(os.environ.get("DUALGPUOPT_SYSTEM_OVERHEAD", "2048"))  # 2GB default
ENV_SAFETY_MARGIN = float(os.environ.get("DUALGPUOPT_SAFETY_MARGIN", "0.1"))  # 10% default
ENV_TP_OVERHEAD = float(os.environ.get("DUALGPUOPT_TP_OVERHEAD", "0.2"))  # 20% default
ENV_KV_CACHE_FACTOR = float(os.environ.get("DUALGPUOPT_KV_CACHE_FACTOR", "2.0"))  # 2.0x default
ENV_MIN_CONTEXT = int(os.environ.get("DUALGPUOPT_MIN_CONTEXT", "128"))  # 128 tokens minimum
ENV_OPT_CACHE_TIMEOUT = int(
    os.environ.get("DUALGPUOPT_OPT_CACHE_TIMEOUT", "30")
)  # 30 seconds cache timeout

# Try to import numpy for vectorized operations
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.info("NumPy not available, using standard Python for calculations")

# Import error handling if available
try:
    from dualgpuopt.error_handler import ErrorCategory, ErrorSeverity, handle_exceptions

    error_handler_available = True
except ImportError:
    error_handler_available = False
    logger.warning("Error handler not available for optimizer, using basic error handling")


class MemoryUnit(Enum):
    """Memory size units"""

    MB = 1
    GB = 1024


@dataclass
class ModelParameters:
    """Parameters defining a large language model"""

    name: str
    context_length: int
    hidden_size: int
    num_layers: int
    num_heads: int
    kv_heads: Optional[int] = None

    @property
    def kv_head_count(self) -> int:
        """Get the number of KV heads, defaulting to num_heads if not specified"""
        return self.kv_heads if self.kv_heads is not None else self.num_heads

    @property
    def head_size(self) -> int:
        """Calculate the size of each attention head"""
        return self.hidden_size // self.num_heads

    @property
    def kv_hidden_size(self) -> int:
        """Calculate the effective hidden size for KV attention heads"""
        return self.kv_head_count * self.head_size * 2  # Both K and V

    def __hash__(self):
        """Make ModelParameters hashable for caching"""
        return hash(
            (
                self.name,
                self.context_length,
                self.hidden_size,
                self.num_layers,
                self.num_heads,
                self.kv_heads if self.kv_heads is not None else -1,
            )
        )


@dataclass
class GPUMemoryInfo:
    """Information about GPU memory availability and capabilities"""

    gpu_id: int
    name: str
    total_memory: int  # in MB
    available_memory: int  # in MB
    is_primary: bool = False

    @property
    def formatted_total(self) -> str:
        """Get formatted total memory string"""
        if self.total_memory > 1024:
            return f"{self.total_memory / 1024:.1f} GB"
        return f"{self.total_memory} MB"

    @property
    def formatted_available(self) -> str:
        """Get formatted available memory string"""
        if self.available_memory > 1024:
            return f"{self.available_memory / 1024:.1f} GB"
        return f"{self.available_memory} MB"

    def __hash__(self):
        """Make GPUMemoryInfo hashable for caching"""
        return hash(
            (self.gpu_id, self.name, self.total_memory, self.available_memory, self.is_primary)
        )


@dataclass
class SplitConfiguration:
    """Configuration for GPU split parameters"""

    tensor_parallel_size: int
    gpu_split: List[float]  # Ratios for each GPU
    memory_per_gpu: List[int]  # Actual memory in MB per GPU
    max_context_length: int
    recommended_context_length: int

    @property
    def formatted_split(self) -> str:
        """Returns formatted GPU split ratios as string"""
        return ", ".join([f"{ratio:.2f}" for ratio in self.gpu_split])

    @property
    def formatted_memory(self) -> str:
        """Returns formatted memory allocation as string"""
        return ", ".join(
            [f"{mem // 1024}GB" if mem > 1024 else f"{mem}MB" for mem in self.memory_per_gpu]
        )


class Optimizer:
    """
    Optimizer class for dual GPU configurations

    Performs memory split calculations and context size optimization for LLM inference
    """

    def __init__(self):
        """Initialize optimizer"""
        # Memory overhead for various operations - configurable via environment variables
        self.memory_overhead = {
            "system": ENV_SYSTEM_OVERHEAD,  # System overhead in MB
            "kv_cache_factor": ENV_KV_CACHE_FACTOR,  # Multiplier for KV cache estimation
            "tensor_split_overhead": ENV_TP_OVERHEAD,  # Overhead for tensor parallelism
            "safety_margin": ENV_SAFETY_MARGIN,  # Safety margin
        }

        # Default fallback values for when GPU info is unavailable
        self.fallback_gpus = [
            GPUMemoryInfo(
                gpu_id=0,
                name="NVIDIA GeForce RTX (FALLBACK)",
                total_memory=24 * 1024,  # 24 GB
                available_memory=20 * 1024,  # 20 GB
                is_primary=True,
            ),
            GPUMemoryInfo(
                gpu_id=1,
                name="NVIDIA GeForce RTX (FALLBACK)",
                total_memory=16 * 1024,  # 16 GB
                available_memory=14 * 1024,  # 14 GB
                is_primary=False,
            ),
        ]

        # Cache for optimization results
        self._memory_cache = {}
        self._context_cache = {}
        self._split_cache = {}
        self._last_gpu_info_time = 0
        self._cached_gpu_info = None
        self._cache_timeout = ENV_OPT_CACHE_TIMEOUT

    def get_gpu_info(self) -> List[GPUMemoryInfo]:
        """
        Get current GPU memory information

        Returns
        -------
            List of GPUMemoryInfo objects for available GPUs

        """
        # Check if we have a recent cache
        current_time = time.time()
        if self._cached_gpu_info and (
            current_time - self._last_gpu_info_time < self._cache_timeout
        ):
            logger.debug("Using cached GPU info")
            return self._cached_gpu_info

        try:
            gpu_data = gpu_info.query()

            # Validate we got data back
            if not gpu_data:
                logger.warning("No GPU data returned from query, using fallback values")
                return self.fallback_gpus

            gpu_info_list = []

            for gpu in gpu_data:
                # Validate the GPU data has required fields
                if not all(key in gpu for key in ["id", "name", "mem_total", "mem_used"]):
                    logger.warning(f"Invalid GPU data format: {gpu}, skipping")
                    continue

                # Validate reasonable memory values (prevent negative/zero values)
                mem_total = max(1024, gpu["mem_total"])  # Minimum 1GB
                mem_used = min(gpu["mem_used"], mem_total)  # Cannot exceed total
                available_memory = max(1024, mem_total - mem_used)  # Minimum 1GB available

                gpu_info_list.append(
                    GPUMemoryInfo(
                        gpu_id=gpu["id"],
                        name=gpu["name"],
                        total_memory=mem_total,
                        available_memory=available_memory,
                        is_primary=gpu["id"] == 0,
                    )
                )

            # If we got no valid GPUs, use fallback
            if not gpu_info_list:
                logger.warning("No valid GPUs found, using fallback values")
                return self.fallback_gpus

            # Update cache
            self._cached_gpu_info = gpu_info_list
            self._last_gpu_info_time = current_time

            return gpu_info_list
        except Exception as e:
            logger.error(f"Failed to get GPU info: {e}")
            # Return fallback data
            return self.fallback_gpus

    def calculate_per_token_memory(self, model: ModelParameters) -> float:
        """
        Calculate memory required per token for KV cache

        Args:
        ----
            model: Model parameters

        Returns:
        -------
            Memory required per token in MB

        """
        # Check cache first
        cache_key = hash(model)
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        try:
            # Calculate bytes needed for one token's key and value states across all layers
            bytes_per_token = (
                # Key states + Value states
                model.kv_hidden_size
                *
                # For all layers
                model.num_layers
                *
                # Size of float16
                2
            )

            # Convert to MB and apply overhead factor
            mb_per_token = (bytes_per_token / (1024 * 1024)) * self.memory_overhead[
                "kv_cache_factor"
            ]

            # Safety bounds - ensure reasonable values
            mb_per_token = max(0.01, min(10.0, mb_per_token))

            # Store in cache
            self._memory_cache[cache_key] = mb_per_token

            return mb_per_token
        except Exception as e:
            logger.error(f"Error calculating per-token memory: {e}")
            # Fallback to a reasonable default (approximately what a 7B model needs)
            return 0.12

    def calculate_max_context(
        self, model: ModelParameters, available_memory: int, tensor_parallel_size: int = 1
    ) -> Tuple[int, int]:
        """
        Calculate maximum and recommended context length

        Args:
        ----
            model: Model parameters
            available_memory: Available GPU memory in MB
            tensor_parallel_size: Number of GPUs to split tensors across

        Returns:
        -------
            Tuple of (max_context_length, recommended_context_length)

        """
        # Check cache first
        cache_key = (hash(model), available_memory, tensor_parallel_size)
        if cache_key in self._context_cache:
            return self._context_cache[cache_key]

        try:
            # Account for tensor parallelism
            effective_memory = available_memory
            if tensor_parallel_size > 1:
                # When using tensor parallelism, there's some overhead
                effective_memory = available_memory * (
                    1 - self.memory_overhead["tensor_split_overhead"]
                )

            # Calculate memory per token
            memory_per_token = self.calculate_per_token_memory(model)

            # Safety check - ensure memory_per_token is positive
            if memory_per_token <= 0:
                logger.warning("Invalid memory_per_token value, using fallback")
                memory_per_token = 0.12  # Default fallback

            # Calculate maximum context length with reasonable bounds
            max_context = int(effective_memory / memory_per_token)
            max_context = max(ENV_MIN_CONTEXT, min(model.context_length, max_context))

            # Apply safety margin for recommended context
            recommended_context = int(max_context * (1 - self.memory_overhead["safety_margin"]))
            recommended_context = max(
                ENV_MIN_CONTEXT, min(recommended_context, model.context_length)
            )

            # Round to nearest 128
            recommended_context = (recommended_context // 128) * 128
            recommended_context = max(recommended_context, ENV_MIN_CONTEXT)

            # Final sanity check - ensure max_context is valid
            max_context = max(recommended_context, max_context)

            # Store in cache
            self._context_cache[cache_key] = (max_context, recommended_context)

            return max_context, recommended_context
        except Exception as e:
            logger.error(f"Error calculating context length: {e}")
            # Return reasonable defaults
            return model.context_length, min(2048, model.context_length)

    def optimize_gpu_split(
        self, model: ModelParameters, gpus: Optional[List[GPUMemoryInfo]] = None
    ) -> SplitConfiguration:
        """
        Calculate optimal GPU split configuration

        Args:
        ----
            model: Model parameters
            gpus: List of GPU info (will query if not provided)

        Returns:
        -------
            SplitConfiguration with optimal settings

        """
        try:
            if gpus is None:
                gpus = self.get_gpu_info()

            # Check cache if we have a valid configuration
            gpu_tuple = tuple(hash(gpu) for gpu in gpus)
            cache_key = (hash(model), gpu_tuple)
            if cache_key in self._split_cache:
                return self._split_cache[cache_key]

            # Ensure we have at least one GPU
            if not gpus:
                logger.error("No GPUs available for optimization")
                # Create a minimal configuration with defaults
                return SplitConfiguration(
                    tensor_parallel_size=1,
                    gpu_split=[1.0],
                    memory_per_gpu=[16 * 1024],  # 16GB default
                    max_context_length=model.context_length,
                    recommended_context_length=min(2048, model.context_length),
                )

            if len(gpus) < 2:
                # If only one GPU, no split needed
                max_context, recommended_context = self.calculate_max_context(
                    model,
                    gpus[0].available_memory,
                )

                config = SplitConfiguration(
                    tensor_parallel_size=1,
                    gpu_split=[1.0],
                    memory_per_gpu=[gpus[0].available_memory],
                    max_context_length=max_context,
                    recommended_context_length=recommended_context,
                )

                self._split_cache[cache_key] = config
                return config

            # For dual GPU, calculate optimal split based on available memory
            # Ensure memory values are reasonable
            valid_gpus = [gpu for gpu in gpus if gpu.available_memory > 0]
            if not valid_gpus:
                logger.warning("No GPUs with available memory, using fallback values")
                valid_gpus = self.fallback_gpus

            # Use vectorized calculations if NumPy is available
            if NUMPY_AVAILABLE and len(valid_gpus) > 1:
                # Convert to arrays for faster calculation
                available_memory = np.array([gpu.available_memory for gpu in valid_gpus])
                total_memory = np.sum(available_memory)

                # Calculate split ratios proportional to available memory
                split_ratios = available_memory / total_memory

                # Calculate memory allocation per GPU
                memory_per_gpu = (split_ratios * total_memory).astype(int).tolist()
                split_ratios = split_ratios.tolist()
            else:
                # Standard calculation without NumPy
                total_memory = sum(gpu.available_memory for gpu in valid_gpus)

                # Calculate split ratios proportional to available memory
                split_ratios = [gpu.available_memory / total_memory for gpu in valid_gpus]

                # Calculate memory allocation per GPU
                memory_per_gpu = [int(ratio * total_memory) for ratio in split_ratios]

            # Calculate context length based on combined memory
            max_context, recommended_context = self.calculate_max_context(
                model,
                total_memory,
                tensor_parallel_size=len(valid_gpus),
            )

            config = SplitConfiguration(
                tensor_parallel_size=len(valid_gpus),
                gpu_split=split_ratios,
                memory_per_gpu=memory_per_gpu,
                max_context_length=max_context,
                recommended_context_length=recommended_context,
            )

            # Store in cache
            self._split_cache[cache_key] = config

            return config
        except Exception as e:
            logger.error(f"Error optimizing GPU split: {e}")
            # Return a safe default configuration
            return SplitConfiguration(
                tensor_parallel_size=2,
                gpu_split=[0.6, 0.4],  # Default 60/40 split
                memory_per_gpu=[12 * 1024, 8 * 1024],  # 12GB/8GB default
                max_context_length=model.context_length,
                recommended_context_length=min(2048, model.context_length),
            )

    def clear_caches(self) -> None:
        """Clear all optimization caches"""
        self._memory_cache.clear()
        self._context_cache.clear()
        self._split_cache.clear()
        self._cached_gpu_info = None
        logger.debug("Cleared optimizer caches")

    def generate_llama_cpp_args(self, config: SplitConfiguration, model_path: str = "") -> str:
        """
        Generate llama.cpp command line arguments for the split configuration

        Args:
        ----
            config: Split configuration
            model_path: Optional model path to include

        Returns:
        -------
            Command line arguments for llama.cpp

        """
        try:
            # Format the split configuration for llama.cpp
            return generate_llama_cpp_cmd(
                model_path=model_path if model_path else "<model_path>",
                gpu_split=config.gpu_split,
                ctx_size=config.recommended_context_length,
            )
        except Exception as e:
            logger.error(f"Error generating llama.cpp arguments: {e}")
            # Return a basic fallback command
            split_str = (
                ",".join([f"{split:.2f}" for split in config.gpu_split])
                if config.gpu_split
                else "0.6,0.4"
            )
            return f"--model {model_path if model_path else '<model_path>'} --ctx-size {config.recommended_context_length} --gpu-layers -1 --split-mode 2 --tensor-split {split_str}"

    def generate_vllm_args(self, config: SplitConfiguration, model_path: str = "") -> str:
        """
        Generate vLLM command line arguments for the split configuration

        Args:
        ----
            config: Split configuration
            model_path: Optional model path to include

        Returns:
        -------
            Command line arguments for vLLM

        """
        try:
            return generate_vllm_cmd(
                model_path=model_path if model_path else "<model_path>",
                tensor_parallel_size=config.tensor_parallel_size,
                max_model_len=config.recommended_context_length,
            )
        except Exception as e:
            logger.error(f"Error generating vLLM arguments: {e}")
            # Return a basic fallback command
            return f"--model {model_path if model_path else '<model_path>'} --tensor-parallel-size {config.tensor_parallel_size} --max-model-len {config.recommended_context_length}"


# Apply error handling decorator if available
def _apply_error_handler(
    component="Optimizer", severity=ErrorSeverity.ERROR if error_handler_available else None
):
    """Apply error handler decorator if available"""

    def decorator(func):
        if error_handler_available:
            return handle_exceptions(component=component, severity=severity, reraise=False)(func)
        # Simple error handling if dedicated error handler isn't available
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                # Return appropriate default values
                if func.__name__ == "calculate_gpu_split":
                    return {"error": str(e), "success": False}
                return None

        return wrapper

    return decorator


# Singleton instance for global access
_optimizer: Optional[Optimizer] = None


def get_optimizer() -> Optimizer:
    """
    Get the global optimizer instance

    Returns
    -------
        The global optimizer instance, creating it if needed

    """
    global _optimizer
    if _optimizer is None:
        _optimizer = Optimizer()
    return _optimizer


def clear_optimizer_caches() -> None:
    """Clear all optimizer caches"""
    optimizer = get_optimizer()
    optimizer.clear_caches()


# Compatibility functions for refactored code
@_apply_error_handler()
def calculate_gpu_split(model_params: Optional[ModelParameters] = None) -> Dict[str, Any]:
    """
    Calculate optimal GPU split for a model (compatibility function)

    Args:
    ----
        model_params: Model parameters, or None to use default parameters

    Returns:
    -------
        Dictionary with split configuration

    """
    optimizer = get_optimizer()

    # Use default parameters if none provided
    if model_params is None:
        model_params = ModelParameters(
            name="Default Model",
            context_length=8192,
            hidden_size=4096,
            num_layers=32,
            num_heads=32,
        )

    # Get GPU info and calculate split
    gpus = optimizer.get_gpu_info()
    config = optimizer.optimize_gpu_split(model_params, gpus)

    # Convert to dictionary format expected by older code
    return {
        "tensor_parallel_size": config.tensor_parallel_size,
        "gpu_split": config.gpu_split,
        "memory_per_gpu": config.memory_per_gpu,
        "max_context": config.max_context_length,
        "recommended_context": config.recommended_context_length,
        "gpus": gpus,
    }


@_apply_error_handler()
def validate_params(params: ModelParameters) -> Tuple[bool, str]:
    """
    Validate model parameters

    Args:
    ----
        params: ModelParameters object

    Returns:
    -------
        Tuple of (is_valid, error_message)

    """
    # Check basic parameters
    if params.hidden_size <= 0:
        return False, "Hidden size must be positive"

    if params.num_layers <= 0:
        return False, "Number of layers must be positive"

    if params.num_heads <= 0:
        return False, "Number of heads must be positive"

    # Check if hidden size is divisible by number of heads
    if params.hidden_size % params.num_heads != 0:
        return (
            False,
            f"Hidden size ({params.hidden_size}) must be divisible by number of heads ({params.num_heads})",
        )

    # Check KV heads if specified
    if params.kv_heads is not None:
        if params.kv_heads <= 0:
            return False, "Number of KV heads must be positive"

        if params.num_heads % params.kv_heads != 0:
            return (
                False,
                f"Number of heads ({params.num_heads}) must be divisible by number of KV heads ({params.kv_heads})",
            )

    # Check context length
    if params.context_length is not None and params.context_length <= 0:
        return False, "Context length must be positive"

    return True, ""
