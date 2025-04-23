"""
Property-based tests for the GPU optimizer algorithms using Hypothesis.
Tests the invariants, boundaries, and edge cases of the optimizer functions.
"""

import os
import sys

import pytest
from hypothesis import assume, example, given, settings
from hypothesis import strategies as st

# Add the project root to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dualgpuopt.optimizer import GPUMemoryInfo, ModelParameters, Optimizer


# Create strategies for our test data
@st.composite
def gpu_memory_info_strategy(draw):
    """Strategy to generate valid GPUMemoryInfo objects"""
    gpu_id = draw(st.integers(min_value=0, max_value=7))
    # GPUs typically have memory between 2GB and 80GB
    total_memory = draw(st.integers(min_value=2 * 1024, max_value=80 * 1024))
    # Available memory should be less than total memory
    available_memory = draw(st.integers(min_value=1024, max_value=total_memory))
    is_primary = draw(st.booleans())

    return GPUMemoryInfo(
        gpu_id=gpu_id,
        name=f"NVIDIA Test GPU {gpu_id}",
        total_memory=total_memory,
        available_memory=available_memory,
        is_primary=is_primary,
    )


@st.composite
def gpu_list_strategy(draw):
    """Strategy to generate lists of GPUMemoryInfo objects"""
    # Most systems will have 1-4 GPUs
    num_gpus = draw(st.integers(min_value=1, max_value=4))
    return [draw(gpu_memory_info_strategy()) for _ in range(num_gpus)]


