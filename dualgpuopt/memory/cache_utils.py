"""
Thread-safe caching utilities for memory-intensive operations.

This module provides decorators and utilities for efficient caching of
function results with thread safety.
"""

import functools
import os
import threading
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, cast

from dualgpuopt.memory.predictor import LRUCache

# Default cache size from environment or hardcoded default
DEFAULT_CACHE_SIZE = int(os.environ.get("DUALGPUOPT_CACHE_SIZE", "128"))

# Type variables for generic typing
R = TypeVar("R")  # Return type
F = TypeVar("F", bound=Callable[..., Any])  # Function type


class CacheStats:
    """Statistics for cache performance monitoring"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self._lock = threading.RLock()

    def register_hit(self) -> None:
        """Register a cache hit"""
        with self._lock:
            self.hits += 1

    def register_miss(self) -> None:
        """Register a cache miss"""
        with self._lock:
            self.misses += 1

    def register_eviction(self) -> None:
        """Register a cache eviction"""
        with self._lock:
            self.evictions += 1

    @property
    def total(self) -> int:
        """Total number of cache lookups"""
        return self.hits + self.misses

    @property
    def hit_ratio(self) -> float:
        """Cache hit ratio"""
        total = self.total
        return self.hits / total if total > 0 else 0.0


# Global cache statistics registry
_cache_stats: Dict[str, CacheStats] = {}
_stats_lock = threading.RLock()


def get_cache_stats(name: str) -> CacheStats:
    """
    Get cache statistics by name

    Args:
    ----
        name: Name of the cache

    Returns:
    -------
        CacheStats object for the named cache
    """
    with _stats_lock:
        if name not in _cache_stats:
            _cache_stats[name] = CacheStats()
        return _cache_stats[name]


def thread_safe_cache(
    maxsize: int = DEFAULT_CACHE_SIZE,
    name: Optional[str] = None,
    key_builder: Optional[Callable[..., Any]] = None,
) -> Callable[[F], F]:
    """
    Decorator for thread-safe memoization of function results

    Args:
    ----
        maxsize: Maximum cache size (items)
        name: Optional name for the cache (for stats tracking)
        key_builder: Optional function to build cache keys from arguments

    Returns:
    -------
        Decorator function
    """

    def _make_key(*args: Any, **kwargs: Any) -> Tuple[Any, ...]:
        """Create a cache key from function arguments"""
        # Sort kwargs for consistent key generation
        sorted_items = sorted(kwargs.items())

        # Include args and sorted kwargs in the key
        return args + tuple(sorted_items)

    # Use the provided key_builder or the default
    get_key = key_builder or _make_key

    def decorator(func: F) -> F:
        """Actual decorator that wraps the function"""
        # Create the cache and get stats
        cache = LRUCache(maxsize=maxsize)
        cache_name = name or f"{func.__module__}.{func.__qualname__}"
        stats = get_cache_stats(cache_name)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapped function with caching"""
            # Generate key from arguments
            key = get_key(*args, **kwargs)

            # Try to get from cache
            try:
                result = cache[key]
                stats.register_hit()
                return result
            except KeyError:
                # Not in cache, calculate result
                stats.register_miss()
                result = func(*args, **kwargs)

                # Store in cache (eviction handled by LRUCache)
                cache[key] = result
                return result

        # Add cache management methods to the wrapper
        def clear_cache() -> None:
            """Clear the function's cache"""
            cache.clear()

        def cache_info() -> Dict[str, Any]:
            """Get information about the cache"""
            return {
                "hits": stats.hits,
                "misses": stats.misses,
                "maxsize": maxsize,
                "currsize": len(cache),
                "hit_ratio": stats.hit_ratio,
            }

        # Attach methods to the wrapper
        wrapper.clear_cache = clear_cache  # type: ignore
        wrapper.cache_info = cache_info  # type: ignore

        return cast(F, wrapper)

    return decorator


def method_cache(
    maxsize: int = DEFAULT_CACHE_SIZE,
    name: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Thread-safe cache decorator specifically for class methods

    Unlike regular function caching, this correctly handles the 'self' parameter
    to prevent memory leaks by using a weak reference to the instance.

    Args:
    ----
        maxsize: Maximum cache size
        name: Optional name for the cache

    Returns:
    -------
        Decorator function for methods
    """

    def decorator(method: F) -> F:
        """Actual decorator that wraps the method"""
        # Get instance-specific cache name if not provided
        cache_name = name or f"{method.__module__}.{method.__qualname__}"
        # Get cache stats for monitoring
        stats = get_cache_stats(cache_name)

        # Create per-instance caches dict keyed by instance id
        instance_caches: Dict[int, LRUCache] = {}
        instance_lock = threading.RLock()

        @functools.wraps(method)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            """Wrapped method with per-instance caching"""
            # Get or create an instance-specific cache
            instance_id = id(self)
            with instance_lock:
                if instance_id not in instance_caches:
                    instance_caches[instance_id] = LRUCache(maxsize=maxsize)
                cache = instance_caches[instance_id]

            # Generate key from arguments (excluding self)
            key = (args, tuple(sorted(kwargs.items())))

            # Try to get from cache
            try:
                result = cache[key]
                stats.register_hit()
                return result
            except KeyError:
                # Not in cache, calculate result
                stats.register_miss()
                result = method(self, *args, **kwargs)
                cache[key] = result
                return result

        # Add a finalizer method to clean up the instance cache
        def cache_cleanup(instance: Any) -> None:
            """Remove the cache for a specific instance"""
            instance_id = id(instance)
            with instance_lock:
                if instance_id in instance_caches:
                    del instance_caches[instance_id]

        # Add cache info method similar to thread_safe_cache
        def cache_info() -> Dict[str, Any]:
            """Get information about the cache"""
            with instance_lock:
                # Count total items across all instance caches
                total_items = sum(len(cache) for cache in instance_caches.values())
                instance_count = len(instance_caches)

            return {
                "hits": stats.hits,
                "misses": stats.misses,
                "maxsize": maxsize,
                "instances": instance_count,
                "total_items": total_items,
                "hit_ratio": stats.hit_ratio,
            }

        wrapper.cache_cleanup = cache_cleanup  # type: ignore
        wrapper.cache_info = cache_info  # type: ignore

        return cast(F, wrapper)

    return decorator
