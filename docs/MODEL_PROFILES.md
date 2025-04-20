# Model Profiles for GPU Optimization

The `model_profiles.py` module provides standardized profiles for common ML models, with memory consumption patterns, optimal batch sizes, and layer distribution recommendations for dual-GPU setups.

## Purpose

Model profiles serve several critical functions in the DualGPUOptimizer:

1. **Memory Estimation**: Predict VRAM requirements for different models and configurations
2. **Optimal Split Calculation**: Recommend how to distribute model layers across multiple GPUs
3. **Batch Size Optimization**: Calculate maximum batch sizes based on available VRAM
4. **Framework Support**: Generate optimized parameters for different ML frameworks

## Key Components

### ModelType Enum

Categorizes models by architecture and capability:

```python
class ModelType(Enum):
    DECODER_ONLY = auto()     # Standard LLMs like Llama, Mistral
    ENCODER_DECODER = auto()  # Models with both components like T5, BART
    ENCODER_ONLY = auto()     # Encoder-only models like BERT
    MIXTURE_OF_EXPERTS = auto() # MoE models like Mixtral
```

### QuantizationType Enum

Supported quantization types with their memory reduction factors:

```python
class QuantizationType(Enum):
    NONE = 1.0         # No quantization (FP16/BF16)
    INT8 = 0.5         # Standard 8-bit quantization
    INT4 = 0.25        # 4-bit quantization
    GPTQ = 0.25        # GPTQ quantization (similar to INT4)
    GGUF_Q4_K_M = 0.27 # GGUF Q4_K_M quantization
    GGUF_Q5_K_M = 0.33 # GGUF Q5_K_M quantization
    GGUF_Q8_0 = 0.52   # GGUF Q8_0 quantization
    AWQQUANT = 0.25    # AWQ quantization
```

### ModelMemoryProfile Class

A comprehensive dataclass that encapsulates model architecture and memory characteristics:

```python
@dataclass
class ModelMemoryProfile:
    name: str                       # Human-readable model name
    model_type: ModelType           # Architecture type
    hidden_size: int                # Model's hidden dimension
    num_layers: int                 # Number of layers/blocks
    num_attention_heads: int        # Number of attention heads
    vocab_size: int                 # Vocabulary size
    max_sequence_length: int        # Maximum supported sequence length
    parameter_count: float          # Parameter count in billions
    base_memory: float              # Base memory requirement in GB
    memory_per_token: float         # Memory per token in GB
    kv_cache_per_token: float       # KV cache per token in GB
    # Optional fields with defaults
    quantization: QuantizationType = QuantizationType.NONE
    expert_count: int = 0           # For MoE models
    activated_experts: int = 0      # For sparse MoE models
    sliding_window: Optional[int] = None
    # GPU split recommendations
    gpu_split_recommendations: Dict[str, Tuple[float, float]] = field(default_factory=dict)
```

## Using Model Profiles

### Getting a Model Profile

```python
from dualgpuopt.model_profiles import get_model_profile

# Get profile for a specific model
profile = get_model_profile("llama2-7b")

# With quantization specified
profile_quantized = get_model_profile("llama2-7b", quantization="int4")
```

### Applying Profiles for GPU Optimization

```python
from dualgpuopt.model_profiles import apply_profile

# GPU specs: mapping of GPU IDs to VRAM in GB
gpu_specs = {"0": 24.0, "1": 12.0}

# Apply profile to get optimized settings
result = apply_profile("llama2-13b", gpu_specs, quantization="q4_k_m")

# Results include:
# - memory_required: Total memory needed by the model
# - max_batch_size: Recommended batch size
# - split_ratio: Optimal GPU split ratio
# - device_map: Layer distribution across GPUs
```

## Supported Models

The module includes built-in profiles for these models:

| Model | Parameters | Hidden Size | Layers | Attention Heads | KV Heads |
|-------|------------|-------------|--------|-----------------|----------|
| Llama-2 7B | 7B | 4096 | 32 | 32 | 32 |
| Llama-2 13B | 13B | 5120 | 40 | 40 | 40 |
| Llama-2 70B | 70B | 8192 | 80 | 64 | 8 |
| Mistral 7B | 7B | 4096 | 32 | 32 | 8 |
| Mixtral 8x7B | 46.7B | 4096 | 32 | 32 | 8 |

## Memory Estimation

The `estimate_total_memory` method provides accurate VRAM usage estimates based on:

- Base model memory (model weights)
- Activation memory (varies with batch size and sequence length)
- KV cache memory (critical for long sequences)
- MoE overhead (for Mixture-of-Experts models)

## Extending with New Models

To add support for a new model, add an entry to the `MODEL_PROFILES` dictionary:

```python
MODEL_PROFILES["new-model-7b"] = ModelMemoryProfile(
    name="New Model 7B",
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
        "24+8": (0.75, 0.25)
    }
)
``` 