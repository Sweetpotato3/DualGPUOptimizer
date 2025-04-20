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
        self.outer = _bubble_frame(self, align)
        
        # Position the bubble with proper alignment and fill behavior
        if is_user:
            self.outer.pack(anchor="e", pady=6, padx=(50, 10), fill="x")
        else:
            self.outer.pack(anchor="w", pady=6, padx=(10, 50), fill="x")



































































































































        # Create content area with a Frame to hold both HTML and resize handle
        content_frame = ttk.Frame(self.outer)
        content_frame.pack(fill="both", expand=True)
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Create the HTML content widget
        self.html = HTMLLabel(content_frame, html=text_md, width=0, background=self.outer.cget("background"))
        self.html.grid(row=0, column=0, sticky="nsew")
        
        # Add resize handle in the bottom right
        resize_style = "info.TButton" if not is_user else "secondary.TButton"
        self.resize_handle = ttk.Button(content_frame, text="↔", width=2, style=resize_style)
        self.resize_handle.grid(row=1, column=0, sticky="se", padx=2, pady=2)
        
        # Track original and current height for resizing
        self.original_height = None
        self.current_height = None
        
        # Bind drag events for resizing
        self.resize_handle.bind("<ButtonPress-1>", self._start_resize)
        self.resize_handle.bind("<B1-Motion>", self._resize)
        self.resize_handle.bind("<ButtonRelease-1>", self._end_resize)
        
        # Bind to window resize for responsive layout adjustments
        self.bind("<Configure>", self._on_resize)
    
    def _start_resize(self, event):
        """Start tracking resize operation"""
        self.resize_y = event.y
        # Store current height
        self.current_height = self.html.winfo_height()
        if not self.original_height:
            self.original_height = self.current_height
    
    def _resize(self, event):
        """Handle resize during mouse drag"""
        diff_y = event.y - self.resize_y
        # Calculate new height and apply min/max constraints
        new_height = max(50, min(500, self.current_height + diff_y))
        self.html.configure(height=new_height)
    
    def _end_resize(self, event):
        """End resize operation"""
        # Store new height
        self.current_height = self.html.winfo_height()
    
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
    
    def reset_size(self):
        """Reset to original size"""
        if self.original_height:
            self.html.configure(height=self.original_height)
            self.current_height = self.original_height 