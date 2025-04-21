"""
Parameter resolver for model launch commands.

This module handles the generation of optimized launch parameters
for different model frameworks and architectures.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any

from dualgpuopt.gpu_info import GPU
from dualgpuopt.optimizer import calculate_gpu_split


class ParameterResolver:
    """Resolves optimal parameters for model launch commands."""

    def __init__(self) -> None:
        """Initialize the parameter resolver."""
        self.logger = logging.getLogger("dualgpuopt.gui.launcher.parameters")

    def resolve_llama_parameters(
        self,
        model_path: str,
        gpus: List[GPU],
        ctx_size: int,
        batch_size: int = 1,
        threads: int = 4
    ) -> Dict[str, Any]:
        """
        Resolve optimal parameters for llama.cpp.

        Args:
            model_path: Path to the model file
            gpus: List of available GPUs
            ctx_size: Context size for model
            batch_size: Batch size for inference
            threads: Number of CPU threads

        Returns:
            Dictionary of resolved parameters
        """
        # This is a placeholder for the actual implementation
        self.logger.debug(f"Resolving llama parameters for {model_path}")

        # Calculate optimal GPU split
        gpu_split = calculate_gpu_split(gpus)
        split_str = ",".join([f"{int(s*100)}" for s in gpu_split])

        return {
            "model_path": model_path,
            "ctx_size": ctx_size,
            "gpu_split": split_str,
            "batch_size": batch_size,
            "threads": threads
        }

    def resolve_vllm_parameters(
        self,
        model_path: str,
        gpus: List[GPU],
        max_memory: Optional[str] = None,
        tensor_parallel_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Resolve optimal parameters for vLLM.

        Args:
            model_path: Path to the model file
            gpus: List of available GPUs
            max_memory: Maximum memory to use
            tensor_parallel_size: Tensor parallel size

        Returns:
            Dictionary of resolved parameters
        """
        # This is a placeholder for the actual implementation
        self.logger.debug(f"Resolving vLLM parameters for {model_path}")

        # Default to using all available GPUs
        if tensor_parallel_size is None:
            tensor_parallel_size = len(gpus)

        return {
            "model_path": model_path,
            "tensor_parallel_size": tensor_parallel_size,
            "max_memory": max_memory or "auto"
        }

    def generate_llama_command(self, parameters: Dict[str, Any]) -> str:
        """
        Generate llama.cpp command line.

        Args:
            parameters: Launch parameters

        Returns:
            Formatted command string
        """
        model_path = parameters["model_path"]
        ctx_size = parameters.get("ctx_size", 2048)
        gpu_split = parameters.get("gpu_split", "100")
        batch_size = parameters.get("batch_size", 1)
        threads = parameters.get("threads", 4)

        return (
            f"./main -m {model_path} "
            f"--ctx-size {ctx_size} "
            f"--gpu-split {gpu_split} "
            f"--batch-size {batch_size} "
            f"--threads {threads}"
        )

    def generate_vllm_command(self, parameters: Dict[str, Any]) -> str:
        """
        Generate vLLM command line.

        Args:
            parameters: Launch parameters

        Returns:
            Formatted command string
        """
        model_path = parameters["model_path"]
        tensor_parallel_size = parameters.get("tensor_parallel_size", 1)
        parameters.get("max_memory", "auto")

        return (
            f"python -m vllm.entrypoints.openai.api_server "
            f"--model {model_path} "
            f"--tensor-parallel-size {tensor_parallel_size} "
            f"--max-model-len 8192"
        )