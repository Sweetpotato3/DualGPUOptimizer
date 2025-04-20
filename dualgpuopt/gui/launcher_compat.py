"""
Backward compatibility layer for launcher.py

This module provides the original API from launcher.py but imports functionality
from the refactored modules. This allows existing code to continue working
while we transition to the new modular structure.
"""
from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import queue
import threading
import subprocess
from typing import Dict, List, Optional, Any

# Import refactored components
from dualgpuopt.gui.launcher.ui_components import LauncherTab
from dualgpuopt.gui.launcher.launch_controller import LaunchController
from dualgpuopt.gui.launcher.process_monitor import ProcessMonitor

# Try to import advanced features
try:
    from dualgpuopt.batch.smart_batch import optimize_batch_size, BatchStats
    from dualgpuopt.ctx_size import calc_max_ctx, model_params_from_name
    from dualgpuopt.layer_balance import rebalance
    from dualgpuopt.vram_reset import reset_vram, ResetMethod, ResetResult
    from dualgpuopt.mpolicy import autocast, scaler
    from dualgpuopt.memory_monitor import get_memory_monitor, MemoryAlertLevel, MemoryAlert
    from dualgpuopt.model_profiles import apply_profile, get_model_profile
    from dualgpuopt.error_handler import get_error_handler, show_error_dialog, ErrorSeverity, ErrorCategory
    from dualgpuopt.telemetry import get_telemetry_service
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Advanced optimization modules not available: {e}")
    ADVANCED_FEATURES_AVAILABLE = False

logger = logging.getLogger("DualGPUOpt.LauncherCompat")


class ModelRunner:
    """
    Backward compatibility wrapper for ProcessMonitor.

    This class maintains the same API as the original ModelRunner class
    but delegates to the refactored ProcessMonitor.
    """

    def __init__(self, log_queue):
        """
        Initialize model runner with log queue.

        Args:
            log_queue: Queue for log messages
        """
        self.log_queue = log_queue
        self.process_monitor = ProcessMonitor()
        self.process = None
        self.running = False
        self.process_id = None
        self.logger = logging.getLogger("DualGPUOpt.ModelRunner")

    def start(self, command, env=None, cwd=None, use_layer_balancing=False, use_mixed_precision=False):
        """
        Start model process.

        Args:
            command: Command string to execute
            env: Environment variables
            cwd: Working directory
            use_layer_balancing: Whether to use layer balancing
            use_mixed_precision: Whether to use mixed precision

        Returns:
            True if started successfully, False otherwise
        """
        if self.process and self.process.poll() is None:
            self.log_queue.put("Error: Model already running")
            return False

        # Reset state
        self.running = True

        # Add layer balancing and mixed precision to env if specified
        full_env = os.environ.copy()
        if env:
            full_env.update(env)

        if use_layer_balancing:
            full_env["LAYER_BALANCE"] = "1"

        if use_mixed_precision:
            full_env["MIXED_PRECISION"] = "1"

        # Reset VRAM if memory monitor is enabled
        if ADVANCED_FEATURES_AVAILABLE and full_env.get("MEMORY_MONITOR") == "1":
            try:
                reset_vram()
                self.log_queue.put("VRAM reset completed")
            except Exception as e:
                self.log_queue.put(f"Warning: VRAM reset failed: {str(e)}")

        # Log the command
        self.log_queue.put(f"Executing: {command}")

        try:
            # Start the process
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=full_env,
                cwd=cwd,
                shell=True
            )

            self.process = process

            # Generate a unique ID
            self.process_id = f"model_run_{id(process)}"

            # Start monitoring
            def on_output(line):
                self.log_queue.put(line)

            def on_exit(pid, code):
                self.running = False
                exit_msg = f"Process exited with code {code}"
                self.log_queue.put(exit_msg)

            self.process_monitor.start_monitoring(
                self.process_id,
                process,
                on_exit=on_exit
            )

            # Start output reader thread
            threading.Thread(
                target=self._read_output,
                daemon=True
            ).start()

            # Monitor OOM if requested
            if ADVANCED_FEATURES_AVAILABLE and full_env.get("MEMORY_MONITOR") == "1":
                self._monitor_oom()

            return True

        except Exception as e:
            self.running = False
            error_msg = f"Error starting process: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.log_queue.put(error_msg)
            return False

    def stop(self):
        """Stop the running model process."""
        self.running = False

        if self.process_id:
            self.process_monitor.terminate_process(self.process_id)
            self.log_queue.put("Process stopped")
            self.process_id = None
            self.process = None

    def _read_output(self):
        """Read and process output from the model process."""
        if not self.process or not self.process.stdout:
            return

        try:
            for line in iter(self.process.stdout.readline, ''):
                if not self.running:
                    break

                # Skip empty lines
                if not line.strip():
                    continue

                # Check for OOM errors
                if 'out of memory' in line.lower() or 'cuda error' in line.lower():
                    self._handle_oom_error(line)

                # Add to log queue
                self.log_queue.put(line.strip())

            # Process completed
            if self.process and self.process.poll() is not None:
                exit_code = self.process.returncode
                if exit_code != 0:
                    self.log_queue.put(f"Process exited with code {exit_code}")
                else:
                    self.log_queue.put("Process completed successfully")

                self.running = False

        except Exception as e:
            self.log_queue.put(f"Error reading process output: {str(e)}")
            self.running = False

    def _handle_oom_error(self, error_line):
        """
        Handle out-of-memory errors.

        Args:
            error_line: Error line from process
        """
        self.log_queue.put("CRITICAL: GPU out of memory detected!")

        # Try to recover by clearing CUDA cache
        try:
            import torch
            if torch.cuda.is_available():
                self.log_queue.put("Attempting to clear CUDA cache...")
                torch.cuda.empty_cache()
                self.log_queue.put("CUDA cache cleared")
        except (ImportError, Exception) as e:
            self.log_queue.put(f"Failed to clear CUDA cache: {str(e)}")

        # Log error details
        self.logger.error(f"OOM error detected: {error_line}")

    def _monitor_oom(self):
        """Register callback for memory pressure and monitor OOM conditions."""
        if not ADVANCED_FEATURES_AVAILABLE:
            return

        try:
            memory_monitor = get_memory_monitor()

            def handle_memory_alert(alert):
                """Handle memory pressure event."""
                gpu_id = alert.gpu_id
                used_mb = alert.context.get("used_memory", 0) / (1024 * 1024)
                total_mb = alert.context.get("total_memory", 0) / (1024 * 1024)
                pressure_pct = (used_mb / total_mb) * 100 if total_mb > 0 else 0

                self.log_queue.put(
                    f"WARNING: High memory pressure on GPU {gpu_id}: "
                    f"{used_mb:.0f}MB/{total_mb:.0f}MB ({pressure_pct:.1f}%)"
                )

                # Try to alleviate pressure by clearing CUDA cache
                try:
                    import torch
                    if torch.cuda.is_available():
                        self.log_queue.put("Clearing CUDA cache to prevent OOM...")
                        torch.cuda.empty_cache()
                except (ImportError, Exception):
                    pass

            # Register callback for high memory usage
            memory_monitor.register_alert_callback(MemoryAlertLevel.WARNING, handle_memory_alert)

        except (ImportError, Exception) as e:
            self.logger.warning(f"Memory monitor not available for OOM prevention: {e}")

    def is_running(self):
        """
        Check if process is running.

        Returns:
            True if running, False otherwise
        """
        if not self.process:
            return False

        return self.process.poll() is None


# Re-export LauncherTab from the refactored module
# The original launcher.py module just needs to import this file and re-export