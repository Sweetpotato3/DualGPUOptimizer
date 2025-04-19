"""
Optimizer module for dual GPU setups
Calculates optimal memory splits and context sizes for LLM inference
"""
from typing import Dict, List, Optional, Tuple, Set, Any
import math
import logging
from dataclasses import dataclass
from enum import Enum

# Import our core functionality
from . import gpu_info
from . import ctx_size
from .commands.gpu_commands import generate_llama_cpp_cmd, generate_vllm_cmd

# Initialize logger
logger = logging.getLogger("DualGPUOpt.Optimizer")


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
        return ", ".join([f"{mem // 1024}GB" if mem > 1024 else f"{mem}MB" for mem in self.memory_per_gpu])


class Optimizer:
    """Optimizer class for dual GPU configurations
    
    Performs memory split calculations and context size optimization for LLM inference
    """
    
    def __init__(self):
        """Initialize optimizer"""
        # Memory overhead for various operations
        self.memory_overhead = {
            "system": 2 * 1024,  # 2 GB for system overhead
            "kv_cache_factor": 2.0,  # Multiplier for KV cache estimation
            "tensor_split_overhead": 0.2,  # 20% overhead for tensor parallelism
            "safety_margin": 0.1,  # 10% safety margin
        }
    
    def get_gpu_info(self) -> List[GPUMemoryInfo]:
        """Get current GPU memory information
        
        Returns:
            List of GPUMemoryInfo objects for available GPUs
        """
        try:
            gpu_data = gpu_info.query()
            gpu_info_list = []
            
            for gpu in gpu_data:
                gpu_info_list.append(GPUMemoryInfo(
                    gpu_id=gpu["id"],
                    name=gpu["name"],
                    total_memory=gpu["mem_total"],
                    available_memory=gpu["mem_total"] - gpu["mem_used"],
                    is_primary=gpu["id"] == 0
                ))
            
            return gpu_info_list
        except Exception as e:
            logger.warning(f"Failed to get GPU info: {e}")
            # Return mock data
            return [
                GPUMemoryInfo(
                    gpu_id=0,
                    name="NVIDIA GeForce RTX 5070 Ti (MOCK)",
                    total_memory=24 * 1024,  # 24 GB
                    available_memory=22 * 1024,  # 22 GB
                    is_primary=True
                ),
                GPUMemoryInfo(
                    gpu_id=1,
                    name="NVIDIA GeForce RTX 4060 (MOCK)",
                    total_memory=12 * 1024,  # 12 GB
                    available_memory=11 * 1024,  # 11 GB
                    is_primary=False
                )
            ]
    
    def calculate_per_token_memory(self, model: ModelParameters) -> float:
        """Calculate memory required per token for KV cache
        
        Args:
            model: Model parameters
            
        Returns:
            Memory required per token in MB
        """
        # Calculate bytes needed for one token's key and value states across all layers
        bytes_per_token = (
            # Key states + Value states
            model.kv_hidden_size * 
            # For all layers
            model.num_layers * 
            # Size of float16
            2
        )
        
        # Convert to MB and apply overhead factor
        mb_per_token = (bytes_per_token / (1024 * 1024)) * self.memory_overhead["kv_cache_factor"]
        
        return mb_per_token
    
    def calculate_max_context(self, 
                             model: ModelParameters, 
                             available_memory: int,
                             tensor_parallel_size: int = 1) -> Tuple[int, int]:
        """Calculate maximum and recommended context length
        
        Args:
            model: Model parameters
            available_memory: Available GPU memory in MB
            tensor_parallel_size: Number of GPUs to split tensors across
            
        Returns:
            Tuple of (max_context_length, recommended_context_length)
        """
        # Account for tensor parallelism
        effective_memory = available_memory
        if tensor_parallel_size > 1:
            # When using tensor parallelism, there's some overhead
            effective_memory = available_memory * (1 - self.memory_overhead["tensor_split_overhead"])
        
        # Calculate memory per token
        memory_per_token = self.calculate_per_token_memory(model)
        
        # Calculate maximum context length
        max_context = int(effective_memory / memory_per_token)
        
        # Apply safety margin for recommended context
        recommended_context = int(max_context * (1 - self.memory_overhead["safety_margin"]))
        
        # Clamp to model's context window
        max_context = min(max_context, model.context_length)
        recommended_context = min(recommended_context, model.context_length)
        
        # Round to nearest 128
        recommended_context = (recommended_context // 128) * 128
        
        return max_context, recommended_context
    
    def optimize_gpu_split(self, 
                           model: ModelParameters,
                           gpus: Optional[List[GPUMemoryInfo]] = None) -> SplitConfiguration:
        """Calculate optimal GPU split configuration
        
        Args:
            model: Model parameters
            gpus: List of GPU info (will query if not provided)
            
        Returns:
            SplitConfiguration with optimal settings
        """
        if gpus is None:
            gpus = self.get_gpu_info()
        
        if len(gpus) < 2:
            # If only one GPU, no split needed
            max_context, recommended_context = self.calculate_max_context(
                model, gpus[0].available_memory
            )
            
            return SplitConfiguration(
                tensor_parallel_size=1,
                gpu_split=[1.0],
                memory_per_gpu=[gpus[0].available_memory],
                max_context_length=max_context,
                recommended_context_length=recommended_context
            )
        
        # For dual GPU, calculate optimal split based on available memory
        total_memory = sum(gpu.available_memory for gpu in gpus)
        
        # Calculate split ratios proportional to available memory
        split_ratios = [gpu.available_memory / total_memory for gpu in gpus]
        
        # Calculate memory allocation per GPU
        memory_per_gpu = [int(ratio * total_memory) for ratio in split_ratios]
        
        # Calculate context length based on combined memory
        max_context, recommended_context = self.calculate_max_context(
            model, total_memory, tensor_parallel_size=len(gpus)
        )
        
        return SplitConfiguration(
            tensor_parallel_size=len(gpus),
            gpu_split=split_ratios,
            memory_per_gpu=memory_per_gpu,
            max_context_length=max_context,
            recommended_context_length=recommended_context
        )
    
    def generate_llama_cpp_args(self, config: SplitConfiguration, model_path: str = "") -> str:
        """Generate llama.cpp command line arguments for the split configuration
        
        Args:
            config: Split configuration
            model_path: Optional model path to include
            
        Returns:
            Command line arguments for llama.cpp
        """
        # Format the split configuration for llama.cpp
        return generate_llama_cpp_cmd(
            model_path=model_path if model_path else "<model_path>", 
            gpu_split=config.gpu_split,
            ctx_size=config.recommended_context_length
        )
    
    def generate_vllm_args(self, config: SplitConfiguration, model_path: str = "") -> str:
        """Generate vLLM command line arguments for the split configuration
        
        Args:
            config: Split configuration
            model_path: Optional model path to include
            
        Returns:
            Command line arguments for vLLM
        """
        return generate_vllm_cmd(
            model_path=model_path if model_path else "<model_path>",
            tensor_parallel_size=config.tensor_parallel_size,
            max_model_len=config.recommended_context_length
        )


# Singleton instance for global access
_optimizer: Optional[Optimizer] = None


def get_optimizer() -> Optimizer:
    """Get the global optimizer instance
    
    Returns:
        The global optimizer instance, creating it if needed
    """
    global _optimizer
    if _optimizer is None:
        _optimizer = Optimizer()
    return _optimizer 