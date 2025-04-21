"""
Resource Manager for CPU/GPU allocation.

Provides a central service for controlling whether operations run on CPU or GPU,
helping preserve VRAM for model inference while using system RAM for other tasks.
"""

from __future__ import annotations

import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, TypeVar, Optional

# Setup logging
logger = logging.getLogger("DualGPUOpt.ResourceManager")

# Type variable for generic function return types
T = TypeVar('T')

# Environment variables for configuration
ENV_CPU_WORKERS = int(os.environ.get("DUALGPUOPT_CPU_WORKERS", "0"))  # 0 means use CPU count


class ResourceType:
    """Resource types for allocation decisions."""
    CPU = "cpu"
    GPU = "gpu"


class ResourceManager:
    """
    Central manager for controlling whether operations run on CPU or GPU.

    This class helps preserve VRAM for model inference by ensuring support
    operations run on CPU, reserving GPU resources for critical tasks.
    """

    def __init__(self, cpu_workers: int = ENV_CPU_WORKERS):
        """
        Initialize the resource manager.

        Args:
            cpu_workers: Number of CPU worker threads (0 for auto-detection)
        """
        self._cpu_executor = ThreadPoolExecutor(
            max_workers=cpu_workers if cpu_workers > 0 else None
        )
        self._component_allocation: Dict[str, str] = self._default_allocations()
        self._lock = threading.RLock()
        logger.info(f"Resource manager initialized with {self._cpu_executor._max_workers} CPU workers")

    def _default_allocations(self) -> Dict[str, str]:
        """Define default resource allocations for components."""
        return {
            "telemetry": ResourceType.CPU,
            "ui": ResourceType.CPU,
            "event_bus": ResourceType.CPU,
            "memory_analysis": ResourceType.CPU,
            "configuration": ResourceType.CPU,
            "command_generation": ResourceType.CPU,
            "model_inference": ResourceType.GPU
        }

    def run_on_cpu(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Run a function on CPU threads, preserving GPU resources.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The result of the function call
        """
        future = self._cpu_executor.submit(func, *args, **kwargs)
        return future.result()

    def get_allocation(self, component: str) -> str:
        """
        Get the current resource allocation for a component.

        Args:
            component: Component name to check

        Returns:
            Resource type (CPU or GPU)
        """
        with self._lock:
            return self._component_allocation.get(component, ResourceType.CPU)

    def set_allocation(self, component: str, resource_type: str) -> None:
        """
        Set the resource allocation for a component.

        Args:
            component: Component name to set
            resource_type: Resource type (CPU or GPU)
        """
        if resource_type not in (ResourceType.CPU, ResourceType.GPU):
            raise ValueError(f"Invalid resource type: {resource_type}")

        with self._lock:
            self._component_allocation[component] = resource_type
            logger.info(f"Set {component} allocation to {resource_type}")

    def should_use_cpu(self, component: str) -> bool:
        """
        Check if a component should use CPU resources.

        Args:
            component: Component name to check

        Returns:
            True if the component should use CPU resources
        """
        return self.get_allocation(component) == ResourceType.CPU

    @staticmethod
    def get_instance() -> ResourceManager:
        """
        Get the global resource manager instance.
        Static method for consistent access across the application.

        Returns:
            The global resource manager instance
        """
        return get_resource_manager()


# Singleton instance
_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    """
    Get the global resource manager instance.

    Returns:
        The global resource manager instance
    """
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager