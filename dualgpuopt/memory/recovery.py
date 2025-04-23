"""
Memory recovery strategies for GPU monitoring.

This module provides recovery strategies to prevent OOM conditions
on GPU devices.
"""

import logging
from enum import Enum, auto
from typing import Callable, Dict, Optional

# Initialize module-level logger
logger = logging.getLogger("DualGPUOpt.MemoryRecovery")


class MemoryRecoveryStrategy(Enum):
    """Memory recovery strategies when approaching OOM"""

    REDUCE_BATCH = auto()  # Reduce batch size
    CLEAR_CACHE = auto()  # Clear caches
    OFFLOAD = auto()  # Offload to CPU/disk
    TERMINATE = auto()  # Terminate low-priority processes


class RecoveryManager:
    """
    Manages recovery strategies for memory management.

    Provides a registry of strategies that can be applied when
    memory usage approaches critical levels.
    """

    def __init__(self):
        """Initialize recovery manager"""
        self._recovery_functions: Dict[MemoryRecoveryStrategy, Callable] = {}

    def register_strategy(self, strategy: MemoryRecoveryStrategy, func: Callable) -> None:
        """
        Register a recovery function for the specified strategy

        Args:
        ----
            strategy: Recovery strategy to register
            func: Function to call when strategy is executed
        """
        self._recovery_functions[strategy] = func
        logger.debug(f"Registered recovery function for strategy {strategy.name}")

    def execute_strategy(self, strategy: MemoryRecoveryStrategy, *args, **kwargs) -> bool:
        """
        Execute a specific recovery strategy

        Args:
        ----
            strategy: Recovery strategy to execute
            *args: Arguments to pass to the recovery function
            **kwargs: Keyword arguments to pass to the recovery function

        Returns:
        -------
            True if recovery was successful, False otherwise
        """
        if strategy not in self._recovery_functions:
            logger.warning(f"No recovery function registered for strategy {strategy.name}")
            return False

        try:
            logger.info(f"Executing recovery strategy: {strategy.name}")
            result = self._recovery_functions[strategy](*args, **kwargs)
            if result:
                logger.info(f"Recovery strategy {strategy.name} successful")
                return True
            else:
                logger.warning(f"Recovery strategy {strategy.name} failed")
                return False
        except Exception as e:
            logger.error(f"Error executing recovery strategy {strategy.name}: {e}")
            return False

    def attempt_recovery(
        self, gpu_id: int, memory_stats: dict, strategies: Optional[list] = None
    ) -> bool:
        """
        Attempt recovery using multiple strategies

        Args:
        ----
            gpu_id: GPU device ID
            memory_stats: Current memory statistics
            strategies: List of strategies to try in order (default is all strategies)

        Returns:
        -------
            True if any recovery strategy succeeded, False otherwise
        """
        if strategies is None:
            # Default strategy order from least to most disruptive
            strategies = [
                MemoryRecoveryStrategy.CLEAR_CACHE,
                MemoryRecoveryStrategy.REDUCE_BATCH,
                MemoryRecoveryStrategy.OFFLOAD,
                MemoryRecoveryStrategy.TERMINATE,
            ]

        logger.warning(f"Attempting automatic memory recovery for GPU {gpu_id}")

        for strategy in strategies:
            if self.execute_strategy(strategy, gpu_id, memory_stats):
                return True

        logger.critical(f"All memory recovery strategies failed for GPU {gpu_id}")
        return False


# Default clear cache implementation
def default_clear_cuda_cache(gpu_id: int, memory_stats: dict) -> bool:
    """Default implementation for clearing CUDA cache"""
    try:
        import torch

        # Clear CUDA cache
        with torch.cuda.device(gpu_id):
            torch.cuda.empty_cache()

        logger.info(f"Cleared CUDA cache for GPU {gpu_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to clear CUDA cache: {e}")
        return False
