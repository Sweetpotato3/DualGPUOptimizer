"""
dualgpuopt.ui.widgets
Reusable neon‑styled ttkbootstrap widgets.
"""
from __future__ import annotations
import tkinter as tk
import ttkbootstrap as ttk
import time, math

# ---------- Custom gradient utility functions for compatibility ----------
def _create_gradient_data(start_rgb, end_rgb, width):
    """Create gradient color data from start to end color across given width."""
    result = []
    sr, sg, sb = start_rgb
    er, eg, eb = end_rgb
    
    for i in range(width):
        # Calculate color for this position
        factor = i / (width - 1) if width > 1 else 0
        r = int(sr + factor * (er - sr))
        g = int(sg + factor * (eg - sg))
        b = int(sb + factor * (eb - sb))
        result.append((r, g, b))
    
    return result

def _rgb_to_hex(rgb_tuple):
    """Convert RGB tuple to hex color string."""
    r, g, b = rgb_tuple
    return f'#{r:02x}{g:02x}{b:02x}'

# ---------- Gradient progress bar (GPU util, VRAM) ----------
class GradientProgress(ttk.Frame):
    """A custom gradient progress bar widget.
    
    Implements an animated progress bar with custom gradient colors.
    """
    def __init__(self, master, width=220, height=16, **kw):
        super().__init__(master, **kw)
        self._w, self._h = width, height
        self._val, self._target = 0, 0
        
        # Create gradient colors
        self._start_color = (48, 255, 144)   # Green
        self._end_color = (255, 64, 224)     # Purple
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(self, width=width, height=height, 
                              highlightthickness=0, bd=0)
        self.canvas.pack(fill='both', expand=True)
        
        # Create rectangle for background
        self.canvas.create_rectangle(0, 0, width, height, 
                                   fill='#202020', outline='')
        
        # Create progress rectangle (initially width 1)
        self._rect_id = self.canvas.create_rectangle(
            0, 0, 1, height, fill=self._rgb_to_hex(self._start_color), outline='')
        
        self._last = time.perf_counter()
        self.after(16, self._tick)

    def set(self, percent: float):
        """Set the progress value (0-100)."""
        self._target = max(0, min(percent, 100))
        
    def _rgb_to_hex(self, rgb_tuple):
        """Convert RGB tuple to hex color string."""
        r, g, b = rgb_tuple
        return f'#{r:02x}{g:02x}{b:02x}'

    def _tick(self):
        """Update animation tick."""
        now = time.perf_counter()
        dt = min(now - self._last, 0.05)
        self._last = now
        
        if abs(self._val - self._target) > 0.5:
            # Smoothly animate toward target
            self._val += math.copysign(dt * 100, self._target - self._val)
            new_w = int(self._w * self._val / 100)
            
            # Update rectangle width and color
            self.canvas.coords(self._rect_id, 0, 0, new_w, self._h)
            
            # Calculate color based on percentage
            if new_w > 1:
                factor = self._val / 100
                r = int(self._start_color[0] + factor * (self._end_color[0] - self._start_color[0]))
                g = int(self._start_color[1] + factor * (self._end_color[1] - self._start_color[1]))
                b = int(self._start_color[2] + factor * (self._end_color[2] - self._start_color[2]))
                self.canvas.itemconfig(self._rect_id, fill=self._rgb_to_hex((r, g, b)))
        
        self.after(16, self._tick)

# ---------- Hover‑glow button ----------
class NeonButton(ttk.Button):
    """Button that glows on hover with a neon effect."""
    
    def __init__(self, master, text, **kw):
        super().__init__(master, text=text, bootstyle="info-outline", **kw)
        self.bind("<Enter>", self._hover)
        self.bind("<Leave>", self._normal)

    def _hover(self, *_):
        """Change style on mouse hover."""
        self.configure(bootstyle="info")

    def _normal(self, *_):
        """Reset style when mouse leaves."""
        self.configure(bootstyle="info-outline") 