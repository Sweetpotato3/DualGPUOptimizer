"""
pystray icon – right‑click → show, Quit; idle checker warning.
"""
from __future__ import annotations
import threading, time, pathlib, sys
import pystray
from PIL import Image, ImageDraw
from dualgpuopt.telemetry import start_stream

def _icon_img() -> Image.Image:
    im = Image.new("RGBA", (64,64), (0,0,0,0))
    d = ImageDraw.Draw(im)
    d.rectangle((8,40,56,56), fill="#33ff55")
    d.rectangle((8,24,32,40), fill="#00b0ff")
    return im

def init_tray(app_frame):
    stream_q = start_stream(5.0)
    icon = pystray.Icon("dualgpu", _icon_img(), "DualGPU Optimiser")

    def on_show(icon, item):
        app_frame.master.deiconify()
    def on_quit(icon, item):
        icon.stop(); sys.exit()
    icon.menu = pystray.Menu(
        pystray.MenuItem("Show", on_show),
        pystray.MenuItem("Quit", on_quit),
    )

    def watcher():
        idle_for = 0
        while True:
            tele = stream_q.get()
            load = max(tele.load)
            if load < 30:
                idle_for += 5
                if idle_for >= 300:
                    icon.notify("GPUs idle for 5 min – free the silicon?")
                    idle_for = 0
            else:
                idle_for = 0
    threading.Thread(target=watcher, daemon=True).start()
    threading.Thread(target=icon.run, daemon=True).start() 