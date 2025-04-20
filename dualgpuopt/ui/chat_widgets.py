from __future__ import annotations
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap import utility
from tkhtmlview import HTMLLabel   # pip install tkhtmlview
import textwrap
from typing import Dict, Optional, List

try:
    from ttkbootstrap.constants import *
    from ttkbootstrap.style import Bootstyle
    TTKBOOTSTRAP_AVAILABLE = True
except ImportError:
    import tkinter.ttk as ttk
    TTKBOOTSTRAP_AVAILABLE = False

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
    """A chat bubble widget with modern styling for user and assistant messages"""
    
    def __init__(self, master, content: str, is_user: bool = False, **kwargs):
        """Initialize a chat bubble widget
        
        Args:
            master: Parent widget
            content: HTML-like formatted text content
            is_user: Whether this is a user message (True) or assistant message (False)
            **kwargs: Additional keyword arguments for the frame
        """
        # Configure the style based on whether it's a user or assistant message
        if TTKBOOTSTRAP_AVAILABLE:
            style = "primary" if is_user else "secondary"
            super().__init__(master, bootstyle=style, padding=10, **kwargs)
        else:
            super().__init__(master, padding=10, **kwargs)
            
        # Set background colors based on message type
        self.bg_color = "#371B59" if is_user else "#2E1D47"
        self.text_color = "#FFFFFF"
        
        # Create a Text widget to display the content with proper wrapping
        self.text = tk.Text(
            self, 
            wrap="word",
            width=60,
            height=4,
            font=("Inter", 10),
            bg=self.bg_color,
            fg=self.text_color,
            relief="flat",
            highlightthickness=0,
            padx=8,
            pady=6
        )
        
        # Insert the content
        self.text.insert("1.0", content)
        
        # Make the text widget read-only
        self.text.configure(state="disabled")
        
        # Adjust height based on content
        self.adjust_height()
        
        # Pack the text widget
        self.text.pack(fill="both", expand=True)
        
        # Add rounded corners and styling to the frame
        if TTKBOOTSTRAP_AVAILABLE:
            self.configure(bootstyle=f"{style}.rounded")
        
    def adjust_height(self):
        """Adjust the height of the text widget based on its content"""
        # Get the height of the content
        num_lines = int(self.text.index('end-1c').split('.')[0])
        
        # Set a minimum height of 2 lines and a maximum of 20
        height = max(2, min(num_lines, 20))
        
        # Update the text widget's height
        self.text.configure(height=height)

# The rest of your existing widget classes...

class MessageContainer(ttk.Frame):
    """Container frame for chat messages with styling."""
    
    def __init__(self, master, **kwargs):
        """Initialize a message container.
        
        Args:
            master: Parent widget
            **kwargs: Additional keyword arguments for the frame
        """
        super().__init__(master, **kwargs)
        
        # Configure grid layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Apply styling - can be customized based on your theme
        if TTKBOOTSTRAP_AVAILABLE:
            self.configure(bootstyle=DARK)
        
    def add_message(self, content: str, is_user: bool = False, **kwargs) -> Bubble:
        """Add a new message to the container.
        
        Args:
            content: Message content
            is_user: Whether this is a user message
            **kwargs: Additional keyword arguments for the message bubble
            
        Returns:
            The created message bubble
        """
        # Create a new row for the message
        row = self.grid_size()[1]
        
        # Create and configure the message bubble
        bubble = Bubble(self, content, is_user, **kwargs)
        bubble.grid(row=row, column=0, sticky="ew", padx=(10 if is_user else 20, 20 if is_user else 10), pady=5)
        
        # Return the created bubble
        return bubble 