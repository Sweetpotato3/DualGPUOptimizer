"""
Launch controller for managing model execution across multiple GPUs.

This module contains the core launch logic for executing models with
optimized parameters on multiple GPUs.
"""
from __future__ import annotations

import logging
import os
import subprocess
import threading
import time
import uuid
from typing import Any, Callable, Optional

from dualgpuopt.gpu_info import GPU
from dualgpuopt.gui.launcher.model_validation import ModelValidator
from dualgpuopt.gui.launcher.parameter_resolver import ParameterResolver

# Import process monitor
from dualgpuopt.gui.launcher.process_monitor import ProcessMonitor
from dualgpuopt.services.event_service import event_bus

# Try to import advanced optimization modules
try:
    from dualgpuopt.batch.smart_batch import optimize_batch_size
    from dualgpuopt.ctx_size import calc_max_ctx, model_params_from_name
    from dualgpuopt.error_handler import ErrorCategory, ErrorSeverity, get_error_handler
    from dualgpuopt.layer_balance import rebalance
    from dualgpuopt.memory_monitor import MemoryAlert, MemoryAlertLevel, get_memory_monitor
    from dualgpuopt.model_profiles import apply_profile, get_model_profile
    from dualgpuopt.mpolicy import autocast, scaler
    from dualgpuopt.telemetry import get_telemetry_service
    from dualgpuopt.vram_reset import ResetMethod, ResetResult, reset_vram

    ADVANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Advanced optimization modules not available: {e}")
    ADVANCED_FEATURES_AVAILABLE = False


