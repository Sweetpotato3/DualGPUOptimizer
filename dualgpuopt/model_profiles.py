"""
Model profiles for GPU memory consumption estimation and optimization.

This module provides standardized profiles for common ML models, with memory 
consumption patterns, optimal batch sizes, and layer distribution recommendations
for dual-GPU setups.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Union
import math


class ModelType(Enum):
    """Categorizes models by architecture and capability."""
    DECODER_ONLY = auto()
    ENCODER_DECODER = auto()
    ENCODER_ONLY = auto()
    MIXTURE_OF_EXPERTS = auto()


class QuantizationType(Enum):
    """Supported quantization types with their memory reduction factors."""
    NONE = 1.0         # No quantization (FP16/BF16)
    INT8 = 0.5         # Standard 8-bit quantization
    INT4 = 0.25        # 4-bit quantization
    GPTQ = 0.25        # GPTQ quantization (similar to INT4)
    GGUF_Q4_K_M = 0.27 # GGUF Q4_K_M quantization
    GGUF_Q5_K_M = 0.33 # GGUF Q5_K_M quantization
    GGUF_Q8_0 = 0.52   # GGUF Q8_0 quantization
    AWQQUANT = 0.25    # AWQ quantization


@dataclass
class ModelMemoryProfile:
    """Memory profile for a specific model architecture."""
    name: str
    model_type: ModelType
    
    # Base parameters
    hidden_size: int
    num_layers: int
    num_attention_heads: int
    vocab_size: int
    max_sequence_length: int
    parameter_count: float  # in billions
    
    # Memory estimates in GB
    base_memory: float
    memory_per_token: float
    kv_cache_per_token: float
    
    # Optional fields with defaults
    quantization: QuantizationType = QuantizationType.NONE
    expert_count: int = 0  # For MoE models
    activated_experts: int = 0  # For sparse MoE models
    sliding_window: Optional[int] = None
    
    # Optimal GPU split recommendations for different VRAM configurations
    gpu_split_recommendations: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate derived properties after initialization."""
        # If not explicitly set, estimate these values
        if not self.base_memory:
            # Roughly estimate base model memory (weights + optimizer states)
            self.base_memory = self.parameter_count * (2.0 / self.quantization.value)
            
        if not self.memory_per_token:
            # Rough estimate of memory per token
            self.memory_per_token = (self.hidden_size * 12) / (1024 * 1024 * 1024)
            
        if not self.kv_cache_per_token:
            # Estimate KV cache size per token
            head_dim = self.hidden_size // self.num_attention_heads
            kv_elements = 2 * self.max_sequence_length * self.num_attention_heads * head_dim * self.num_layers
            self.kv_cache_per_token = (kv_elements * 2) / (1024 * 1024 * 1024)  # 2 bytes for FP16
    
    def estimate_total_memory(self, batch_size: int, sequence_length: int) -> float:
        """
        Estimate total GPU memory required for a specific batch and sequence length.
        
        Args:
            batch_size: Number of sequences to process in parallel
            sequence_length: Length of each sequence in tokens
            
        Returns:
            Estimated memory requirement in GB
        """
        # Base model memory (weights)
        total_memory = self.base_memory
        
        # Memory for activations
        activation_memory = batch_size * sequence_length * self.memory_per_token
        
        # KV cache memory
        kv_memory = 0.0
        if self.model_type in [ModelType.DECODER_ONLY, ModelType.ENCODER_DECODER]:
            effective_seq_len = sequence_length
            if self.sliding_window and sequence_length > self.sliding_window:
                effective_seq_len = self.sliding_window
            kv_memory = batch_size * effective_seq_len * self.kv_cache_per_token
        
        # Add extra memory for MoE models
        moe_factor = 1.0
        if self.model_type == ModelType.MIXTURE_OF_EXPERTS and self.expert_count > 0:
            # For MoE models, we need more memory for experts
            if self.activated_experts > 0:
                moe_factor = 1.0 + (self.activated_experts / self.expert_count)
            else:
                moe_factor = 1.2  # Default assumption: 20% overhead for MoE
            
        return (total_memory + activation_memory + kv_memory) * moe_factor
    
    def calculate_max_batch_size(self, available_memory: float, sequence_length: int) -> int:
        """
        Calculate maximum batch size given available memory and sequence length.
        
        Args:
            available_memory: Available GPU memory in GB
            sequence_length: Sequence length in tokens
            
        Returns:
            Maximum batch size
        """
        # Reserve memory for model weights and some overhead
        remaining_memory = available_memory - self.base_memory - 0.5  # 0.5GB for overhead
        
        if remaining_memory <= 0:
            return 0
        
        # Calculate memory needed per sequence
        memory_per_sequence = sequence_length * self.memory_per_token
        
        # Add KV cache if applicable
        if self.model_type in [ModelType.DECODER_ONLY, ModelType.ENCODER_DECODER]:
            effective_seq_len = sequence_length
            if self.sliding_window and sequence_length > self.sliding_window:
                effective_seq_len = self.sliding_window
            memory_per_sequence += effective_seq_len * self.kv_cache_per_token
        
        # Account for MoE overhead
        if self.model_type == ModelType.MIXTURE_OF_EXPERTS and self.expert_count > 0:
            if self.activated_experts > 0:
                memory_per_sequence *= 1.0 + (self.activated_experts / self.expert_count)
            else:
                memory_per_sequence *= 1.2  # Default MoE overhead
        
        # Calculate max batch size and round down
        max_batch = int(remaining_memory / memory_per_sequence)
        return max(1, max_batch)  # Ensure at least batch size 1
    
    def recommend_gpu_split(self, vram_gb_primary: float, vram_gb_secondary: float) -> Tuple[float, float]:
        """
        Recommend how to split model between two GPUs based on their VRAM.
        
        Args:
            vram_gb_primary: Primary GPU VRAM in GB
            vram_gb_secondary: Secondary GPU VRAM in GB
            
        Returns:
            Tuple of (primary_gpu_percentage, secondary_gpu_percentage)
        """
        vram_key = f"{int(vram_gb_primary)}+{int(vram_gb_secondary)}"
        
        # If we have a pre-computed recommendation, use it
        if vram_key in self.gpu_split_recommendations:
            return self.gpu_split_recommendations[vram_key]
        
        # Otherwise, calculate based on relative VRAM sizes
        total_vram = vram_gb_primary + vram_gb_secondary
        primary_pct = vram_gb_primary / total_vram
        secondary_pct = vram_gb_secondary / total_vram
        
        # Adjust for minimum requirements - each GPU needs at least 20% of the model
        if primary_pct < 0.2:
            primary_pct = 0.2
            secondary_pct = 0.8
        elif secondary_pct < 0.2:
            primary_pct = 0.8
            secondary_pct = 0.2
            
        return (primary_pct, secondary_pct)


