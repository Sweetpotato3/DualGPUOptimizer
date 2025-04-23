"""
Process monitoring utilities for model execution.

This module handles monitoring and management of running model processes.
"""
from __future__ import annotations

import logging
import subprocess
import threading
import time
from typing import Callable, Optional

from dualgpuopt.services.event_service import event_bus


class ProcessMonitor:
    """Monitors running model processes and their resource usage."""

    def __init__(self) -> None:
        """Initialize the process monitor."""
        self.logger = logging.getLogger("dualgpuopt.gui.launcher.process")
        self.active_monitors: dict[str, threading.Thread] = {}
        self.stop_events: dict[str, threading.Event] = {}
        self.processes: dict[str, subprocess.Popen] = {}

    def start_monitoring(
        self,
        process_id: str,
        process: subprocess.Popen,
        on_exit: Optional[Callable[[str, int], None]] = None,
        interval: float = 1.0,
    ) -> bool:
        """
        Start monitoring a process.

        Args:
        ----
            process_id: ID for the process
            process: Subprocess Popen object
            on_exit: Callback to execute when process exits
            interval: Monitoring interval in seconds

        Returns:
        -------
            True if monitoring started, False otherwise

        """
        if process_id in self.active_monitors:
            self.logger.warning(f"Already monitoring process: {process_id}")
            return False

        # Create stop event
        stop_event = threading.Event()
        self.stop_events[process_id] = stop_event

        # Store process
        self.processes[process_id] = process

        # Create and start monitor thread
        monitor_thread = threading.Thread(
            target=self._monitor_process,
            args=(process_id, process, stop_event, on_exit, interval),
            daemon=True,
        )
        monitor_thread.start()

        # Store monitor thread
        self.active_monitors[process_id] = monitor_thread

        self.logger.info(f"Started monitoring process: {process_id} (PID: {process.pid})")
        return True

    def stop_monitoring(self, process_id: str) -> bool:
        """
        Stop monitoring a process.

        Args:
        ----
            process_id: ID of the process to stop monitoring

        Returns:
        -------
            True if stopped, False if not found

        """
        if process_id not in self.stop_events:
            self.logger.warning(f"Process not found for monitoring: {process_id}")
            return False

        # Signal thread to stop
        self.stop_events[process_id].set()

        # Wait for thread to exit (with timeout)
        self.active_monitors[process_id].join(timeout=2.0)

        # Clean up
        del self.stop_events[process_id]
        del self.active_monitors[process_id]
        if process_id in self.processes:
            del self.processes[process_id]

        self.logger.info(f"Stopped monitoring process: {process_id}")
        return True

    def terminate_process(self, process_id: str) -> bool:
        """
        Terminate a running process.

        Args:
        ----
            process_id: ID of the process to terminate

        Returns:
        -------
            True if terminated, False if not found

        """
        if process_id not in self.processes:
            self.logger.warning(f"Process not found for termination: {process_id}")
            return False

        process = self.processes[process_id]
        try:
            process.terminate()

            # Give process time to terminate gracefully
            terminated = False
            for _ in range(5):
                if process.poll() is not None:
                    terminated = True
                    break
                time.sleep(0.5)

            # Force kill if still running
            if not terminated:
                self.logger.warning(f"Process did not terminate gracefully, killing: {process_id}")
                process.kill()

            # Stop monitoring
            self.stop_monitoring(process_id)

            self.logger.info(f"Terminated process: {process_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error terminating process {process_id}: {e}")
            return False

    def _monitor_process(
        self,
        process_id: str,
        process: subprocess.Popen,
        stop_event: threading.Event,
        on_exit: Optional[Callable[[str, int], None]],
        interval: float,
    ) -> None:
        """
        Monitor a process until it exits or monitoring is stopped.

        Args:
        ----
            process_id: ID of the process
            process: Subprocess Popen object
            stop_event: Event to signal monitoring should stop
            on_exit: Callback to execute when process exits
            interval: Monitoring interval in seconds

        """
        self.logger.debug(f"Starting monitor thread for process: {process_id}")

        while not stop_event.is_set():
            # Check if process is still running
            return_code = process.poll()
            if return_code is not None:
                # Process has exited
                self.logger.info(f"Process {process_id} exited with code: {return_code}")

                # Execute callback if provided
                if on_exit:
                    try:
                        on_exit(process_id, return_code)
                    except Exception as e:
                        self.logger.error(f"Error in process exit callback: {e}")

                # Publish event
                event_bus.publish(
                    "process_exited",
                    {
                        "process_id": process_id,
                        "return_code": return_code,
                    },
                )

                # Remove from processes
                if process_id in self.processes:
                    del self.processes[process_id]

                # Exit the monitor
                break

            # Read process output for logging if available
            self._read_process_output(process)

            # Wait for interval or until stop event is set
            stop_event.wait(interval)

    def _read_process_output(self, process: subprocess.Popen) -> None:
        """
        Read and log process output if available.

        Args:
        ----
            process: Subprocess Popen object

        """
        # Only try to read if stdout/stderr are pipes
        if process.stdout and hasattr(process.stdout, "readline"):
            try:
                line = process.stdout.readline()
                if line:
                    self.logger.debug(
                        f"Process output: {line.decode('utf-8', errors='replace').strip()}"
                    )
            except Exception:
                pass

        if process.stderr and hasattr(process.stderr, "readline"):
            try:
                line = process.stderr.readline()
                if line:
                    self.logger.warning(
                        f"Process error: {line.decode('utf-8', errors='replace').strip()}"
                    )
            except Exception:
                pass
