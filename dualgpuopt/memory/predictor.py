"""
Memory usage prediction and modeling for GPU monitoring.

This module provides classes for predicting memory usage based on
model profiles and historical data.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple

import numpy as np

# Initialize module-level logger
logger = logging.getLogger("DualGPUOpt.MemoryPredictor")


class MemoryProfile:
    """Memory usage profile for a specific model or workload"""

    def __init__(self,
                name: str,
                base_usage: int,                  # Base memory usage in bytes
                per_batch_usage: int,             # Additional memory per batch item in bytes
                per_token_usage: int,             # Memory per token in bytes
                growth_rate: float = 1.05,        # Memory growth rate factor
                recovery_buffer: float = 0.85):   # Target usage after OOM recovery
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

    def estimate_usage(self, batch_size: int, token_count: int) -> int:
        """Estimate memory usage for given batch size and token count"""
        return self.base_usage + (self.per_batch_usage * batch_size) + (self.per_token_usage * token_count)

    def max_batch_size(self, available_memory: int, token_count: int) -> int:
        """Calculate maximum batch size given available memory and token count"""
        if self.per_batch_usage <= 0:
            return 1  # Avoid division by zero

        # Calculate memory available for batches
        batch_memory = available_memory - self.base_usage - (self.per_token_usage * token_count)

        # Calculate max batch size and apply safety factor
        max_batch = int(batch_memory / self.per_batch_usage)
        return max(1, max_batch)  # Ensure at least batch size 1

    def max_sequence_length(self, available_memory: int, batch_size: int) -> int:
        """Calculate maximum sequence length given available memory and batch size"""
        if self.per_token_usage <= 0:
            return 2048  # Default to reasonable value

        # Calculate memory available for tokens
        token_memory = available_memory - self.base_usage - (self.per_batch_usage * batch_size)

        # Calculate max sequence length
        max_length = int(token_memory / self.per_token_usage)
        return max(128, max_length)  # Ensure reasonable minimum

    def update_history(self, memory_usage: int):
        """Update usage history with current memory usage"""
        self.usage_history.append((time.time(), memory_usage))

        # Keep last 100 data points
        if len(self.usage_history) > 100:
            self.usage_history = self.usage_history[-100:]

    def project_growth(self, time_horizon: float = 60.0) -> Optional[int]:
        """Project memory growth over time horizon in seconds"""
        if len(self.usage_history) < 5:
            return None  # Not enough data

        # Extract times and usages
        times, usages = zip(*self.usage_history)
        times = np.array(times)
        usages = np.array(usages)

        # Calculate time differences from now
        current_time = time.time()
        time_diffs = current_time - times

        # Filter to recent history (last 5 minutes)
        recent_mask = time_diffs < 300
        if np.sum(recent_mask) < 3:
            return None  # Not enough recent data

        # Fit linear model to recent data
        times_filtered = times[recent_mask]
        usages_filtered = usages[recent_mask]

        try:
            # Simple linear regression
            times_norm = times_filtered - np.min(times_filtered)
            if np.max(times_norm) == 0:
                return usages_filtered[-1]  # No time variation, return last value

            slope, intercept = np.polyfit(times_norm, usages_filtered, 1)

            # Project memory usage
            projected_usage = intercept + slope * (time_horizon)

            # Apply growth factor to account for non-linear growth
            return int(projected_usage * self.growth_rate)
        except:
            return None  # Error in projection


# Default memory profiles for common models
DEFAULT_PROFILES = {
    "llama2-7b": MemoryProfile(
        name="llama2-7b",
        base_usage=7 * 1024 * 1024 * 1024,  # 7 GB base
        per_batch_usage=50 * 1024 * 1024,   # 50 MB per batch
        per_token_usage=3 * 1024,          # 3 KB per token
    ),
    "llama2-13b": MemoryProfile(
        name="llama2-13b",
        base_usage=13 * 1024 * 1024 * 1024,  # 13 GB base
        per_batch_usage=100 * 1024 * 1024,   # 100 MB per batch
        per_token_usage=5 * 1024,           # 5 KB per token
    ),
    "llama2-70b": MemoryProfile(
        name="llama2-70b",
        base_usage=35 * 1024 * 1024 * 1024,  # 35 GB base (split across GPUs)
        per_batch_usage=350 * 1024 * 1024,   # 350 MB per batch
        per_token_usage=18 * 1024,          # 18 KB per token
    ),
    "mistral-7b": MemoryProfile(
        name="mistral-7b",
        base_usage=8 * 1024 * 1024 * 1024,   # 8 GB base
        per_batch_usage=55 * 1024 * 1024,    # 55 MB per batch
        per_token_usage=3 * 1024,           # 3 KB per token
    ),
    "mixtral-8x7b": MemoryProfile(
        name="mixtral-8x7b",
        base_usage=25 * 1024 * 1024 * 1024,  # 25 GB base (shared across GPUs)
        per_batch_usage=200 * 1024 * 1024,   # 200 MB per batch
        per_token_usage=12 * 1024,          # 12 KB per token
    )
}


def initialize_memory_profiles():
    """Initialize default memory profiles"""
    from dualgpuopt.memory.monitor import get_memory_monitor

    monitor = get_memory_monitor()
    for profile in DEFAULT_PROFILES.values():
        monitor.register_profile(profile)
    logger.info(f"Initialized {len(DEFAULT_PROFILES)} default memory profiles")