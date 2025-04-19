"""
NVML‑based polling generator: yield dict every `interval` seconds.
"""
from __future__ import annotations
import time, dataclasses as dc, queue, threading
from typing import Dict, List
from dualgpuopt.gpu_info import probe_gpus, GPU

@dc.dataclass(slots=True)
class Telemetry:
    ts: float
    load: List[int]     # %
    mem_used: List[int] # MiB
    pcie_rx: List[int]  # KiB/s
    pcie_tx: List[int]

def _collect() -> Telemetry:
    gpus = probe_gpus()
    load, mem = [], []
    rx, tx   = [], []
    import pynvml as nv
    nv.nvmlInit()
    for g in gpus:
        h = nv.nvmlDeviceGetHandleByIndex(g.index)
        util = nv.nvmlDeviceGetUtilizationRates(h)
        load.append(util.gpu)
        mem.append(g.mem_total - g.mem_free)
        bw  = nv.nvmlDeviceGetPcieThroughput(h, nv.NVML_PCIE_UTIL_RX_BYTES)
        bw2 = nv.nvmlDeviceGetPcieThroughput(h, nv.NVML_PCIE_UTIL_TX_BYTES)
        rx.append(bw)
        tx.append(bw2)
    nv.nvmlShutdown()
    return Telemetry(time.time(), load, mem, rx, tx)

def start_stream(interval: float=1.0) -> "queue.Queue[Telemetry]":
    q: "queue.Queue[Telemetry]" = queue.Queue()
    def run() -> None:
        while True:
            q.put(_collect())
            time.sleep(interval)
    th = threading.Thread(target=run, daemon=True)
    th.start()
    return q 