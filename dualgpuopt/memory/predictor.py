"""
Memory usage prediction and modeling for GPU monitoring.

This module provides classes for predicting memory usage based on
model profiles and historical data.
"""

import logging
import os
import time
from functools import lru_cache
from typing import List, Optional, Set, Tuple

# Try to import numpy for optimized calculations
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# Initialize module-level logger
logger = logging.getLogger("DualGPUOpt.MemoryPredictor")

# Environment configuration
ENV_PROFILE_CACHE_SIZE = int(os.environ.get("DUALGPUOPT_PROFILE_CACHE", "64"))  # Items in LRU cache


class MemoryProfile:
    """Memory usage profile for a specific model or workload"""

    def __init__(
        self,
        name: str,
        base_usage: int,  # Base memory usage in bytes
        per_batch_usage: int,  # Additional memory per batch item in bytes
        per_token_usage: int,  # Memory per token in bytes
        growth_rate: float = 1.05,  # Memory growth rate factor
        recovery_buffer: float = 0.85,
    ):  # Target usage after OOM recovery
        """
        Initialize memory profile

        Args:
            name: Profile name
            base_usage: Base memory usage in bytes
            per_batch_usage: Additional memory per batch item in bytes
            per_token_usage: Memory per token in bytes
            growth_rate: Memory growth rate factor for projections
            recovery_buffer: Target usage percentage after OOM recovery
        """
        self.name = name
        self.base_usage = base_usage
        self.per_batch_usage = per_batch_usage
        self.per_token_usage = per_token_usage
        self.growth_rate = growth_rate
        self.recovery_buffer = recovery_buffer
        self.usage_history: List[Tuple[float, int]] = []  # (timestamp, bytes)

        # Add cache to reduce repeated calculations
        self._estimation_cache = {}
        self._max_batch_cache = {}
        self._max_seq_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def clear_caches(self) -> None:
        """Clear all calculation caches"""
        self._estimation_cache.clear()
        self._max_batch_cache.clear()
        self._max_seq_cache.clear()

    # Using method-level cache dictionary instead of lru_cache to avoid memory leaks
    def _estimate_usage_cached(
        self, batch_size: int, token_count: int, kv_cache_factor: float = 1.0
    ) -> int:
        """Cached version of memory estimation

        Args:
            batch_size: Batch size to estimate for
            token_count: Number of tokens to estimate for
            kv_cache_factor: Multiplier for token memory (KV cache scaling)

        Returns:
            Estimated memory usage in bytes
        """
        # Create cache key
        cache_key = (batch_size, token_count, kv_cache_factor)

        # Check if result is in cache
        if cache_key in self._estimation_cache:
            self._cache_hits += 1
            return self._estimation_cache[cache_key]

        # Calculate result if not in cache
        self._cache_misses += 1
        # Apply the KV cache factor to the token memory calculation
        token_memory = self.per_token_usage * token_count * kv_cache_factor
        result = self.base_usage + (self.per_batch_usage * batch_size) + token_memory

        # Store in cache (maintain cache size limit)
        if len(self._estimation_cache) >= ENV_PROFILE_CACHE_SIZE:
            # Remove a random entry when full
            self._estimation_cache.pop(next(iter(self._estimation_cache)))

        self._estimation_cache[cache_key] = result
        return result

    def estimate_usage(
        self, batch_size: int, token_count: int, kv_cache_factor: float = 1.0
    ) -> int:
        """Estimate memory usage for given batch size and token count

        Args:
            batch_size: Batch size to estimate for
            token_count: Number of tokens to estimate for
            kv_cache_factor: Multiplier for token memory (KV cache scaling)

        Returns:
            Estimated memory usage in bytes
        """
        # Convert to positive integers
        batch_size = max(1, int(batch_size))
        token_count = max(1, int(token_count))
        kv_cache_factor = max(0.1, float(kv_cache_factor))  # Ensure positive factor

        # Use the cached version
        return self._estimate_usage_cached(batch_size, token_count, kv_cache_factor)

    # Using manual caching instead of lru_cache to avoid memory leaks
    def max_batch_size(self, available_memory: int, token_count: int) -> int:
        """Calculate maximum batch size given available memory and token count

        Args:
            available_memory: Available memory in bytes
            token_count: Number of tokens per sequence

        Returns:
            Maximum batch size
        """
        # Create cache key
        cache_key = (available_memory, token_count)

        # Check if result is in cache
        if cache_key in self._max_batch_cache:
            self._cache_hits += 1
            return self._max_batch_cache[cache_key]

        # Calculate result if not in cache
        self._cache_misses += 1

        if self.per_batch_usage <= 0:
            return 1  # Avoid division by zero

        # Convert to positive values
        available_memory = max(0, int(available_memory))
        token_count = max(0, int(token_count))

        # Calculate memory available for batches
        token_memory = self.per_token_usage * token_count
        batch_memory = available_memory - self.base_usage - token_memory

        # Calculate max batch size and apply safety factor
        if batch_memory <= 0:
            result = 1  # No memory available for batches
        else:
            result = max(
                1, int(batch_memory / self.per_batch_usage)
            )  # Ensure at least batch size 1

        # Store in cache (maintain cache size limit)
        if len(self._max_batch_cache) >= ENV_PROFILE_CACHE_SIZE:
            # Remove a random entry when full
            self._max_batch_cache.pop(next(iter(self._max_batch_cache)))

        self._max_batch_cache[cache_key] = result
        return result

    # Using manual caching instead of lru_cache to avoid memory leaks
    def max_sequence_length(self, available_memory: int, batch_size: int) -> int:
        """Calculate maximum sequence length given available memory and batch size

        Args:
            available_memory: Available memory in bytes
            batch_size: Batch size

        Returns:
            Maximum sequence length
        """
        # Create cache key
        cache_key = (available_memory, batch_size)

        # Check if result is in cache
        if cache_key in self._max_seq_cache:
            self._cache_hits += 1
            return self._max_seq_cache[cache_key]

        # Calculate result if not in cache
        self._cache_misses += 1

        if self.per_token_usage <= 0:
            return 2048  # Default to reasonable value

        # Convert to positive values
        available_memory = max(0, int(available_memory))
        batch_size = max(1, int(batch_size))

        # Calculate memory available for tokens
        batch_memory = self.per_batch_usage * batch_size
        token_memory = available_memory - self.base_usage - batch_memory

        # Calculate max sequence length
        if token_memory <= 0:
            result = 128  # Minimum reasonable length
        else:
            result = max(128, int(token_memory / self.per_token_usage))  # Ensure reasonable minimum

        # Store in cache (maintain cache size limit)
        if len(self._max_seq_cache) >= ENV_PROFILE_CACHE_SIZE:
            # Remove a random entry when full
            self._max_seq_cache.pop(next(iter(self._max_seq_cache)))

        self._max_seq_cache[cache_key] = result
        return result

    def update_history(self, memory_usage: int, max_history: int = 100) -> None:
        """Update usage history with current memory usage

        Args:
            memory_usage: Current memory usage in bytes
            max_history: Maximum history points to keep
        """
        timestamp = time.time()
        self.usage_history.append((timestamp, memory_usage))

        # Keep last N data points
        if len(self.usage_history) > max_history:
            self.usage_history = self.usage_history[-max_history:]

    def project_growth(self, time_horizon: float = 60.0) -> Optional[int]:
        """Project memory growth over time horizon in seconds

        Args:
            time_horizon: Time horizon for projection in seconds

        Returns:
            Projected memory usage in bytes, or None if projection not possible
        """
        if len(self.usage_history) < 5:
            return None  # Not enough data

        # Use numpy for vectorized operations if available
        if NUMPY_AVAILABLE:
            # Extract times and usages
            times, usages = zip(*self.usage_history)
            times_array = np.array(times)
            usages_array = np.array(usages)

            # Calculate time differences from now
            current_time = time.time()
            time_diffs = current_time - times_array

            # Filter to recent history (last 5 minutes)
            recent_mask = time_diffs < 300
            if np.sum(recent_mask) < 3:
                return None  # Not enough recent data

            # Fit linear model to recent data
            times_filtered = times_array[recent_mask]
            usages_filtered = usages_array[recent_mask]

            try:
                # Simple linear regression
                times_norm = times_filtered - np.min(times_filtered)
                if np.max(times_norm) == 0:
                    return usages_filtered[-1]  # No time variation, return last value

                slope, intercept = np.polyfit(times_norm, usages_filtered, 1)

                # Project memory usage
                projected_usage = intercept + slope * time_horizon

                # Apply growth factor to account for non-linear growth
                return int(projected_usage * self.growth_rate)
            except Exception:
                return None  # Error in projection
        else:
            # Standard Python implementation without numpy
            # Extract times and usages
            times = [t for t, _ in self.usage_history]
            usages = [u for _, u in self.usage_history]

            # Calculate time differences from now
            current_time = time.time()
            time_diffs = [current_time - t for t in times]

            # Filter to recent history (last 5 minutes)
            recent_data = [
                (t, u) for (t, u), diff in zip(self.usage_history, time_diffs) if diff < 300
            ]
            if len(recent_data) < 3:
                return None  # Not enough recent data

            # Extract recent times and usages
            recent_times = [t for t, _ in recent_data]
            recent_usages = [u for _, u in recent_data]

            try:
                # Normalize times
                min_time = min(recent_times)
                recent_times_norm = [t - min_time for t in recent_times]
                max_time_norm = max(recent_times_norm)

                if max_time_norm == 0:
                    return recent_usages[-1]  # No time variation, return last value

                # Calculate least squares fit manually
                n = len(recent_times_norm)
                sum_x = sum(recent_times_norm)
                sum_y = sum(recent_usages)
                sum_xx = sum(x * x for x in recent_times_norm)
                sum_xy = sum(x * y for x, y in zip(recent_times_norm, recent_usages))

                # Calculate slope and intercept
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
                intercept = (sum_y - slope * sum_x) / n

                # Project memory usage
                projected_usage = intercept + slope * time_horizon

                # Apply growth factor
                return int(projected_usage * self.growth_rate)
            except Exception:
                return None  # Error in projection

    def batch_estimate_usage(
        self, batch_configs: List[Tuple[int, int]], kv_cache_factor: float = 1.0
    ) -> List[int]:
        """Estimate memory usage for multiple batch configurations at once

        Args:
            batch_configs: List of (batch_size, token_count) tuples
            kv_cache_factor: Multiplier for token memory (KV cache scaling)

        Returns:
            List of estimated memory usage in bytes
        """
        if NUMPY_AVAILABLE and len(batch_configs) > 1:
            # Convert to arrays for vectorized calculation
            batch_sizes = np.array([bs for bs, _ in batch_configs])
            token_counts = np.array([tc for _, tc in batch_configs])

            # Vectorized calculation with kv_cache_factor
            batch_memory = self.per_batch_usage * batch_sizes
            token_memory = self.per_token_usage * token_counts * kv_cache_factor
            total_memory = self.base_usage + batch_memory + token_memory

            return total_memory.tolist()
        else:
            # Standard loop-based calculation
            return [self.estimate_usage(bs, tc, kv_cache_factor) for bs, tc in batch_configs]


