import unittest
import concurrent.futures
from dualgpuopt.memory.predictor import MemoryProfile


class TestMemoryProfile(unittest.TestCase):
    """Test suite for the MemoryProfile caching behavior in the memory predictor module"""

    def setUp(self):
        """Set up a memory profile for testing"""
        self.profile = MemoryProfile(
            name="test_profile",
            base_usage=1024 * 1024 * 1024,  # 1 GB base
            per_batch_usage=10 * 1024 * 1024,  # 10 MB per batch
            per_token_usage=1 * 1024,  # 1 KB per token
            growth_rate=1.05,
            recovery_buffer=0.85,
        )

    def test_estimate_usage_caching(self):
        """Test that estimate_usage properly caches results"""
        # Track initial cache stats
        initial_hits = self.profile._cache_hits
        initial_misses = self.profile._cache_misses
        
        # First call should miss cache
        result1 = self.profile.estimate_usage(10, 1000, 1.0)
        self.assertEqual(self.profile._cache_misses, initial_misses + 1)
        
        # Second call with same params should hit cache
        result2 = self.profile.estimate_usage(10, 1000, 1.0)
        self.assertEqual(self.profile._cache_hits, initial_hits + 1)
        self.assertEqual(result1, result2)
        
        # Call with different params should miss cache
        self.profile.estimate_usage(20, 1000, 1.0)
        self.assertEqual(self.profile._cache_misses, initial_misses + 2)
        
        # Verify correct result
        expected = (
            self.profile.base_usage +
            (self.profile.per_batch_usage * 10) + 
            (self.profile.per_token_usage * 1000)
        )
        self.assertEqual(result1, expected)

    def test_max_batch_size_caching(self):
        """Test that max_batch_size properly caches results"""
        # Track initial cache stats
        initial_hits = self.profile._cache_hits
        initial_misses = self.profile._cache_misses
        
        # First call should miss cache
        memory_size = 4 * 1024 * 1024 * 1024  # 4 GB
        token_count = 2000
        result1 = self.profile.max_batch_size(memory_size, token_count)
        self.assertEqual(self.profile._cache_misses, initial_misses + 1)
        
        # Second call with same params should hit cache
        result2 = self.profile.max_batch_size(memory_size, token_count)
        self.assertEqual(self.profile._cache_hits, initial_hits + 1)
        self.assertEqual(result1, result2)
        
        # Call with different params should miss cache
        self.profile.max_batch_size(memory_size, 3000)
        self.assertEqual(self.profile._cache_misses, initial_misses + 2)
        
        # Calculate expected result
        available_for_batches = (
            memory_size - self.profile.base_usage - 
            (self.profile.per_token_usage * token_count)
        )
        expected = max(1, int(available_for_batches / self.profile.per_batch_usage))
        self.assertEqual(result1, expected)

    def test_max_sequence_length_caching(self):
        """Test that max_sequence_length properly caches results"""
        # Track initial cache stats
        initial_hits = self.profile._cache_hits
        initial_misses = self.profile._cache_misses
        
        # First call should miss cache
        memory_size = 4 * 1024 * 1024 * 1024  # 4 GB
        batch_size = 10
        result1 = self.profile.max_sequence_length(memory_size, batch_size)
        self.assertEqual(self.profile._cache_misses, initial_misses + 1)
        
        # Second call with same params should hit cache
        result2 = self.profile.max_sequence_length(memory_size, batch_size)
        self.assertEqual(self.profile._cache_hits, initial_hits + 1)
        self.assertEqual(result1, result2)
        
        # Call with different params should miss cache
        self.profile.max_sequence_length(memory_size, 20)
        self.assertEqual(self.profile._cache_misses, initial_misses + 2)
        
        # Calculate expected result
        available_for_tokens = (
            memory_size - self.profile.base_usage - 
            (self.profile.per_batch_usage * batch_size)
        )
        expected = max(128, int(available_for_tokens / self.profile.per_token_usage))
        self.assertEqual(result1, expected)

    def test_clear_caches(self):
        """Test that clear_caches properly clears all caches"""
        # Populate caches
        self.profile.estimate_usage(10, 1000, 1.0)
        self.profile.max_batch_size(4 * 1024 * 1024 * 1024, 2000)
        self.profile.max_sequence_length(4 * 1024 * 1024 * 1024, 10)
        
        # Clear caches
        self.profile.clear_caches()
        
        # Track cache stats
        initial_hits = self.profile._cache_hits
        initial_misses = self.profile._cache_misses
        
        # All these calls should miss cache after clearing
        self.profile.estimate_usage(10, 1000, 1.0)
        self.profile.max_batch_size(4 * 1024 * 1024 * 1024, 2000)
        self.profile.max_sequence_length(4 * 1024 * 1024 * 1024, 10)
        
        # Should have 3 misses and no hits
        self.assertEqual(self.profile._cache_hits, initial_hits)
        self.assertEqual(self.profile._cache_misses, initial_misses + 3)

    def test_thread_safety(self):
        """Test thread safety of profile caching"""
        NUM_THREADS = 5
        NUM_ITERATIONS = 100
        
        def worker_function(thread_id):
            for i in range(NUM_ITERATIONS):
                # Use different values to test cache behavior
                batch_size = (i % 5) + 1
                token_count = (i % 10) * 100 + 100
                memory_size = (2 + (i % 4)) * 1024 * 1024 * 1024
                
                try:
                    # Call all cached methods
                    self.profile.estimate_usage(batch_size, token_count, 1.0)
                    self.profile.max_batch_size(memory_size, token_count)
                    self.profile.max_sequence_length(memory_size, batch_size)
                    
                    # Occasionally clear caches
                    if i % 20 == 0:
                        self.profile.clear_caches()
                except Exception as e:
                    return False, str(e)
            return True, None
        
        # Run concurrent operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            futures = [executor.submit(worker_function, i) for i in range(NUM_THREADS)]
            results = [future.result() for future in futures]
        
        # Check all threads completed successfully
        for success, error in results:
            self.assertTrue(success, f"Thread operation failed: {error}")

    def test_batch_estimate_usage(self):
        """Test batch estimation functionality"""
        # Create batch configs
        batch_configs = [
            (5, 1000),   # 5 batches, 1000 tokens
            (10, 2000),  # 10 batches, 2000 tokens
            (15, 1500)   # 15 batches, 1500 tokens
        ]
        
        # Calculate result using batch method
        results = self.profile.batch_estimate_usage(batch_configs, 1.0)
        
        # Calculate expected results individually
        expected_results = []
        for batch_size, token_count in batch_configs:
            expected = (
                self.profile.base_usage +
                (self.profile.per_batch_usage * batch_size) + 
                (self.profile.per_token_usage * token_count)
            )
            expected_results.append(expected)
        
        # Compare results
        self.assertEqual(len(results), len(expected_results))
        for actual, expected in zip(results, expected_results):
            self.assertEqual(actual, expected)

    def test_kv_cache_scaling(self):
        """Test that KV cache factor properly scales token memory"""
        # Calculate with default KV cache factor (1.0)
        result1 = self.profile.estimate_usage(10, 1000, 1.0)
        
        # Calculate with doubled KV cache factor (2.0)
        result2 = self.profile.estimate_usage(10, 1000, 2.0)
        
        # Calculate difference (should be token memory * difference in KV cache factor)
        diff = result2 - result1
        expected_diff = self.profile.per_token_usage * 1000 * 1.0  # Additional token memory
        
        self.assertEqual(diff, expected_diff)


if __name__ == "__main__":
    unittest.main() 