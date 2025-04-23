import os
import sys
from unittest.mock import patch

# Import the memory predictor module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from dualgpuopt.memory.predictor import MemoryProfile


class TestMemoryPredictor:
    """Test cases for memory prediction functionality."""

    def test_base_memory_calculation(self):
        """Test basic memory calculation for a model."""
        # Test parameters
        model_size_gb = 7
        context_length = 4096
        batch_size = 1

        # Create a memory profile for the test
        profile = MemoryProfile(
            name="TestModel",
            base_usage=model_size_gb * 1024 * 1024 * 1024,  # Convert GB to bytes
            per_batch_usage=100 * 1024 * 1024,  # 100MB per batch item
            per_token_usage=2 * 1024 * 1024,  # 2MB per token
            growth_rate=1.05,
            recovery_buffer=0.85,
        )

        # Call the method under test
        memory_required = profile.estimate_usage(batch_size, context_length)

        # Basic verification - expected to be larger than model size due to overhead
        assert memory_required > model_size_gb * 1024 * 1024 * 1024
        # Should include model size plus KV cache
        expected_min = model_size_gb * 1024 * 1024 * 1024 * 1.1  # At least 10% overhead
        assert memory_required >= expected_min

    def test_context_length_impact(self):
        """Test how context length affects memory requirements."""
        # Create a memory profile for the test
        profile = MemoryProfile(
            name="TestModel",
            base_usage=7 * 1024 * 1024 * 1024,  # 7GB base model
            per_batch_usage=100 * 1024 * 1024,  # 100MB per batch item
            per_token_usage=2 * 1024 * 1024,  # 2MB per token
            growth_rate=1.05,
            recovery_buffer=0.85,
        )

        # Base calculation
        base_memory = profile.estimate_usage(batch_size=1, token_count=2048)

        # Double context length
        double_ctx_memory = profile.estimate_usage(batch_size=1, token_count=4096)

        # Memory should increase with context length (KV cache grows)
        assert double_ctx_memory > base_memory
        # Simple linear relationship expected for KV cache portion
        # Model weights stay constant, but KV cache roughly doubles
        kv_cache_base = base_memory - (7 * 1024 * 1024 * 1024)
        kv_cache_double = double_ctx_memory - (7 * 1024 * 1024 * 1024)
        assert kv_cache_double > 1.8 * kv_cache_base  # Allow some variation in overhead

    def test_batch_size_impact(self):
        """Test how batch size affects memory requirements."""
        # Create a memory profile for the test
        profile = MemoryProfile(
            name="TestModel",
            base_usage=7 * 1024 * 1024 * 1024,  # 7GB base model
            per_batch_usage=100 * 1024 * 1024,  # 100MB per batch item
            per_token_usage=2 * 1024 * 1024,  # 2MB per token
            growth_rate=1.05,
            recovery_buffer=0.85,
        )

        # Base calculation
        base_memory = profile.estimate_usage(batch_size=1, token_count=2048)

        # Double batch size
        double_batch_memory = profile.estimate_usage(batch_size=2, token_count=2048)

        # Memory should increase with batch size (more activations)
        assert double_batch_memory > base_memory
        # Memory increase should be proportional to batch size increase
        # for the activation portion (not the model weights)
        activations_base = base_memory - (7 * 1024 * 1024 * 1024)
        activations_double = double_batch_memory - (7 * 1024 * 1024 * 1024)
        # Should be roughly proportional to batch size increase
        assert activations_double > 1.8 * activations_base

    def test_with_kv_cache_scaling_factor(self):
        """Test with custom KV cache scaling factor."""
        # Set custom KV cache factor through environment
        with patch.dict(os.environ, {"DUALGPUOPT_KV_CACHE_FACTOR": "3.0"}):
            # Base calculation with default factor
            base_memory = MemoryProfile(
                name="TestModel",
                base_usage=7 * 1024 * 1024 * 1024,  # 7GB base model
                per_batch_usage=100 * 1024 * 1024,  # 100MB per batch item
                per_token_usage=2 * 1024 * 1024,  # 2MB per token
                growth_rate=1.05,
                recovery_buffer=0.85,
            ).estimate_usage(batch_size=1, token_count=2048)

            # Calculation with increased factor
            custom_memory = MemoryProfile(
                name="TestModel",
                base_usage=7 * 1024 * 1024 * 1024,  # 7GB base model
                per_batch_usage=100 * 1024 * 1024,  # 100MB per batch item
                per_token_usage=2 * 1024 * 1024,  # 2MB per token
                growth_rate=1.05,
                recovery_buffer=0.85,
            ).estimate_usage(batch_size=1, token_count=2048, kv_cache_factor=3.0)

            # Memory should be higher with larger KV cache factor
            assert custom_memory > base_memory

    def test_model_size_scaling(self):
        """Test linear scaling with model size."""
        # Small model
        small_model_memory = MemoryProfile(
            name="TestModel",
            base_usage=7 * 1024 * 1024 * 1024,  # 7GB base model
            per_batch_usage=100 * 1024 * 1024,  # 100MB per batch item
            per_token_usage=2 * 1024 * 1024,  # 2MB per token
            growth_rate=1.05,
            recovery_buffer=0.85,
        ).estimate_usage(batch_size=1, token_count=2048)

        # Double model size
        large_model_memory = MemoryProfile(
            name="TestModel",
            base_usage=14 * 1024 * 1024 * 1024,  # 14GB base model
            per_batch_usage=100 * 1024 * 1024,  # 100MB per batch item
            per_token_usage=2 * 1024 * 1024,  # 2MB per token
            growth_rate=1.05,
            recovery_buffer=0.85,
        ).estimate_usage(batch_size=1, token_count=2048)

        # Memory should roughly double (not exactly due to KV cache scaling)
        # But should be at least 1.8x and less than 2.2x
        ratio = large_model_memory / small_model_memory
        assert 1.8 <= ratio <= 2.2
