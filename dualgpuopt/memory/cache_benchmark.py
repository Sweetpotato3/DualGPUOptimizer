"""
Cache system benchmark and validation script.

This script tests the performance, correctness, and memory characteristics
of the thread-safe caching system.
"""

import time
import gc
import statistics
from concurrent.futures import ThreadPoolExecutor
import tracemalloc

from dualgpuopt.memory.cache_utils import thread_safe_cache, method_cache, get_cache_stats


# Test 1: Performance improvement with fibonacci
def benchmark_fibonacci():
    print("\n=== Fibonacci Performance Benchmark ===")
    
    # Non-cached version
    def fib_nocache(n):
        if n <= 1:
            return n
        return fib_nocache(n-1) + fib_nocache(n-2)
    
    # Cached version
    @thread_safe_cache(maxsize=100)
    def fib_cached(n):
        if n <= 1:
            return n
        return fib_cached(n-1) + fib_cached(n-2)
    
    # Test parameters
    n_values = [20, 25, 30, 32]
    
    # Test non-cached version
    print("Non-cached version:")
    for n in n_values:
        start = time.time()
        result = fib_nocache(n)
        duration = time.time() - start
        print(f"  fib({n}) = {result} took {duration:.6f} seconds")
    
    # Test cached version - first run
    print("\nCached version (first run):")
    for n in n_values:
        start = time.time()
        result = fib_cached(n)
        duration = time.time() - start
        print(f"  fib({n}) = {result} took {duration:.6f} seconds")
    
    # Test cached version - second run
    print("\nCached version (second run, should be near-instant):")
    for n in n_values:
        start = time.time()
        result = fib_cached(n)
        duration = time.time() - start
        print(f"  fib({n}) = {result} took {duration:.6f} seconds")
    
    # Print cache stats
    cache_info = fib_cached.cache_info()
    print(f"\nCache info: {cache_info}")


# Test 2: Thread safety validation
def test_thread_safety():
    print("\n=== Thread Safety Test ===")
    
    # Shared results list
    results = []
    
    # Create a cached function that simulates a slow computation
    @thread_safe_cache(maxsize=100, name="thread_safety_test")
    def cached_compute(x):
        # Simulate computation
        time.sleep(0.01)
        return x * 2
    
    def worker(_, iterations):
        thread_results = []
        for _ in range(iterations):
            # Call with the same value from multiple threads
            result = cached_compute(100)
            thread_results.append(result)
        return thread_results
    
    # Run with multiple threads
    num_threads = 10
    iterations = 100
    total_calls = num_threads * iterations
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, i, iterations) for i in range(num_threads)]
        for future in futures:
            results.extend(future.result())
    duration = time.time() - start
    
    # Validate results
    correct_result = 100 * 2
    all_correct = all(r == correct_result for r in results)
    print(f"All results correct: {all_correct}")
    print(f"Total threads: {num_threads}, total calls: {total_calls}")
    print(f"Execution time: {duration:.6f} seconds")
    
    # Check cache stats
    stats = get_cache_stats("thread_safety_test")
    hit_ratio = stats.hit_ratio * 100
    print(f"Cache hits: {stats.hits}, misses: {stats.misses}, hit ratio: {hit_ratio:.2f}%")
    print(f"Expected hits = total calls - 1 = {total_calls - 1}")
    print("Expected misses = 1")
    print(f"Thread safety validated: {stats.hits == total_calls - 1 and stats.misses == 1}")


