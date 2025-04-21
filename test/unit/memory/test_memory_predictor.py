from unittest.mock import patch
import sys
import os

# Import the memory predictor module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from dualgpuopt.memory.predictor import predict_memory_requirements

class TestMemoryPredictor:
    """Test cases for memory prediction functionality."""

    def test_base_memory_calculation(self):
        """Test basic memory calculation for a model."""
        # Test parameters
        model_size_gb = 7
        context_length = 4096
        batch_size = 1

        # Call the function under test
        memory_required = predict_memory_requirements(
            model_size_gb=model_size_gb,
            context_length=context_length,
            batch_size=batch_size
        )

        # Basic verification - expected to be larger than model size due to overhead
        assert memory_required > model_size_gb * 1024 * 1024 * 1024
        # Should include model size plus KV cache
        expected_min = model_size_gb * 1024 * 1024 * 1024 * 1.1  # At least 10% overhead
        assert memory_required >= expected_min

    def test_context_length_impact(self):
        """Test how context length affects memory requirements."""
        # Base calculation
        base_memory = predict_memory_requirements(
            model_size_gb=7,
            context_length=2048,
            batch_size=1
        )

        # Double context length
        double_ctx_memory = predict_memory_requirements(
            model_size_gb=7,
            context_length=4096,
            batch_size=1
        )

        # Memory should increase with context length (KV cache grows)
        assert double_ctx_memory > base_memory
        # Simple linear relationship expected for KV cache portion
        # Model weights stay constant, but KV cache roughly doubles
        kv_cache_base = base_memory - (7 * 1024 * 1024 * 1024)
        kv_cache_double = double_ctx_memory - (7 * 1024 * 1024 * 1024)
        assert kv_cache_double > 1.8 * kv_cache_base  # Allow some variation in overhead

    def test_batch_size_impact(self):
        """Test how batch size affects memory requirements."""
        # Base calculation
        base_memory = predict_memory_requirements(
            model_size_gb=7,
            context_length=2048,
            batch_size=1
        )

        # Double batch size
        double_batch_memory = predict_memory_requirements(
            model_size_gb=7,
            context_length=2048,
            batch_size=2
        )

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
            base_memory = predict_memory_requirements(
                model_size_gb=7,
                context_length=2048,
                batch_size=1
            )

            # Calculation with increased factor
            custom_memory = predict_memory_requirements(
                model_size_gb=7,
                context_length=2048,
                batch_size=1,
                kv_cache_factor=3.0  # Explicitly passed to override default
            )

            # Memory should be higher with larger KV cache factor
            assert custom_memory > base_memory

    def test_model_size_scaling(self):
        """Test linear scaling with model size."""
        # Small model
        small_model_memory = predict_memory_requirements(
            model_size_gb=7,
            context_length=2048,
            batch_size=1
        )

        # Double model size
        large_model_memory = predict_memory_requirements(
            model_size_gb=14,
            context_length=2048,
            batch_size=1
        )

        # Memory should roughly double (not exactly due to KV cache scaling)
        # But should be at least 1.8x and less than 2.2x
        ratio = large_model_memory / small_model_memory
        assert 1.8 <= ratio <= 2.2