# Common model profiles
MODEL_PROFILES: Dict[str, ModelMemoryProfile] = {
    # Llama 2 models
    "llama2-7b": ModelMemoryProfile(
        name="Llama-2 7B",
        model_type=ModelType.DECODER_ONLY,
        hidden_size=4096,
        num_layers=32,
        num_attention_heads=32,
        vocab_size=32000,
        max_sequence_length=4096,
        parameter_count=7.0,
        base_memory=14.0,
        memory_per_token=0.000043,
        kv_cache_per_token=0.000016,
        gpu_split_recommendations={
            "8+8": (0.5, 0.5),
            "12+8": (0.6, 0.4),
            "16+8": (0.7, 0.3),
            "24+8": (0.75, 0.25)
        }
    ),
    
    "llama2-13b": ModelMemoryProfile(
        name="Llama-2 13B",
        model_type=ModelType.DECODER_ONLY,
        hidden_size=5120,
        num_layers=40,
        num_attention_heads=40,
        vocab_size=32000,
        max_sequence_length=4096,
        parameter_count=13.0,
        base_memory=26.0,
        memory_per_token=0.000067,
        kv_cache_per_token=0.000025,
        gpu_split_recommendations={
            "12+12": (0.5, 0.5),
            "16+8": (0.7, 0.3),
            "24+8": (0.75, 0.25),
            "24+16": (0.6, 0.4)
        }
    ),
    
    "llama2-70b": ModelMemoryProfile(
        name="Llama-2 70B",
        model_type=ModelType.DECODER_ONLY,
        hidden_size=8192,
        num_layers=80,
        num_attention_heads=64,
        vocab_size=32000,
        max_sequence_length=4096,
        parameter_count=70.0,
        base_memory=140.0,
        memory_per_token=0.00016,
        kv_cache_per_token=0.000064,
        gpu_split_recommendations={
            "24+24": (0.5, 0.5),
            "48+24": (0.66, 0.34),
            "80+24": (0.75, 0.25)
        }
    ),
    
    # Mixtral models
    "mixtral-8x7b": ModelMemoryProfile(
        name="Mixtral 8x7B",
        model_type=ModelType.MIXTURE_OF_EXPERTS,
        hidden_size=4096,
        num_layers=32,
        num_attention_heads=32,
        vocab_size=32000,
        max_sequence_length=32768,
        parameter_count=46.7,  # Effective params, total is ~85B
        base_memory=94.0,
        memory_per_token=0.000047,
        kv_cache_per_token=0.000016,
        expert_count=8,
        activated_experts=2,
        gpu_split_recommendations={
            "24+24": (0.5, 0.5),
            "48+24": (0.66, 0.34),
            "80+48": (0.65, 0.35)
        }
    ),
    
    # Mistral models
    "mistral-7b": ModelMemoryProfile(
        name="Mistral 7B",
        model_type=ModelType.DECODER_ONLY,
        hidden_size=4096,
        num_layers=32,
        num_attention_heads=32,
        vocab_size=32000,
        max_sequence_length=32768,
        parameter_count=7.0,
        base_memory=14.0,
        memory_per_token=0.000043,
        kv_cache_per_token=0.000016,
        sliding_window=4096,
        gpu_split_recommendations={
            "8+8": (0.5, 0.5),
            "12+8": (0.6, 0.4),
            "16+8": (0.7, 0.3),
            "24+8": (0.75, 0.25)
        }
    ),
}


