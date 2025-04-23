"""
Smart batching system for length-aware inference scheduling.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("dualgpuopt.batch")


class SmartBatcher:
    """
    Length-aware batch scheduler for optimized inference.

    This class groups similar length sequences together to improve throughput
    while maintaining low latency.
    """

    def __init__(
        self,
        max_batch_size: int = 32,
        length_threshold: int = 256,
    ) -> None:
        """
        Initialize the smart batcher.

        Args:
        ----
            max_batch_size: Maximum number of sequences in a batch
            length_threshold: Threshold for considering sequences as "long"

        """
        self.max_batch_size = max_batch_size
        self.length_threshold = length_threshold
        self.logger = logging.getLogger("dualgpuopt.batch.smart_batch")

    def optimize_batches(
        self,
        sequences: list[tuple[str, int]],
    ) -> list[list[int]]:
        """
        Group sequences into optimized batches.

        Args:
        ----
            sequences: List of (text, sequence_id) tuples

        Returns:
        -------
            List of batches, where each batch is a list of sequence IDs

        """
        if not sequences:
            return []

        # Sort sequences by length
        seq_lengths = [(len(seq[0]), seq[1]) for seq in sequences]
        sorted_seqs = sorted(seq_lengths, key=lambda x: x[0])

        # Group into batches
        batches: list[list[int]] = []
        current_batch: list[int] = []
        current_length = 0

        for length, seq_id in sorted_seqs:
            # If adding this sequence would exceed max batch size or
            # it's a long sequence and the batch already has items
            if len(current_batch) >= self.max_batch_size or (
                length > self.length_threshold and current_batch
            ):
                batches.append(current_batch)
                current_batch = [seq_id]
                current_length = length
            else:
                current_batch.append(seq_id)
                current_length = max(current_length, length)

        # Add the last batch if not empty
        if current_batch:
            batches.append(current_batch)

        self.logger.debug(
            f"Created {len(batches)} optimized batches from {len(sequences)} sequences"
        )
        return batches


def optimize_batch_size(
    gpu_memory_gb: float,
    model_size_gb: float,
) -> int:
    """
    Calculate optimal batch size based on available GPU memory.

    Args:
    ----
        gpu_memory_gb: Available GPU memory in GB
        model_size_gb: Model size in GB

    Returns:
    -------
        Optimal batch size

    """
    # Simple heuristic: leave 20% for overhead, use rest for batching
    available_memory = gpu_memory_gb * 0.8 - model_size_gb

    # Assuming each sequence in batch uses ~5% of model size
    per_sequence_gb = model_size_gb * 0.05

    batch_size = int(available_memory / per_sequence_gb)
    return max(1, min(batch_size, 64))  # Clamp between 1 and 64
