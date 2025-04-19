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
    load: List[int]           # GPU utilization %
    mem_used: List[int]       # MiB
    pcie_rx: List[int]        # KiB/s
    pcie_tx: List[int]        # KiB/s
    temperature: List[int]    # °C
    power_usage: List[float]  # Watts
    memory_util: List[int]    # Memory utilization %
    fan_speed: List[int]      # Fan speed %
    graphics_clock: List[int] # MHz
    memory_clock: List[int]   # MHz

def _collect() -> Telemetry:
    gpus = probe_gpus()
    load, mem = [], []
    rx, tx = [], []
    temperature = []
    power_usage = []
    memory_util = []
    fan_speed = []
    graphics_clock = []
    memory_clock = []
    
    import pynvml as nv
    nv.nvmlInit()
    
    try:
        for g in gpus:
            h = nv.nvmlDeviceGetHandleByIndex(g.index)
            
            # Basic metrics (always collected)
            util = nv.nvmlDeviceGetUtilizationRates(h)
            load.append(util.gpu)
            mem.append(g.mem_used)
            memory_util.append(util.memory)
            
            # PCIe throughput
            try:
                bw = nv.nvmlDeviceGetPcieThroughput(h, nv.NVML_PCIE_UTIL_RX_BYTES)
                bw2 = nv.nvmlDeviceGetPcieThroughput(h, nv.NVML_PCIE_UTIL_TX_BYTES)
                rx.append(bw)
                tx.append(bw2)
            except Exception:
                rx.append(0)
                tx.append(0)
                
            # Temperature
            try:
                temp = nv.nvmlDeviceGetTemperature(h, nv.NVML_TEMPERATURE_GPU)
                temperature.append(temp)
            except Exception:
                temperature.append(0)
                
            # Power usage
            try:
                power = nv.nvmlDeviceGetPowerUsage(h) / 1000.0  # Convert from mW to W
                power_usage.append(round(power, 1))
            except Exception:
                power_usage.append(0.0)
                
            # Fan speed
            try:
                fan = nv.nvmlDeviceGetFanSpeed(h)
                fan_speed.append(fan)
            except Exception:
                fan_speed.append(0)
                
            # Clock speeds
            try:
                g_clock = nv.nvmlDeviceGetClockInfo(h, nv.NVML_CLOCK_GRAPHICS)
                graphics_clock.append(g_clock)
                
                m_clock = nv.nvmlDeviceGetClockInfo(h, nv.NVML_CLOCK_MEM)
                memory_clock.append(m_clock)
            except Exception:
                graphics_clock.append(0)
                memory_clock.append(0)
    finally:
        nv.nvmlShutdown()
        
    return Telemetry(
        time.time(),
        load,
        mem,
        rx,
        tx,
        temperature,
        power_usage,
        memory_util,
        fan_speed,
        graphics_clock,
        memory_clock
    )

def start_stream(interval: float=1.0) -> "queue.Queue[Telemetry]":
    q: "queue.Queue[Telemetry]" = queue.Queue()
    def run() -> None:
        while True:
            q.put(_collect())
            time.sleep(interval)
    th = threading.Thread(target=run, daemon=True)
    th.start()
    return q 