"""
dualgpuopt.ui.neon
Neon‑style reusable widgets & styling helpers.
"""
from __future__ import annotations
import ttkbootstrap as ttk
from ttkbootstrap import utility
import tkinter as tk
import time, math

# ---------- Theme bootstrap ----------
def init_theme(style: ttk.Style):
    style.theme_use("darkly")                            # base dark
    accent = "#9B59B6"                                   # neon purple
    style.configure(".", font=("Inter", 10))
    style.configure("Card.TFrame", background="#2E1D47", padding=12)
    style.configure("Title.TLabel", font=("Inter SemiBold", 14))
    style.configure("Prompt.TEntry", fieldbackground="#221638",
                    borderwidth=0, foreground="#E6E6E6",
                    insertcolor="#E6E6E6", padding=8)
    style.map("TNotebook.Tab",
              background=[("selected", "#371B59")],
              foreground=[("selected", "white")])

# ---------- neon hover button ----------
class NeonButton(ttk.Button):
    def __init__(self, master, text, **kw):
        super().__init__(master, text=text, bootstyle="info-outline", **kw)
        self._normal = "#9B59B6"; self._hover = "#BF7DE0"
        self.bind("<Enter>", lambda *_: self.configure(bootstyle="info"))
        self.bind("<Leave>", lambda *_: self.configure(bootstyle="info-outline"))

# ---------- smooth gradient bar ----------
class GradientBar(ttk.Canvas):
    def __init__(self, master, w=260, h=14, **kw):
        super().__init__(master, width=w, height=h, highlightthickness=0, **kw)
        self._w, self._h, self._val, self._tar = w, h, 0., 0.
        self._grad = utility.gradient((55,242,190), (228,54,207), w)
        self._img = utility.gradient_image(1, h, self._grad)
        self._img_id = self.create_image(0,0,anchor="nw",image=self._img)
        self._last = time.perf_counter(); self.after(16,self._tick)

    def set(self, pct: float): self._tar = max(0., min(pct,100.))
    def _tick(self):
        now = time.perf_counter(); step = (now-self._last)*120
        self._last = now
        if abs(self._val-self._tar)>.3:
            self._val += math.copysign(step, self._tar-self._val)
            new_w = int(self._w*self._val/100)
            self._img = utility.gradient_image(max(new_w,1), self._h, self._grad)
            self.itemconfigure(self._img_id, image=self._img)
        self.after(16,self._tick) 