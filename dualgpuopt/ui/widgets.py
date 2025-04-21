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

# ---------- Simple progress bar for compatibility ----------
class GradientProgress(ttk.Frame):
    """A simple progress bar widget that avoids compatibility issues.

    Implements a basic progress bar with text display.
    """
    def __init__(self, master, width=220, height=16, **kw):
        """Initialize a simple progress bar."""
        super().__init__(master, width=width, height=height, **kw)

        # Initialize variables
        self._val = 0
        self._target = 0

        # Create a label to display the percentage
        self.label = ttk.Label(self, text="0%", anchor="center")
        self.label.pack(fill="both", expand=True)

        # Start animation
        self._last = time.perf_counter()
        self.after(50, self._tick)

    def set(self, percent: float):
        """Set the progress value (0-100)."""
        self._target = max(0, min(percent, 100))

    def _update_display(self):
        """Update the progress display."""
        # Update the label text
        self.label.configure(text=f"{int(self._val)}%")

        # Update the label color based on value
        if self._val < 30:
            self.label.configure(foreground="green")
        elif self._val < 70:
            self.label.configure(foreground="orange")
        else:
            self.label.configure(foreground="red")

    def _tick(self):
        """Update animation tick."""
        now = time.perf_counter()
        dt = min(now - self._last, 0.05)
        self._last = now

        if abs(self._val - self._target) > 0.5:
            # Smoothly animate toward target
            self._val += math.copysign(dt * 100, self._target - self._val)
            self._update_display()

        self.after(50, self._tick)

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