"""
GPU command generation for llama.cpp and vLLM
"""
from __future__ import annotations
import logging
from typing import Dict, List, Optional, Union

logger = logging.getLogger("DualGPUOpt.Commands")

def generate_llama_cpp_cmd(
    model_path: str,
    gpu_split: List[float] = None,
    ctx_size: int = 4096,
    n_gpu_layers: int = -1,
    threads: int = 8,
    additional_args: str = ""
) -> str:
    """
    Generate command line for llama.cpp

    Args:
        model_path: Path to the model file
        gpu_split: List of GPU split ratios
        ctx_size: Context size in tokens
        n_gpu_layers: Number of layers to offload to GPU (-1 for all)
        threads: Number of threads to use
        additional_args: Additional command line arguments

    Returns:
        Command string for llama.cpp
    """
    cmd = f"./llama.cpp -m {model_path} -c {ctx_size} -t {threads}"

    # Add GPU layers
    cmd += f" --gpu-layers {n_gpu_layers}"

    # Add tensor split if provided
    if gpu_split and len(gpu_split) > 1:
        split_str = ",".join(f"{ratio:.2f}" for ratio in gpu_split)
        cmd += f" --tensor-split {split_str}"

    # Add additional arguments
    if additional_args:
        cmd += f" {additional_args}"

    logger.info(f"Generated llama.cpp command: {cmd}")
    return cmd

def generate_vllm_cmd(
    model_path: str,
    tensor_parallel_size: int = 2,
    max_model_len: Optional[int] = None,
    gpu_memory_utilization: float = 0.9,
    quantization: Optional[str] = None
) -> str:
    """
    Generate command line for vLLM

    Args:
        model_path: Path to the model
        tensor_parallel_size: Number of GPUs to use (typically 2)
        max_model_len: Maximum context length
        gpu_memory_utilization: GPU memory utilization (0.0-1.0)
        quantization: Quantization mode (e.g., "awq", "sq", None)

    Returns:
        Command string for vLLM
    """
    cmd = f"python -m vllm.entrypoints.openai.api_server --model {model_path}"

    # Add tensor parallelism
    cmd += f" --tensor-parallel-size {tensor_parallel_size}"

    # Add model length if provided
    if max_model_len:
        cmd += f" --max-model-len {max_model_len}"

    # Add memory utilization
    cmd += f" --gpu-memory-utilization {gpu_memory_utilization:.1f}"

    # Add quantization if provided
    if quantization:
        cmd += f" --quantization {quantization}"

    logger.info(f"Generated vLLM command: {cmd}")
    return cmd

def generate_env_vars(use_tensor_parallel: bool = True) -> Dict[str, str]:
    """
    Generate environment variables for optimal performance

    Args:
        use_tensor_parallel: Whether tensor parallelism is being used

    Returns:
        Dictionary of environment variables
    """
    env_vars = {
        "CUDA_DEVICE_MAX_CONNECTIONS": "1",  # Limit connections for better tensor parallel perf
        "NCCL_P2P_DISABLE": "1" if use_tensor_parallel else "0",  # Disable P2P for TP
        "CUDA_VISIBLE_DEVICES": "0,1"  # Use both GPUs
    }

    return env_vars