# Test 3: Method caching validation
def test_method_caching():
    print("\n=== Method Cache Test ===")
    
    class ExpensiveCalculator:
        def __init__(self, name, multiplier):
            self.name = name
            self.multiplier = multiplier
            self.calls = 0
        
        @method_cache(maxsize=50)
        def calculate(self, x, y=1):
            self.calls += 1
            # Simulate expensive calculation
            time.sleep(0.01)
            return (x * y) * self.multiplier
    
    # Create multiple instances
    calc1 = ExpensiveCalculator("calc1", 2)
    calc2 = ExpensiveCalculator("calc2", 3)
    
    # Test instance-specific caching
    print("Testing instance-specific caching...")
    
    # Call on first instance
    start = time.time()
    result1_1 = calc1.calculate(10, 5)
    duration1_1 = time.time() - start
    
    # Call again on first instance
    start = time.time()
    result1_2 = calc1.calculate(10, 5)
    duration1_2 = time.time() - start
    
    # Call on second instance
    start = time.time()
    result2 = calc2.calculate(10, 5)
    duration2 = time.time() - start
    
    print(f"First call on calc1: result={result1_1}, time={duration1_1:.6f}s, calls={calc1.calls}")
    print(f"Second call on calc1: result={result1_2}, time={duration1_2:.6f}s, calls={calc1.calls}")
    print(f"First call on calc2: result={result2}, time={duration2:.6f}s, calls={calc2.calls}")
    
    # Validate instance isolation
    print("\nValidating instance isolation:")
    expected_calls_calc1 = 1  # Should only compute once for calc1
    expected_calls_calc2 = 1  # Should compute once for calc2 despite same params
    print(f"calc1 calls: {calc1.calls} (expected: {expected_calls_calc1})")
    print(f"calc2 calls: {calc2.calls} (expected: {expected_calls_calc2})")
    
    # Test cache cleanup
    print("\nTesting cache cleanup...")
    calc1.calculate.cache_cleanup(calc1)
    
    # Call again after cleanup
    start = time.time()
    result1_3 = calc1.calculate(10, 5)
    duration1_3 = time.time() - start
    
    print(f"Call after cleanup: result={result1_3}, time={duration1_3:.6f}s, calls={calc1.calls}")
    print(f"Expected calls after cleanup: {expected_calls_calc1 + 1}")
    
    # Verify cleanup worked correctly
    is_cleanup_successful = calc1.calls == expected_calls_calc1 + 1
    print(f"Cleanup validation: {is_cleanup_successful}")


# Test 4: Memory usage analysis
def test_memory_usage():
    print("\n=== Memory Usage Analysis ===")
    
    # Start tracking memory
    tracemalloc.start()
    
    # Test functions
    def create_data(size):
        # Create list of numbers
        return [i for i in range(size)]
    
    @thread_safe_cache(maxsize=10, name="mem_test")
    def cached_create_data(size):
        # Create list of numbers
        return [i for i in range(size)]
    
    # Memory test parameters
    sizes = [100_000, 200_000, 300_000, 400_000, 500_000]
    iterations = 10
    
    # Measure memory usage without caching
    current, peak = tracemalloc.get_traced_memory()
    print(f"Initial memory usage: {current / 1024 / 1024:.2f} MB")
    
    print("\nWithout caching:")
    non_cached_sizes = []
    for _ in range(iterations):
        for size in sizes:
            # Force garbage collection
            gc.collect()
            
            # Measure memory before
            before, _ = tracemalloc.get_traced_memory()
            
            # Create data
            data = create_data(size)
            
            # Measure memory after
            after, _ = tracemalloc.get_traced_memory()
            memory_increase = after - before
            non_cached_sizes.append(memory_increase)
            
            # Clear data
            del data
    
    # Measure memory usage with caching
    print("\nWith caching:")
    cached_sizes = []
    for _ in range(iterations):
        for size in sizes:
            # Force garbage collection
            gc.collect()
            
            # Measure memory before
            before, _ = tracemalloc.get_traced_memory()
            
            # Create data
            data = cached_create_data(size)
            
            # Measure memory after
            after, _ = tracemalloc.get_traced_memory()
            memory_increase = after - before
            cached_sizes.append(memory_increase)
            
            # Clear data reference but keep cache
            del data
    
    # Print statistics
    print("\nMemory usage statistics (bytes):")
    print(f"  Without caching - mean: {statistics.mean(non_cached_sizes):.0f}, "
          f"median: {statistics.median(non_cached_sizes):.0f}")
    print(f"  With caching - mean: {statistics.mean(cached_sizes):.0f}, "
          f"median: {statistics.median(cached_sizes):.0f}")
    
    # Print cache stats
    stats = get_cache_stats("mem_test")
    print(f"\nCache stats - hits: {stats.hits}, misses: {stats.misses}, hit ratio: {stats.hit_ratio:.2f}")
    
    # Stop tracking memory
    tracemalloc.stop()


if __name__ == "__main__":
    print("Running cache benchmarks and validation tests...")
    
    # Test performance
    benchmark_fibonacci()
    
    # Test thread safety
    test_thread_safety()
    
    # Test method caching
    test_method_caching()
    
    # Test memory usage
    test_memory_usage()
    
    print("\nAll tests completed successfully!") 