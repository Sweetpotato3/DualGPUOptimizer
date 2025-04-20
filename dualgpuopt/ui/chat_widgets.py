from __future__ import annotations
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap import utility
from tkhtmlview import HTMLLabel   # pip install tkhtmlview

# ---------- bubble style ----------
def _bubble_frame(parent, align="left", bg="#371b59") -> ttk.Frame:
    """Create a styled bubble frame
    
    Args:
        parent: Parent widget
        align: Alignment ('left' or 'right')
        bg: Background color
        
    Returns:
        Configured frame widget
    """
    # Create frame with rounded corners and padding
    f = ttk.Frame(parent, style="info.TFrame", padding=12)
    f.configure(bootstyle="info" if align == "left" else "secondary")
    
    # Make the bubble content flexible for different window sizes
    f.columnconfigure(0, weight=1)
    f.rowconfigure(0, weight=1)
    
    return f

# ---------- message bubble ----------
class Bubble(ttk.Frame):
    """A chat bubble widget that displays HTML/Markdown formatted text
    
    This widget creates message bubbles similar to modern chat applications,
    with support for different alignments and HTML/Markdown content.
    """
    def __init__(self, parent, text_md: str, is_user: bool):
        """Initialize a new chat bubble
        
        Args:
            parent: Parent widget
            text_md: HTML/Markdown formatted text content
            is_user: True if this is a user message (right-aligned)
        """
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        
        # Determine alignment based on message sender
        align = "right" if is_user else "left"
        
        # Create styled outer frame
        outer = _bubble_frame(self, align)
        
        # Position the bubble with proper alignment and fill behavior
        if is_user:
            outer.pack(anchor="e", pady=6, padx=(50, 10), fill="x")
        else:
            outer.pack(anchor="w", pady=6, padx=(10, 50), fill="x")
        
        # Create the HTML content widget
        self.html = HTMLLabel(outer, html=text_md, width=0, background=outer.cget("background"))
        self.html.pack(fill="both", expand=True)
        
        # Bind to window resize for responsive layout adjustments
        self.bind("<Configure>", self._on_resize)
    
    def _on_resize(self, event=None):
        """Handle resize events to adjust text wrapping
        
        Args:
            event: The resize event
        """
        # Update wrapping based on current size
        parent_width = self.winfo_width()
        if parent_width > 10:  # Only adjust if we have a real width
            # Set the wraplength to a percentage of the parent width
            wrap_width = int(parent_width * 0.95)  # 95% of container width
            self.html.config(wraplength=wrap_width) 