"""
Smart batching system for length-aware inference scheduling
"""
from typing import List, Dict, Any, Optional, Tuple, Callable
import logging
import time
import math
from dataclasses import dataclass

# Initialize logger
logger = logging.getLogger("DualGPUOpt.SmartBatch")


def optimize_batch_size(
    gpu_memory_gb: float,
    model_size_gb: float,
    model_type: str = None
) -> int:
    """Calculate optimal batch size based on model-specific memory requirements

    Args:
        gpu_memory_gb: Available GPU memory in GB
        model_size_gb: Model size in GB
        model_type: Optional model type for specific configurations

    Returns:
        Optimal batch size
    """
    # Get model-specific parameters
    try:
        from ..model_profiles import MODEL_PROFILES

        # Default profile if no model type specified
        if model_type is None or model_type not in MODEL_PROFILES:
            model_type = "default"

        # Get profile parameters
        profile = MODEL_PROFILES.get(model_type, MODEL_PROFILES["default"])
        per_token_memory = profile.get("per_token_memory", 2.0)
        overhead_factor = profile.get("overhead_factor", 0.15)

    except ImportError:
        # Fallback to reasonable defaults if profiles not available
        logger.warning("Model profiles not available, using default parameters")
        per_token_memory = 2.0
        overhead_factor = 0.15

    # Calculate available memory with model-specific overhead
    system_reserve_gb = 1.0  # 1 GB fixed reserve
    available_memory = gpu_memory_gb - (model_size_gb * (1 + overhead_factor)) - system_reserve_gb

    # Calculate memory needed per sequence in batch
    avg_seq_length = 512  # Reasonable default
    per_sequence_gb = (per_token_memory * avg_seq_length) / 1024

    # Calculate batch size with safety margin
    if available_memory <= 0 or per_sequence_gb <= 0:
        return 1

    raw_batch_size = int(available_memory / per_sequence_gb)

    # Apply reasonable bounds, allowing non-power-of-2 for flexibility
    batch_size = max(1, min(raw_batch_size, 64))

    logger.info(f"Optimized batch size: {batch_size} for {model_type} model "
               f"({gpu_memory_gb:.1f}GB GPU, {model_size_gb:.1f}GB model)")
    return batch_size


@dataclass
class BatchStats:
    """Statistics for a processed batch"""
    tokens_in: int
    tokens_out: int
    processing_time: float
    oom_events: int

    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second throughput"""
        if self.processing_time <= 0:
            return 0
        return self.tokens_out / self.processing_time


class SmartBatcher:
    """Length-aware batch scheduler for optimized inference

    Groups similar-length sequences together to improve throughput
    while maintaining low latency
    """

    def __init__(
        self,
        max_batch_size: int = 32,
        length_threshold: int = 256,
        adaptive_sizing: bool = True,
        oom_recovery: bool = True
    ) -> None:
        """Initialize the smart batcher

        Args:
            max_batch_size: Maximum number of sequences in a batch
            length_threshold: Threshold for considering sequences as "long"
            adaptive_sizing: Whether to dynamically adjust batch size based on performance
            oom_recovery: Whether to enable automatic OOM recovery
        """
        self.max_batch_size = max_batch_size
        self.length_threshold = length_threshold
        self.adaptive_sizing = adaptive_sizing
        self.oom_recovery = oom_recovery

        # Performance tracking
        self.batch_stats: List[BatchStats] = []
        self.backpressure_active = False
        self.oom_count = 0
        self.current_scale_factor = 1.0

    def optimize_batches(
        self,
        sequences: List[Tuple[str, int]]
    ) -> List[List[int]]:
        """Group sequences into optimized batches

        Args:
            sequences: List of (text, sequence_id) tuples

        Returns:
            List of batches, where each batch is a list of sequence IDs
        """
        if not sequences:
            return []

        # Sort sequences by length for more efficient processing
        seq_lengths = [(len(seq[0]), seq[1]) for seq in sequences]
        sorted_seqs = sorted(seq_lengths, key=lambda x: x[0])

        # Apply backpressure if active (reduce effective batch size)
        effective_batch_size = self.max_batch_size
        if self.backpressure_active:
            effective_batch_size = max(1, int(effective_batch_size * self.current_scale_factor))
            logger.info(f"Backpressure active: reduced batch size to {effective_batch_size}")

        # Group into batches with enhanced logic
        batches: List[List[int]] = []
        current_batch: List[int] = []
        current_length = 0
        current_token_sum = 0
        max_token_sum = 16384  # Maximum total tokens in a batch

        for length, seq_id in sorted_seqs:
            # Check if adding this sequence would exceed constraints:
            # 1. Batch size limit
            # 2. Large length difference from current batch
            # 3. Total token count exceeds maximum
            if (len(current_batch) >= effective_batch_size or
                (length > self.length_threshold and current_batch and length > 2 * current_length) or
                (current_token_sum + length > max_token_sum)):

                batches.append(current_batch)
                current_batch = [seq_id]
                current_length = length
                current_token_sum = length
            else:
                current_batch.append(seq_id)
                current_length = max(current_length, length)
                current_token_sum += length

        # Add the last batch if not empty
        if current_batch:
            batches.append(current_batch)

        logger.debug(f"Created {len(batches)} optimized batches from {len(sequences)} sequences")
        return batches

    def record_batch_stats(self, stats: BatchStats) -> None:
        """Record statistics for a processed batch

        Args:
            stats: Batch statistics
        """
        self.batch_stats.append(stats)

        # Keep only last 20 batch stats for adaptive sizing
        if len(self.batch_stats) > 20:
            self.batch_stats.pop(0)

        # Update backpressure state
        if stats.oom_events > 0:
            self.oom_count += 1
            self.backpressure_active = True
            # Reduce batch size by 25% after OOM
            self.current_scale_factor = max(0.25, self.current_scale_factor * 0.75)
            logger.warning(f"OOM detected: activating backpressure, scale={self.current_scale_factor:.2f}")
        else:
            # Gradually recover if we've processed 5 batches without OOM
            if self.backpressure_active and len(self.batch_stats) >= 5 and all(s.oom_events == 0 for s in self.batch_stats[-5:]):
                # Increase scale factor, but still keep some backpressure
                self.current_scale_factor = min(0.95, self.current_scale_factor * 1.1)
                logger.info(f"Gradually reducing backpressure, scale={self.current_scale_factor:.2f}")

                # Deactivate backpressure if we're close to normal
                if self.current_scale_factor > 0.9:
                    self.backpressure_active = False
                    logger.info("Backpressure deactivated")

    def reset_cache(self) -> None:
        """Reset CUDA cache to recover from OOM conditions"""
        try:
            import torch
            if torch.cuda.is_available():
                # Clear CUDA cache
                torch.cuda.empty_cache()
                logger.info("CUDA cache cleared for OOM recovery")

                # Perform additional memory cleanup
                for i in range(torch.cuda.device_count()):
                    torch.cuda.reset_peak_memory_stats(i)

                return True
        except ImportError:
            logger.warning("PyTorch not available for cache reset")
        except Exception as e:
            logger.error(f"Error resetting cache: {e}")

        return False