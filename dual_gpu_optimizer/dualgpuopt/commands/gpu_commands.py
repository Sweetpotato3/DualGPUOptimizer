"""
GPU-specific commands for operations like overclocking.
"""
from __future__ import annotations

import os
from typing import Dict, Any, Optional

from dualgpuopt.commands.command_base import Command
from dualgpuopt.services.config_service import config_service
from dualgpuopt.services.error_service import error_service


class ApplyOverclockCommand(Command):
    """Command to apply overclocking settings to a GPU."""

    def __init__(self,
                gpu_index: int,
                core_offset: int,
                memory_offset: int,
                power_limit: int,
                fan_speed: int,
                auto_fan: bool) -> None:
        """
        Initialize the overclocking command.

        Args:
            gpu_index: GPU index
            core_offset: Core clock offset in MHz
            memory_offset: Memory clock offset in MHz
            power_limit: Power limit percentage
            fan_speed: Fan speed percentage
            auto_fan: Whether to use automatic fan control
        """
        super().__init__("apply_overclock")
        self.gpu_index = gpu_index
        self.core_offset = core_offset
        self.memory_offset = memory_offset
        self.power_limit = power_limit
        self.fan_speed = fan_speed
        self.auto_fan = auto_fan

        # Store original values for undo
        self.original_values: Dict[str, Any] = self._get_current_values()

    def execute(self) -> bool:
        """
        Apply overclocking settings to the GPU.

        Returns:
            Success status
        """
        # Save original values first if not already saved
        if not self.original_values:
            self.original_values = self._get_current_values()

        try:
            # Apply the overclocking
            # This is a mock implementation - in a real application,
            # this would call into the GPU driver APIs
            self.logger.info(f"Applying overclock to GPU {self.gpu_index}:")
            self.logger.info(f"  Core offset: {self.core_offset} MHz")
            self.logger.info(f"  Memory offset: {self.memory_offset} MHz")
            self.logger.info(f"  Power limit: {self.power_limit}%")
            self.logger.info(f"  Fan speed: {'Auto' if self.auto_fan else f'{self.fan_speed}%'}")

            # Save to config
            self._save_to_config()

            # Publish result
            self._publish_result(True, {
                "gpu_index": self.gpu_index,
                "settings": {
                    "core_offset": self.core_offset,
                    "memory_offset": self.memory_offset,
                    "power_limit": self.power_limit,
                    "fan_speed": self.fan_speed,
                    "auto_fan": self.auto_fan
                }
            })

            return True
        except Exception as e:
            error_service.handle_error(e, level="ERROR", title="Overclock Error",
                                    context={"operation": "apply_overclock", "gpu_index": self.gpu_index})
            return False

    def undo(self) -> bool:
        """
        Restore original GPU settings.

        Returns:
            Success status
        """
        try:
            if not self.original_values:
                self.logger.warning("No original values to restore")
                return False

            # Implement logic to restore original values
            self.logger.info(f"Restoring original settings for GPU {self.gpu_index}")

            # Here we would call into the GPU driver APIs to restore
            # the original settings, using self.original_values

            # Save original values back to config
            gpu_oc = config_service.get("gpu_overclock", {})

            if str(self.gpu_index) in gpu_oc:
                # Restore original values in config
                if self.original_values.get("saved", False):
                    gpu_oc[str(self.gpu_index)] = self.original_values
                else:
                    # If there were no original saved values, remove the entry
                    del gpu_oc[str(self.gpu_index)]

                # Save updated config
                config_service.set("gpu_overclock", gpu_oc)

            # Publish result
            self._publish_result(True, {
                "gpu_index": self.gpu_index,
                "restored": True
            })

            return True
        except Exception as e:
            error_service.handle_error(e, level="ERROR", title="Restore Error",
                                    context={"operation": "restore_gpu_settings", "gpu_index": self.gpu_index})
            return False

    def _get_current_values(self) -> Dict[str, Any]:
        """
        Get current GPU settings.

        Returns:
            Current settings
        """
        # In a real application, we would query the GPU driver here
        # For now, just get values from config if they exist
        gpu_oc = config_service.get("gpu_overclock", {})
        settings = gpu_oc.get(str(self.gpu_index), {})

        if settings:
            return {
                "core": settings.get("core", 0),
                "memory": settings.get("memory", 0),
                "power": settings.get("power", 100),
                "fan": settings.get("fan", 0),
                "auto_fan": settings.get("auto_fan", True),
                "saved": True
            }
        return {
            "core": 0,
            "memory": 0,
            "power": 100,
            "fan": 0,
            "auto_fan": True,
            "saved": False
        }

    def _save_to_config(self) -> None:
        """Save settings to configuration."""
        # Get current GPU overclock settings
        gpu_oc = config_service.get("gpu_overclock", {})

        # Update settings for this GPU
        gpu_oc[str(self.gpu_index)] = {
            "core": self.core_offset,
            "memory": self.memory_offset,
            "power": self.power_limit,
            "fan": self.fan_speed,
            "auto_fan": self.auto_fan
        }

        # Save updated settings
        config_service.set("gpu_overclock", gpu_oc)


class EnableMockGpuCommand(Command):
    """Command to enable mock GPU mode."""

    def __init__(self) -> None:
        """Initialize the command."""
        super().__init__("enable_mock_gpu")
        self.was_enabled = "DGPUOPT_MOCK_GPUS" in os.environ

    def execute(self) -> bool:
        """
        Enable mock GPU mode.

        Returns:
            Success status
        """
        try:
            # Set environment variable for mock mode
            os.environ["DGPUOPT_MOCK_GPUS"] = "1"
            self.logger.info("Mock GPU mode enabled")

            # Publish result
            self._publish_result(True)

            return True
        except Exception as e:
            error_service.handle_error(e, level="ERROR", title="Mock GPU Error",
                                    context={"operation": "enable_mock_gpu"})
            return False

    def undo(self) -> bool:
        """
        Disable mock GPU mode if it wasn't enabled before.

        Returns:
            Success status
        """
        try:
            if not self.was_enabled and "DGPUOPT_MOCK_GPUS" in os.environ:
                del os.environ["DGPUOPT_MOCK_GPUS"]
                self.logger.info("Mock GPU mode disabled")

            # Publish result
            self._publish_result(True)

            return True
        except Exception as e:
            error_service.handle_error(e, level="ERROR", title="Mock GPU Error",
                                    context={"operation": "disable_mock_gpu"})
            return False