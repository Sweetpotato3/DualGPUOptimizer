"""
GPU-specific command generation for model execution.
"""
from __future__ import annotations

import pathlib
import logging
from typing import Dict, List, Optional

from dualgpuopt.gpu_info import GPU
from dualgpuopt import optimizer


logger = logging.getLogger("dualgpuopt.commands")


class CommandGenerator:
    """Generates optimized commands for running models on GPUs."""

    def __init__(self, gpus: List[GPU]) -> None:
        """
        Initialize command generator.

        Args:
            gpus: List of GPU objects
        """
        self.gpus = gpus
        self.gpu_split = optimizer.split_string(gpus)
        self.tensor_parallel = len(gpus)

    def generate_llama_cpp_command(self, model_path: str, ctx_size: int) -> str:
        """
        Generate an optimized command for llama.cpp.

        Args:
            model_path: Path to the model file
            ctx_size: Context size

        Returns:
            Command string for llama.cpp
        """
        return optimizer.llama_command(model_path, ctx_size, self.gpu_split)

    def generate_vllm_command(self, model_path: str) -> str:
        """
        Generate an optimized command for vLLM.

        Args:
            model_path: Path to the model file

        Returns:
            Command string for vLLM
        """
        return optimizer.vllm_command(model_path, self.tensor_parallel)

    def generate_env_file(self, output_path: Optional[pathlib.Path] = None) -> pathlib.Path:
        """
        Generate an environment file with optimal settings.

        Args:
            output_path: Path to save the environment file

        Returns:
            Path to the created file
        """
        if output_path is None:
            output_path = pathlib.Path.home() / ".env"
        return optimizer.make_env_file(self.gpus, output_path)

    def generate_all(self, model_path: str, ctx_size: int) -> Dict[str, str]:
        """
        Generate all commands and environment file.

        Args:
            model_path: Path to the model file
            ctx_size: Context size

        Returns:
            Dictionary with all generated commands and paths
        """
        llama_cmd = self.generate_llama_cpp_command(model_path, ctx_size)
        vllm_cmd = self.generate_vllm_command(model_path)
        env_path = self.generate_env_file()

        return {
            "llama_cpp": llama_cmd,
            "vllm": vllm_cmd,
            "env_file": str(env_path),
            "gpu_split": self.gpu_split
        }


def generate_commands(gpus: List[GPU], model_path: str, ctx_size: int) -> Dict[str, str]:
    """
    Convenience function to generate all commands in one call.

    Args:
        gpus: List of GPU objects
        model_path: Path to the model file
        ctx_size: Context size

    Returns:
        Dictionary with all generated commands and paths
    """
    generator = CommandGenerator(gpus)
    return generator.generate_all(model_path, ctx_size)