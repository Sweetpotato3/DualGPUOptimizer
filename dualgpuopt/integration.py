"""
Integration code to connect the Optimizer to the UI
"""
from __future__ import annotations
import logging
from typing import Optional

# Initialize logger
logger = logging.getLogger("DualGPUOpt.Integration")

class OptimizerIntegration:
    """
    Integration class to connect the optimizer with the UI
    This serves as a bridge between the optimizer and the UI components
    """

    def __init__(self):
        """Initialize the integration"""
        self.model_path = ""
        self.tensor_parallel_size = 2  # Default to 2 GPUs
        self.llama_cmd = ""
        self.vllm_cmd = ""
        self.has_valid_config = False

    def update_model_path(self, path: str) -> None:
        """
        Update the model path

        Args:
            path: Path to the model file
        """
        self.model_path = path
        logger.info(f"Model path updated: {path}")
        self._update_commands()

    def update_commands(self, llama_cmd: str, vllm_cmd: str) -> None:
        """
        Update command strings

        Args:
            llama_cmd: llama.cpp command
            vllm_cmd: vLLM command
        """
        self.llama_cmd = llama_cmd
        self.vllm_cmd = vllm_cmd
        self.has_valid_config = bool(llama_cmd and vllm_cmd)
        logger.info("Commands updated")

    def _update_commands(self) -> None:
        """
        Refresh commands with the current model path
        """
        if self.model_path and self.llama_cmd and "<model_path>" in self.llama_cmd:
            self.llama_cmd = self.llama_cmd.replace("<model_path>", self.model_path)

        if self.model_path and self.vllm_cmd and "<model_path>" in self.vllm_cmd:
            self.vllm_cmd = self.vllm_cmd.replace("<model_path>", self.model_path)

    def get_llama_command(self) -> str:
        """
        Get the current llama.cpp command

        Returns:
            Command string for llama.cpp
        """
        return self.llama_cmd

    def get_vllm_command(self) -> str:
        """
        Get the current vLLM command

        Returns:
            Command string for vLLM
        """
        return self.vllm_cmd

    def is_config_valid(self) -> bool:
        """
        Check if the current configuration is valid

        Returns:
            True if the configuration is valid
        """
        return self.has_valid_config

# Singleton instance
_optimizer_integration: Optional[OptimizerIntegration] = None

def get_optimizer_integration() -> OptimizerIntegration:
    """
    Get the optimizer integration singleton instance

    Returns:
        OptimizerIntegration instance
    """
    global _optimizer_integration
    if _optimizer_integration is None:
        _optimizer_integration = OptimizerIntegration()
    return _optimizer_integration