# Default memory profiles for common models
DEFAULT_PROFILES = {
    "llama2-7b": MemoryProfile(
        name="llama2-7b",
        base_usage=7 * 1024 * 1024 * 1024,  # 7 GB base
        per_batch_usage=50 * 1024 * 1024,  # 50 MB per batch
        per_token_usage=3 * 1024,  # 3 KB per token
    ),
    "llama2-13b": MemoryProfile(
        name="llama2-13b",
        base_usage=13 * 1024 * 1024 * 1024,  # 13 GB base
        per_batch_usage=100 * 1024 * 1024,  # 100 MB per batch
        per_token_usage=5 * 1024,  # 5 KB per token
    ),
    "llama2-70b": MemoryProfile(
        name="llama2-70b",
        base_usage=35 * 1024 * 1024 * 1024,  # 35 GB base (split across GPUs)
        per_batch_usage=350 * 1024 * 1024,  # 350 MB per batch
        per_token_usage=18 * 1024,  # 18 KB per token
    ),
    "mistral-7b": MemoryProfile(
        name="mistral-7b",
        base_usage=8 * 1024 * 1024 * 1024,  # 8 GB base
        per_batch_usage=55 * 1024 * 1024,  # 55 MB per batch
        per_token_usage=3 * 1024,  # 3 KB per token
    ),
    "mixtral-8x7b": MemoryProfile(
        name="mixtral-8x7b",
        base_usage=25 * 1024 * 1024 * 1024,  # 25 GB base (shared across GPUs)
        per_batch_usage=200 * 1024 * 1024,  # 200 MB per batch
        per_token_usage=12 * 1024,  # 12 KB per token
    ),
}