@st.composite
def model_parameters_strategy(draw):
    """Strategy to generate valid ModelParameters objects"""
    # Common model sizes range from small (1B) to large (70B+)
    num_layers = draw(st.integers(min_value=8, max_value=80))
    hidden_size = draw(st.integers(min_value=768, max_value=8192))
    # Heads are typically a fraction of hidden size
    num_heads = draw(st.integers(min_value=max(1, hidden_size // 128), max_value=hidden_size // 64))
    context_length = draw(st.integers(min_value=1024, max_value=32768))

    return ModelParameters(
        name=f"Test Model {num_layers}L-{hidden_size}H-{num_heads}A",
        num_layers=num_layers,
        hidden_size=hidden_size,
        num_heads=num_heads,
        context_length=context_length,
    )


class TestOptimizerProperties:
    """Property-based tests for the GPU optimizer algorithms."""

    @given(
        model=model_parameters_strategy(),
        gpus=gpu_list_strategy(),
    )
    @settings(max_examples=100, deadline=None)
    def test_split_configuration_sum_to_one(self, model, gpus):
        """Test that GPU split ratios always sum to approximately 1.0"""
        # Skip tests with no GPUs or no available memory
        assume(len(gpus) > 0)
        assume(all(gpu.available_memory > 0 for gpu in gpus))

        optimizer = Optimizer()
        config = optimizer.optimize_gpu_split(model, gpus)

        # Check that splits sum to 1.0 (allowing for floating-point precision)
        assert abs(sum(config.gpu_split) - 1.0) < 1e-10

        # Check that tensor parallel size equals number of GPUs
        assert config.tensor_parallel_size == len(gpus)

        # Check that memory allocations are consistent with split ratios
        for i, ratio in enumerate(config.gpu_split):
            expected_memory = int(ratio * sum(gpu.available_memory for gpu in gpus))
            # Allow some small difference due to integer rounding
            assert abs(config.memory_per_gpu[i] - expected_memory) <= len(gpus)

    @given(
        model=model_parameters_strategy(),
        gpus=gpu_list_strategy(),
    )
    @settings(max_examples=100, deadline=None)
    def test_context_size_within_model_limits(self, model, gpus):
        """Test that calculated context sizes are within model limits"""
        # Skip tests with no GPUs or no available memory
        assume(len(gpus) > 0)
        assume(all(gpu.available_memory > 0 for gpu in gpus))

        optimizer = Optimizer()
        config = optimizer.optimize_gpu_split(model, gpus)

        # Max context should never exceed model's max context length
        assert config.max_context_length <= model.context_length

        # Recommended context should be at most the max context
        assert config.recommended_context_length <= config.max_context_length

        # Recommended context should be at least the minimum context (defined in ENV_MIN_CONTEXT)
        assert config.recommended_context_length >= 128  # Assuming ENV_MIN_CONTEXT is 128

    @given(
        model=model_parameters_strategy(),
        available_memory=st.integers(min_value=1024, max_value=80 * 1024),
    )
    @settings(max_examples=100, deadline=None)
    def test_max_context_monotonicity(self, model, available_memory):
        """Test that max context increases monotonically with available memory"""
        optimizer = Optimizer()

        # Calculate context with original memory
        max_context1, _ = optimizer.calculate_max_context(model, available_memory)

        # Calculate context with more memory
        more_memory = available_memory + 1024  # Add 1GB
        max_context2, _ = optimizer.calculate_max_context(model, more_memory)

        # Context should be larger or equal with more memory
        assert max_context2 >= max_context1

    @given(
        model=model_parameters_strategy(),
        gpus=st.lists(gpu_memory_info_strategy(), min_size=2, max_size=2),
    )
    @settings(max_examples=100, deadline=None)
    @example(
        model=ModelParameters(
            name="Test", num_layers=32, hidden_size=4096, num_heads=32, context_length=8192
        ),
        gpus=[
            GPUMemoryInfo(
                gpu_id=0,
                name="GPU 0",
                total_memory=24 * 1024,
                available_memory=20 * 1024,
                is_primary=True,
            ),
            GPUMemoryInfo(
                gpu_id=1,
                name="GPU 1",
                total_memory=8 * 1024,
                available_memory=6 * 1024,
                is_primary=False,
            ),
        ],
    )
    def test_split_proportional_to_available_memory(self, model, gpus):
        """Test that GPU splits are proportional to available memory"""
        # Skip if any GPU has zero available memory
        assume(all(gpu.available_memory > 0 for gpu in gpus))

        optimizer = Optimizer()
        config = optimizer.optimize_gpu_split(model, gpus)

        # Split ratios should be proportional to available memory
        total_memory = sum(gpu.available_memory for gpu in gpus)
        expected_ratios = [gpu.available_memory / total_memory for gpu in gpus]

        # Check that each split is within a small epsilon of the expected ratio
        for actual, expected in zip(config.gpu_split, expected_ratios):
            assert abs(actual - expected) < 0.01

    @given(model=model_parameters_strategy())
    @settings(max_examples=100, deadline=None)
    def test_single_gpu_optimization(self, model):
        """Test optimization with a single GPU"""
        # Create a single GPU
        gpu = GPUMemoryInfo(
            gpu_id=0,
            name="NVIDIA Test GPU 0",
            total_memory=24 * 1024,  # 24GB
            available_memory=20 * 1024,  # 20GB
            is_primary=True,
        )

        optimizer = Optimizer()
        config = optimizer.optimize_gpu_split(model, [gpu])

        # For single GPU, tensor parallel size should be 1
        assert config.tensor_parallel_size == 1

        # Single GPU should have 100% of the split
        assert len(config.gpu_split) == 1
        assert config.gpu_split[0] == 1.0

        # Memory per GPU should match available memory
        assert len(config.memory_per_gpu) == 1
        assert config.memory_per_gpu[0] == gpu.available_memory

    @given(
        model=model_parameters_strategy(),
        gpus=gpu_list_strategy(),
    )
    @settings(max_examples=50, deadline=None)
    def test_cache_consistency(self, model, gpus):
        """Test that cached results are consistent"""
        # Skip tests with no GPUs or no available memory
        assume(len(gpus) > 0)
        assume(all(gpu.available_memory > 0 for gpu in gpus))

        optimizer = Optimizer()

        # Call optimize twice with the same parameters
        config1 = optimizer.optimize_gpu_split(model, gpus)
        config2 = optimizer.optimize_gpu_split(model, gpus)

        # Results should be identical (object equality due to caching)
        assert config1 is config2

        # Clear cache and calculate again
        optimizer.clear_caches()
        config3 = optimizer.optimize_gpu_split(model, gpus)

        # Should be different object but same values
        assert config1 is not config3
        assert config1.gpu_split == config3.gpu_split
        assert config1.memory_per_gpu == config3.memory_per_gpu
        assert config1.max_context_length == config3.max_context_length
        assert config1.recommended_context_length == config3.recommended_context_length


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
