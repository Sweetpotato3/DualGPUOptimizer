"""
Non‑blocking subprocess wrapper + log streamer for llama.cpp / vLLM
"""
from __future__ import annotations
import subprocess, threading, queue, pathlib, shlex


class Runner:
    def __init__(self, cmd: str, workdir: str | pathlib.Path = ".") -> None:
        self.cmd = cmd
        self.proc: subprocess.Popen | None = None
        self.q: "queue.Queue[str]" = queue.Queue()
        self.cwd = pathlib.Path(workdir)

    def start(self) -> None:
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
        assert self.proc and self.proc.stdout
        for line in self.proc.stdout:
            self.q.put(line.rstrip("\n"))
        self.proc.wait()

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