@lru_cache(maxsize=1)
def get_available_profiles() -> Set[str]:
    """Get the set of available profile names

    Returns:
        Set of profile names
    """
    return set(DEFAULT_PROFILES.keys())


@lru_cache(maxsize=ENV_PROFILE_CACHE_SIZE)
def get_profile(name: str) -> Optional[MemoryProfile]:
    """Get a memory profile by name

    Args:
        name: Profile name

    Returns:
        MemoryProfile or None if not found
    """
    return DEFAULT_PROFILES.get(name)


def clear_profile_caches():
    """Clear all profile caches"""
    get_available_profiles.cache_clear()
    get_profile.cache_clear()

    # Clear caches in all default profiles
    for profile in DEFAULT_PROFILES.values():
        profile.clear_caches()
        # Methods now use manual caching, no need to clear lru_cache

    logger.debug("Cleared all memory profile caches")


def initialize_memory_profiles():
    """Initialize default memory profiles"""
    from dualgpuopt.memory.monitor import get_memory_monitor

    monitor = get_memory_monitor()
    for profile in DEFAULT_PROFILES.values():
        monitor.register_profile(profile)
    logger.info(f"Initialized {len(DEFAULT_PROFILES)} default memory profiles")


def find_optimal_batch(
    available_memory: int,
    profile: MemoryProfile,
    token_lengths: List[int],
    memory_buffer: float = 0.9,
) -> Tuple[int, int]:
    """Find optimal batch size and sequence length given available memory

    Args:
        available_memory: Available memory in bytes
        profile: Memory profile to use
        token_lengths: List of possible token lengths to consider
        memory_buffer: Safety buffer factor (1.0 = use all memory)

    Returns:
        Tuple of (batch_size, sequence_length)
    """
    # Apply safety buffer
    effective_memory = int(available_memory * memory_buffer)

    best_batch = 1
    best_seq_len = min(token_lengths) if token_lengths else 1024
    max_throughput = 0

    if NUMPY_AVAILABLE:
        # Vectorized approach
        seq_lengths = np.array(token_lengths)
        batch_sizes = np.array(
            [profile.max_batch_size(effective_memory, seq_len) for seq_len in seq_lengths]
        )

        # Calculate throughput (batch_size * sequence_length)
        throughputs = batch_sizes * seq_lengths

        # Find maximum throughput
        max_idx = np.argmax(throughputs)
        if throughputs[max_idx] > max_throughput:
            max_throughput = throughputs[max_idx]
            best_batch = int(batch_sizes[max_idx])
            best_seq_len = int(seq_lengths[max_idx])
    else:
        # Standard approach
        for seq_len in token_lengths:
            batch_size = profile.max_batch_size(effective_memory, seq_len)
            throughput = batch_size * seq_len

            if throughput > max_throughput:
                max_throughput = throughput
                best_batch = batch_size
                best_seq_len = seq_len

    return best_batch, best_seq_len
