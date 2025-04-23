from __future__ import annotations
from PySide6.QtCore import QThread, Signal
import subprocess, re, json, time, shlex, os, sys, signal

TOK_RE = re.compile(r"tok/s:(\d+\.\d+).*?loss:(\d+\.\d+)")
PCT_RE = re.compile(r"Epoch (\d+)/(\d+) \| .*? (\d+)%")

class TrainerWorker(QThread):
    progress   = Signal(int, float, float)   # % , tok/s , loss
    log_line   = Signal(str)
    finished   = Signal(bool)

    def __init__(self, *, base_model, dataset, epochs, per_device_batch):
        super().__init__()
        self.cmd = (
            f"{shlex.quote(sys.executable)} -m dualgpuopt.scripts.train_qlora "
            f"--base_model {shlex.quote(base_model)} "
            f"--dataset_path {shlex.quote(dataset)} "
            f"--output_dir checkpoints/legal-lora "
            f"--epochs {epochs}"
        )
        os.environ["PER_DEVICE_BATCH"] = str(per_device_batch)
        self._stop = False

    def request_stop(self): self._stop = True

    def run(self):
        proc = subprocess.Popen(self.cmd, shell=True, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in proc.stdout:
            self.log_line.emit(line.rstrip())
            if m := TOK_RE.search(line):
                tok_s, loss = map(float, m.groups())
            else:
                tok_s = loss = float("nan")
            if m := PCT_RE.search(line):
                done, total, pct = map(int, m.groups())
                self.progress.emit(pct, tok_s, loss)
            if self._stop:
                proc.send_signal(signal.SIGINT)
        ok = proc.wait() == 0
        self.finished.emit(ok) 