class LaunchController:
    """Controller for launching models on multiple GPUs."""

    def __init__(self, gpus: list[GPU] = None) -> None:
        """
        Initialize the launch controller.

        Args:
        ----
            gpus: List of GPU objects to use for launching models
        """
        self.gpus = gpus or []
        self.logger = logging.getLogger("dualgpuopt.gui.launcher.controller")
        self.active_processes: dict[str, subprocess.Popen] = {}

        # Create component instances
        self.process_monitor = ProcessMonitor()
        self.parameter_resolver = ParameterResolver()
        self.model_validator = ModelValidator()

        # Initialize memory monitor if available
        self.memory_monitor = None
        if ADVANCED_FEATURES_AVAILABLE:
            try:
                self.memory_monitor = get_memory_monitor()
            except Exception as e:
                self.logger.warning(f"Error initializing memory monitor: {e}")

        # Register event handlers
        self._register_event_handlers()

    def _register_event_handlers(self) -> None:
        """Register event handlers."""
        event_bus.subscribe("gpu_list_updated", self._handle_gpu_update)

    def _handle_gpu_update(self, data: dict[str, Any]) -> None:
        """
        Handle GPU list updates.

        Args:
        ----
            data: Event data containing updated GPU list
        """
        if "gpus" in data:
            self.gpus = data["gpus"]
            self.logger.debug(f"Updated GPU list in launcher: {len(self.gpus)} GPUs")

    def launch_model(
        self,
        model_path: str,
        framework: str,
        parameters: dict[str, Any],
        env_vars: Optional[dict[str, str]] = None,
        on_output: Optional[Callable[[str], None]] = None,
        on_exit: Optional[Callable[[str, int], None]] = None,
        cwd: Optional[str] = None,
    ) -> tuple[bool, str, Optional[str]]:
        """
        Launch a model with the specified parameters.

        Args:
        ----
            model_path: Path to the model file
            framework: Framework to use (llama.cpp, vllm)
            parameters: Launch parameters
            env_vars: Additional environment variables
            on_output: Callback for process output
            on_exit: Callback for process exit
            cwd: Working directory

        Returns:
        -------
            Tuple of (success, process_id, error_message)
        """
        # Validate parameters
        valid, error_msg = self.model_validator.validate_launch_parameters(
            model_path,
            framework,
            parameters,
            self.gpus,
        )

        if not valid:
            self.logger.error(f"Invalid launch parameters: {error_msg}")
            return False, "", error_msg

        # Generate command based on framework
        command = ""
        if framework.lower() == "llama.cpp":
            command = self.parameter_resolver.generate_llama_command(parameters)
        elif framework.lower() == "vllm":
            command = self.parameter_resolver.generate_vllm_command(parameters)
        else:
            error_msg = f"Unsupported framework: {framework}"
            self.logger.error(error_msg)
            return False, "", error_msg

        # Set up environment variables
        full_env = os.environ.copy()
        if env_vars:
            full_env.update(env_vars)

        # Add model path to environment
        full_env["MODEL_PATH"] = model_path

        # Apply model-specific optimizations if available
        if ADVANCED_FEATURES_AVAILABLE:
            try:
                # Apply model profile if available
                apply_profile(model_path)
                self.logger.info(f"Applied optimization profile for {os.path.basename(model_path)}")

                # Reset VRAM before launching
                if self.memory_monitor:
                    reset_vram()
                    self.logger.info("VRAM reset completed")
            except Exception as e:
                self.logger.warning(f"Error applying optimizations: {e}")

        # Generate a unique process ID
        process_id = str(uuid.uuid4())

        # Start the process
        try:
            self.logger.info(f"Launching process: {command}")

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=full_env,
                cwd=cwd,
                shell=True,
            )

            # Store process
            self.active_processes[process_id] = process

            # Start monitoring process
            self.process_monitor.start_monitoring(
                process_id,
                process,
                on_exit=on_exit,
                interval=1.0,
            )

            # Start output reader thread if callback provided
            if on_output:
                threading.Thread(
                    target=self._read_process_output,
                    args=(process, on_output),
                    daemon=True,
                ).start()

            # Publish launch event
            event_bus.publish(
                "model_launched",
                {
                    "process_id": process_id,
                    "model_path": model_path,
                    "framework": framework,
                    "parameters": parameters,
                },
            )

            return True, process_id, None

        except Exception as e:
            error_msg = f"Error launching model: {e!s}"
            self.logger.error(error_msg, exc_info=True)
            return False, "", error_msg

    def stop_model(self, process_id: str) -> bool:
        """
        Stop a running model process.

        Args:
        ----
            process_id: ID of the process to stop

        Returns:
        -------
            True if stop successful, False otherwise
        """
        if process_id not in self.active_processes:
            self.logger.warning(f"Process not found: {process_id}")
            return False

        # Terminate process using process monitor
        result = self.process_monitor.terminate_process(process_id)

        # Remove from active processes
        if result and process_id in self.active_processes:
            del self.active_processes[process_id]

        # Publish stop event
        event_bus.publish(
            "model_stopped",
            {
                "process_id": process_id,
                "result": result,
            },
        )

        return result

    def get_active_processes(self) -> dict[str, subprocess.Popen]:
        """
        Get active model processes.

        Returns
        -------
            Dictionary of active processes
        """
        return self.active_processes.copy()

    def _read_process_output(
        self, process: subprocess.Popen, callback: Callable[[str], None]
    ) -> None:
        """
        Read and process output from the model process.

        Args:
        ----
            process: Subprocess Popen object
            callback: Callback function for output lines
        """
        if not process or not process.stdout:
            return

        try:
            for line in iter(process.stdout.readline, ""):
                # Skip empty lines
                if not line.strip():
                    continue

                # Execute callback
                callback(line.strip())

                # Check for OOM or CUDA errors
                if "out of memory" in line.lower() or "cuda error" in line.lower():
                    self._handle_oom_error(line)

                # Process completed or failed
                if process.poll() is not None:
                    break

        except Exception as e:
            self.logger.error(f"Error reading process output: {e!s}", exc_info=True)

    def _handle_oom_error(self, error_line: str) -> None:
        """
        Handle out-of-memory errors.

        Args:
        ----
            error_line: Error line from process output
        """
        self.logger.error(f"OOM error detected: {error_line}")

        # Try to recover by clearing CUDA cache
        try:
            import torch

            if torch.cuda.is_available():
                self.logger.info("Clearing CUDA cache to recover from OOM")
                torch.cuda.empty_cache()
        except ImportError:
            pass

        # Publish OOM event
        event_bus.publish(
            "oom_error",
            {
                "error_line": error_line,
                "timestamp": time.time(),
            },
        )

    def estimate_memory_requirements(
        self, model_path: str, framework: str, ctx_size: int
    ) -> dict[str, Any]:
        """
        Estimate memory requirements for a model.

        Args:
        ----
            model_path: Path to model file
            framework: Framework (llama.cpp, vllm)
            ctx_size: Context size in tokens

        Returns:
        -------
            Dictionary with memory requirement estimates
        """
        if not ADVANCED_FEATURES_AVAILABLE:
            return {"error": "Advanced features not available"}

        try:
            model_name = os.path.basename(model_path).lower()

            # Extract model parameters from name
            layers, heads, kv_heads, hidden_size, moe_factor = model_params_from_name(model_name)

            # Get model size in billions of parameters
            model_size_b = self._estimate_model_size(model_name)

            # Calculate memory requirements
            token_bytes = 8  # Approximate bytes per token in KV cache
            kv_cache_mb = (ctx_size * token_bytes * layers * kv_heads * hidden_size) / (1024 * 1024)
            model_weight_mb = model_size_b * 1000  # Rough estimate

            # Get available memory
            available_memory = []
            for gpu in self.gpus:
                available_memory.append(gpu.mem_free_mb)

            return {
                "model_name": model_name,
                "parameters_b": model_size_b,
                "layers": layers,
                "heads": heads,
                "kv_heads": kv_heads,
                "hidden_size": hidden_size,
                "moe_factor": moe_factor,
                "kv_cache_mb": kv_cache_mb,
                "model_weight_mb": model_weight_mb,
                "available_memory_mb": available_memory,
                "total_required_mb": kv_cache_mb + model_weight_mb,
            }

        except Exception as e:
            self.logger.error(f"Error estimating memory requirements: {e!s}", exc_info=True)
            return {"error": str(e)}

    def _estimate_model_size(self, model_name: str) -> float:
        """
        Estimate model size in billions of parameters from name.

        Args:
        ----
            model_name: Model name or path

        Returns:
        -------
            Model size in billions of parameters
        """
        # Estimate model size based on filename patterns
        if "70b" in model_name:
            return 70.0
        elif "13b" in model_name:
            return 13.0
        elif "7b" in model_name:
            return 7.0
        elif "mixtral" in model_name:
            return 46.7  # Mixtral 8x7B
        elif "mistral" in model_name:
            return 7.0  # Mistral 7B
        elif "llama" in model_name:
            return 7.0  # Default for LLaMA if no size specified
        else:
            return 7.0  # Default fallback

    def optimize_gpu_split(self) -> str:
        """
        Calculate optimal GPU split for the available GPUs.

        Returns
        -------
            GPU split as a comma-separated string of percentages
        """
        if not self.gpus:
            return "100"

        # For single GPU, use 100%
        if len(self.gpus) == 1:
            return "100"

        # Calculate split based on available memory
        total_memory = sum(gpu.mem_free_mb for gpu in self.gpus)
        if total_memory <= 0:
            return ",".join(["50"] * len(self.gpus))

        # Calculate proportional split
        split = [int((gpu.mem_free_mb / total_memory) * 100) for gpu in self.gpus]

        # Ensure sum is 100
        while sum(split) < 100:
            split[split.index(min(split))] += 1

        while sum(split) > 100:
            split[split.index(max(split))] -= 1

        return ",".join(map(str, split))
