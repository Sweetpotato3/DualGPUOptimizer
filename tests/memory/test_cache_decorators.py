import concurrent.futures
import time
import unittest

from dualgpuopt.memory.cache_utils import get_cache_stats, method_cache, thread_safe_cache


class TestCacheDecorators(unittest.TestCase):
    """Test suite for the thread-safe cache decorators"""

    def test_thread_safe_cache_basic(self):
        """Test basic functionality of thread_safe_cache decorator"""
        # Track number of function calls
        call_count = 0

        @thread_safe_cache(maxsize=5)
        def expensive_function(x, y=10):
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)  # Simulate expensive operation
            return x * y

        # First call should execute the function
        result1 = expensive_function(5)
        self.assertEqual(result1, 50)
        self.assertEqual(call_count, 1)

        # Second call with same args should use the cache
        result2 = expensive_function(5)
        self.assertEqual(result2, 50)
        self.assertEqual(call_count, 1)  # No additional call

        # Call with different args should execute the function
        result3 = expensive_function(10)
        self.assertEqual(result3, 100)
        self.assertEqual(call_count, 2)

        # Check cache info
        cache_info = expensive_function.cache_info()
        self.assertEqual(cache_info["hits"], 1)
        self.assertEqual(cache_info["misses"], 2)
        self.assertEqual(cache_info["currsize"], 2)

    def test_thread_safe_cache_eviction(self):
        """Test cache eviction with thread_safe_cache decorator"""

        @thread_safe_cache(maxsize=3)
        def cached_function(x):
            return x * 2

        # Fill the cache
        for i in range(5):
            cached_function(i)

        # Check cache size
        self.assertEqual(cached_function.cache_info()["currsize"], 3)

        # Most recent 3 values should be cached (2, 3, 4)
        for i in range(3):
            # Reset the cache stats
            hits_before = cached_function.cache_info()["hits"]
            cached_function(i)
            hits_after = cached_function.cache_info()["hits"]
            # The first 2 values should be evicted (0, 1)
            self.assertEqual(hits_after - hits_before, 1 if i >= 2 else 0)

    def test_thread_safe_cache_concurrency(self):
        """Test thread safety of the cache decorator"""
        call_count = 0

        @thread_safe_cache(maxsize=100)
        def cached_function(x):
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)  # Simulate expensive operation
            return x * 2

        def worker():
            results = []
            # Call with the same value multiple times
            for _ in range(10):
                results.append(cached_function(5))
            return results

        # Run 5 threads simultaneously
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker) for _ in range(5)]
            results = [future.result() for future in futures]

        # All results should be the same
        for result_list in results:
            self.assertEqual(result_list, [10] * 10)

        # The function should only be called once despite 50 total calls
        self.assertEqual(call_count, 1)

        # Cache should show 49 hits and 1 miss
        cache_info = cached_function.cache_info()
        self.assertEqual(cache_info["hits"], 49)
        self.assertEqual(cache_info["misses"], 1)

    def test_clear_cache(self):
        """Test clearing the cache"""

        @thread_safe_cache(maxsize=10)
        def cached_function(x):
            return x * 2

        # Fill cache
        for i in range(5):
            cached_function(i)

        # Check cache contains items
        self.assertEqual(cached_function.cache_info()["currsize"], 5)

        # Clear cache
        cached_function.clear_cache()

        # Cache should be empty
        self.assertEqual(cached_function.cache_info()["currsize"], 0)

        # Next call should be a miss
        hits_before = cached_function.cache_info()["hits"]
        cached_function(0)  # Was previously called
        hits_after = cached_function.cache_info()["hits"]
        self.assertEqual(hits_after - hits_before, 0)  # Should be a miss

    def test_method_cache(self):
        """Test method_cache decorator on class methods"""
        call_count = 0

        class TestClass:
            def __init__(self, multiplier):
                self.multiplier = multiplier

            @method_cache(maxsize=5)
            def cached_method(self, x):
                nonlocal call_count
                call_count += 1
                return x * self.multiplier

        # Create two instances
        obj1 = TestClass(2)
        obj2 = TestClass(3)

        # Call on first instance
        result1_1 = obj1.cached_method(5)
        self.assertEqual(result1_1, 10)
        self.assertEqual(call_count, 1)

        # Call again on first instance (should hit cache)
        result1_2 = obj1.cached_method(5)
        self.assertEqual(result1_2, 10)
        self.assertEqual(call_count, 1)  # No additional call

        # Call on second instance (should miss cache despite same input)
        result2 = obj2.cached_method(5)
        self.assertEqual(result2, 15)  # Different result due to different multiplier
        self.assertEqual(call_count, 2)  # New call for different instance

        # Clean up instance cache
        obj1.cached_method.cache_cleanup(obj1)

        # Next call on obj1 should miss cache
        obj1.cached_method(5)
        self.assertEqual(call_count, 3)

    def test_cache_stats_registry(self):
        """Test that cache statistics are properly registered"""

        # Create a cached function with a specific name
        @thread_safe_cache(name="test_function")
        def cached_function(x):
            return x * 2

        # Call function to generate stats
        cached_function(5)
        cached_function(5)  # Hit
        cached_function(10)  # Miss

        # Get stats from registry
        stats = get_cache_stats("test_function")
        self.assertEqual(stats.hits, 1)
        self.assertEqual(stats.misses, 2)
        self.assertEqual(stats.total, 3)
        self.assertAlmostEqual(stats.hit_ratio, 1 / 3)


if __name__ == "__main__":
    unittest.main()
