"""
GPU command generation for llama.cpp and vLLM
"""
from __future__ import annotations
import logging
from typing import Dict, List

logger = logging.getLogger("DualGPUOpt.Commands")

# Import resource manager if available
try:
    from dualgpuopt.services.resource_manager import ResourceManager
    resource_manager_available = True
    logger.debug("Resource manager available for command generation")
except ImportError:
    resource_manager_available = False
    logger.warning("Resource manager not available for command generation")

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
    # Use resource manager to offload command generation to CPU if available
    if resource_manager_available:
        resource_manager = ResourceManager.get_instance()
        if resource_manager.should_use_cpu("command_generation"):
            return resource_manager.run_on_cpu(
                _cpu_generate_llama_cmd,
                model_path,
                gpu_split,
                ctx_size,
                n_gpu_layers,
                threads,
                additional_args
            )

    # Default generation method
    return _cpu_generate_llama_cmd(
        model_path,
        gpu_split,
        ctx_size,
        n_gpu_layers,
        threads,
        additional_args
    )

def _cpu_generate_llama_cmd(
    model_path: str,
    gpu_split: List[float] = None,
    ctx_size: int = 4096,
    n_gpu_layers: int = -1,
    threads: int = 8,
    additional_args: str = ""
) -> str:
    """
    CPU-optimized implementation for generating llama.cpp command

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
    tensor_parallel: int = 2,
    max_tokens: int = 4096,
    additional_args: str = ""
) -> str:
    """
    Generate command line for vLLM

    Args:
        model_path: Path to the model file or HuggingFace model name
        tensor_parallel: Number of GPUs for tensor parallelism
        max_tokens: Maximum number of tokens (context size)
        additional_args: Additional command line arguments

    Returns:
        Command string for vLLM
    """
    # Use resource manager to offload command generation to CPU if available
    if resource_manager_available:
        resource_manager = ResourceManager.get_instance()
        if resource_manager.should_use_cpu("command_generation"):
            return resource_manager.run_on_cpu(
                _cpu_generate_vllm_cmd,
                model_path,
                tensor_parallel,
                max_tokens,
                additional_args
            )

    # Default generation method
    return _cpu_generate_vllm_cmd(
        model_path,
        tensor_parallel,
        max_tokens,
        additional_args
    )

def _cpu_generate_vllm_cmd(
    model_path: str,
    tensor_parallel: int = 2,
    max_tokens: int = 4096,
    additional_args: str = ""
) -> str:
    """
    CPU-optimized implementation for generating vLLM command

    Args:
        model_path: Path to the model file or HuggingFace model name
        tensor_parallel: Number of GPUs for tensor parallelism
        max_tokens: Maximum number of tokens (context size)
        additional_args: Additional command line arguments

    Returns:
        Command string for vLLM
    """
    cmd = f"python -m vllm.entrypoints.openai.api_server --model {model_path}"
    cmd += f" --tensor-parallel-size {tensor_parallel} --max-model-len {max_tokens}"

    # Add additional arguments
    if additional_args:
        cmd += f" {additional_args}"

    logger.info(f"Generated vLLM command: {cmd}")
    return cmd

def generate_env_vars(
    gpu_split: List[float] = None,
    ctx_size: int = 4096,
    format_type: str = "shell"
) -> Dict[str, str]:
    """
    Generate environment variables for GPU optimization

    Args:
        gpu_split: List of GPU split ratios
        ctx_size: Context size in tokens
        format_type: Format type (shell, json, etc.)

    Returns:
        Dictionary of environment variables
    """
    # Use resource manager to offload env vars generation to CPU if available
    if resource_manager_available:
        resource_manager = ResourceManager.get_instance()
        if resource_manager.should_use_cpu("command_generation"):
            return resource_manager.run_on_cpu(
                _cpu_generate_env_vars,
                gpu_split,
                ctx_size,
                format_type
            )

    # Default generation method
    return _cpu_generate_env_vars(
        gpu_split,
        ctx_size,
        format_type
    )

def _cpu_generate_env_vars(
    gpu_split: List[float] = None,
    ctx_size: int = 4096,
    format_type: str = "shell"
) -> Dict[str, str]:
    """
    CPU-optimized implementation for generating environment variables

    Args:
        gpu_split: List of GPU split ratios
        ctx_size: Context size in tokens
        format_type: Format type (shell, json, etc.)

    Returns:
        Dictionary of environment variables
    """
    env_vars = {
        "DUALGPUOPT_CONTEXT_SIZE": str(ctx_size),
        "CUDA_VISIBLE_DEVICES": "0,1" if gpu_split and len(gpu_split) > 1 else "0",
        "NCCL_P2P_DISABLE": "1",  # Disable NCCL P2P for better performance
        "CUDA_DEVICE_MAX_CONNECTIONS": "1"  # Better memory allocation
    }

    # Add GPU split if provided
    if gpu_split and len(gpu_split) > 1:
        split_str = ",".join(f"{ratio:.2f}" for ratio in gpu_split)
        env_vars["DUALGPUOPT_GPU_SPLIT"] = split_str

    logger.info(f"Generated environment variables: {env_vars}")
    return env_vars