def get_model_profile(model_name: str, quantization: Optional[str] = None) -> ModelMemoryProfile:
    """
    Get a model profile by name, optionally with specific quantization.
    
    Args:
        model_name: Base model name (e.g., "llama2-7b")
        quantization: Optional quantization type (e.g., "int8", "int4", "q4_k_m")
        
    Returns:
        ModelMemoryProfile with adjusted memory requirements based on quantization
    """
    # Standardize model name format
    model_name = model_name.lower().replace(" ", "").replace("_", "").replace("-", "")
    
    # Try to match with our known profiles
    profile = None
    for key, prof in MODEL_PROFILES.items():
        if model_name in key.lower().replace("-", "").replace("_", ""):
            profile = prof
            break
    
    if not profile:
        # Handle unknown models with best-guess estimates
        if "7b" in model_name:
            profile = MODEL_PROFILES["llama2-7b"]
        elif "13b" in model_name:
            profile = MODEL_PROFILES["llama2-13b"]
        elif "70b" in model_name:
            profile = MODEL_PROFILES["llama2-70b"]
        elif "mixtral" in model_name:
            profile = MODEL_PROFILES["mixtral-8x7b"]
        else:
            # Default to 7B profile if we can't determine
            profile = MODEL_PROFILES["llama2-7b"]
    
    # Create a copy of the profile to modify for quantization
    result = ModelMemoryProfile(
        name=profile.name,
        model_type=profile.model_type,
        hidden_size=profile.hidden_size,
        num_layers=profile.num_layers,
        num_attention_heads=profile.num_attention_heads,
        vocab_size=profile.vocab_size,
        max_sequence_length=profile.max_sequence_length,
        parameter_count=profile.parameter_count,
        base_memory=profile.base_memory,
        memory_per_token=profile.memory_per_token,
        kv_cache_per_token=profile.kv_cache_per_token,
        expert_count=profile.expert_count,
        activated_experts=profile.activated_experts,
        sliding_window=profile.sliding_window,
        gpu_split_recommendations=profile.gpu_split_recommendations.copy()
    )
    
    # Apply quantization if specified
    if quantization:
        quant_type = None
        if quantization.lower() in ("int8", "8bit"):
            quant_type = QuantizationType.INT8
        elif quantization.lower() in ("int4", "4bit", "gptq"):
            quant_type = QuantizationType.INT4
        elif quantization.lower() in ("q4_k_m", "q4k", "q4"):
            quant_type = QuantizationType.GGUF_Q4_K_M
        elif quantization.lower() in ("q5_k_m", "q5k", "q5"):
            quant_type = QuantizationType.GGUF_Q5_K_M
        elif quantization.lower() in ("q8_0", "q8"):
            quant_type = QuantizationType.GGUF_Q8_0
        elif quantization.lower() in ("awq"):
            quant_type = QuantizationType.AWQQUANT
            
        if quant_type:
            result.quantization = quant_type
            # Adjust base memory according to quantization factor
            result.base_memory = profile.base_memory * quant_type.value
    
    return result 