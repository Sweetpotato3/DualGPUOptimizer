"""
Non‑blocking subprocess wrapper + log streamer for llama.cpp / vLLM
"""
from __future__ import annotations

import pathlib
import queue
import shlex
import subprocess
import threading
from typing import Optional


class Runner:
    def __init__(self, cmd: str, workdir: str | pathlib.Path = ".") -> None:
        """
        Initialize a Runner for managing subprocess execution.

        Args:
        ----
            cmd: Command string to execute
            workdir: Working directory for command execution

        """
        self.cmd = cmd
        self.proc: Optional[subprocess.Popen] = None
        self.q: queue.Queue[str] = queue.Queue()
        self.cwd = pathlib.Path(workdir)

    def start(self) -> None:
        """
        Start the subprocess if not already running.
        Output lines are streamed to internal queue.
        """
        if self.proc:
            return

        self.proc = subprocess.Popen(
            shlex.split(self.cmd),
            cwd=self.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self) -> None:
        """
        Internal method to pump output lines from subprocess
        to the queue for non-blocking reading.
        """
        assert self.proc and self.proc.stdout
        for line in self.proc.stdout:
            self.q.put(line.rstrip("\n"))
        self.proc.wait()

    def stop(self) -> None:
        """
        Terminate the subprocess gracefully if running.
        """
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()

    def is_running(self) -> bool:
        """
        Check if the subprocess is still running.

        Returns
        -------
            bool: True if process is running, False otherwise

        """
        return self.proc is not None and self.proc.poll() is None
