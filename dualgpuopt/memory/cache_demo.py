"""
Demonstration of caching utilities for DualGPUOptimizer.

This module provides examples of how to use the caching decorators
for various types of functions and methods.
"""

import logging
import time

from dualgpuopt.memory.cache_utils import get_cache_stats, method_cache, thread_safe_cache

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("CacheDemo")


# Example 1: Simple function caching
@thread_safe_cache(maxsize=100)
def fibonacci(n: int) -> int:
    """Calculate fibonacci number (deliberately inefficient for demo)"""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


# Example 2: Method caching with instance-specific cache
class ModelMemoryCalculator:
    """Example class demonstrating method caching"""

    def __init__(self, base_size_mb: int, token_size_bytes: int):
        self.base_size = base_size_mb * 1024 * 1024  # Convert to bytes
        self.token_size = token_size_bytes

    @method_cache(maxsize=50)
    def calculate_memory(self, batch_size: int, sequence_length: int) -> int:
        """Calculate memory usage for given parameters"""
        logger.info(f"Calculating memory for batch={batch_size}, seq_len={sequence_length}")
        # Simulate complex calculation
        time.sleep(0.1)
        return self.base_size + (batch_size * sequence_length * self.token_size)

    @method_cache(maxsize=20)
    def find_optimal_batch(self, available_memory: int, sequence_length: int) -> int:
        """Find optimal batch size for given memory and sequence length"""
        logger.info(
            f"Finding optimal batch for memory={available_memory}, seq_len={sequence_length}"
        )
        # Simulate complex optimization
        time.sleep(0.2)

        # Memory available for batch processing
        batch_memory = available_memory - self.base_size
        if batch_memory <= 0:
            return 1

        # Calculate max batch size
        return max(1, batch_memory // (sequence_length * self.token_size))


def display_cache_stats(name: str) -> None:
    """Display cache statistics for a named cache"""
    stats = get_cache_stats(name)
    logger.info(f"Cache stats for '{name}':")
    logger.info(f"  Hits: {stats.hits}")
    logger.info(f"  Misses: {stats.misses}")
    logger.info(f"  Total: {stats.total}")
    logger.info(f"  Hit ratio: {stats.hit_ratio:.2f}")


def run_demo():
    """Run the cache demonstration"""
    logger.info("Cache Utilities Demonstration")
    logger.info("-" * 50)

    # Example 1: Fibonacci
    logger.info("Example 1: Fibonacci calculation with caching")

    # First run will populate cache
    start_time = time.time()
    result = fibonacci(30)
    first_run_time = time.time() - start_time
    logger.info(f"First run: fibonacci(30) = {result}, time: {first_run_time:.6f}s")

    # Second run will use cache
    start_time = time.time()
    result = fibonacci(30)
    second_run_time = max(0.000001, time.time() - start_time)  # Prevent division by zero
    logger.info(f"Second run: fibonacci(30) = {result}, time: {second_run_time:.6f}s")

    # Calculate speedup factor, ensuring we don't divide by zero
    if second_run_time > 0:
        speedup = first_run_time / second_run_time
        logger.info(f"Speedup factor: {speedup:.1f}x")
    else:
        logger.info("Speedup factor: extremely fast (too quick to measure)")

    # Display cache info
    cache_info = fibonacci.cache_info()
    logger.info(f"Cache info: {cache_info}")

    # Example 2: Method caching
    logger.info("\nExample 2: Method caching for model memory calculation")

    # Create calculator instances
    small_model = ModelMemoryCalculator(
        base_size_mb=7 * 1024, token_size_bytes=2 * 1024
    )  # 7GB model
    large_model = ModelMemoryCalculator(
        base_size_mb=13 * 1024, token_size_bytes=4 * 1024
    )  # 13GB model

    # Calculate memory for small model
    logger.info("Small model calculations:")
    small_model.calculate_memory(10, 1024)  # First call (cache miss)
    small_model.calculate_memory(10, 1024)  # Second call (cache hit)
    small_model.calculate_memory(20, 1024)  # Different params (cache miss)

    # Calculate memory for large model
    logger.info("\nLarge model calculations:")
    large_model.calculate_memory(10, 1024)  # Same params but different instance (cache miss)
    large_model.calculate_memory(10, 1024)  # Second call to large model (cache hit)

    # Find optimal batch sizes
    logger.info("\nOptimal batch size calculations:")
    small_model.find_optimal_batch(16 * 1024 * 1024 * 1024, 2048)  # 16GB memory
    small_model.find_optimal_batch(16 * 1024 * 1024 * 1024, 2048)  # Cache hit
    small_model.find_optimal_batch(32 * 1024 * 1024 * 1024, 2048)  # Different memory (cache miss)

    # Display stats
    logger.info("\nCache Statistics:")
    display_cache_stats("dualgpuopt.memory.cache_demo.fibonacci")

    # Clean up instance cache
    logger.info("\nCleaning up instance cache for small_model")
    small_model.calculate_memory.cache_cleanup(small_model)

    # After cleanup, should be a cache miss
    logger.info("After cleanup, calling calculate_memory again:")
    small_model.calculate_memory(10, 1024)  # Should be a cache miss

    logger.info("-" * 50)
    logger.info("Demo completed")


if __name__ == "__main__":
    run_demo()
