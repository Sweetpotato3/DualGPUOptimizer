"""
Model validation logic for DualGPUOptimizer.

This module contains functions for validating model paths and parameters
before launching models.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

from dualgpuopt.gpu_info import GPU


class ModelValidator:
    """Validator for model files and parameters."""
    
    def __init__(self) -> None:
        """Initialize the model validator."""
        self.logger = logging.getLogger("dualgpuopt.gui.launcher.validator")
    
    def validate_model_path(self, model_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a model file path.
        
        Args:
            model_path: Path to the model file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not model_path:
            return False, "Model path cannot be empty"
        
        path = Path(model_path)
        
        if not path.exists():
            return False, f"Model file does not exist: {model_path}"
        
        if not path.is_file():
            return False, f"Model path is not a file: {model_path}"
        
        # Check for common model file extensions
        valid_extensions = [".bin", ".gguf", ".pt", ".ggml", ".safetensors"]
        if path.suffix not in valid_extensions:
            self.logger.warning(f"Model file has unusual extension: {path.suffix}")
            # This is just a warning, not an error
        
        return True, None
    
    def validate_gpu_configuration(self, gpus: List[GPU]) -> Tuple[bool, Optional[str]]:
        """
        Validate GPU configuration for model launch.
        
        Args:
            gpus: List of available GPUs
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not gpus:
            return False, "No GPUs available for model execution"
        
        # Check if any GPU has enough memory (at least 2GB free)
        min_memory_gb = 2
        has_enough_memory = any(gpu.mem_free_gb >= min_memory_gb for gpu in gpus)
        
        if not has_enough_memory:
            return False, f"No GPU has at least {min_memory_gb}GB free memory"
        
        return True, None
    
    def validate_context_size(self, ctx_size: int, gpus: List[GPU]) -> Tuple[bool, Optional[str]]:
        """
        Validate context size against available GPU memory.
        
        Args:
            ctx_size: Context size for model in tokens
            gpus: List of available GPUs
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if ctx_size <= 0:
            return False, "Context size must be greater than 0"
        
        # Rough estimate: each token requires ~8 bytes in 8-bit quantization
        # This is a simplified calculation
        memory_required_gb = (ctx_size * 8) / (1024 * 1024 * 1024)
        total_memory_gb = sum(gpu.mem_free_gb for gpu in gpus)
        
        if memory_required_gb > total_memory_gb:
            return False, f"Context size {ctx_size} requires ~{memory_required_gb:.1f}GB, but only {total_memory_gb:.1f}GB is available"
        
        return True, None
    
    def validate_launch_parameters(
        self, 
        model_path: str, 
        framework: str, 
        parameters: Dict[str, Any],
        gpus: List[GPU]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate all launch parameters.
        
        Args:
            model_path: Path to the model file
            framework: Framework to use (llama.cpp, vllm)
            parameters: Launch parameters
            gpus: List of available GPUs
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate model path
        valid, error = self.validate_model_path(model_path)
        if not valid:
            return False, error
        
        # Validate GPU configuration
        valid, error = self.validate_gpu_configuration(gpus)
        if not valid:
            return False, error
        
        # Framework-specific validation
        if framework == "llama.cpp":
            # Validate context size
            ctx_size = parameters.get("ctx_size", 2048)
            valid, error = self.validate_context_size(ctx_size, gpus)
            if not valid:
                return False, error
        
        elif framework == "vllm":
            # Validate tensor parallel size
            tp_size = parameters.get("tensor_parallel_size", len(gpus))
            if tp_size > len(gpus):
                return False, f"Tensor parallel size {tp_size} exceeds available GPU count {len(gpus)}"
        
        return True, None 