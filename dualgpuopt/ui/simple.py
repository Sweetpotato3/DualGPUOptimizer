"""
Simple UI module for DualGPUOptimizer

Provides a basic UI that works with minimal dependencies.
Used as a fallback when more advanced UI options are not available.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
import threading
import time
import logging
import sys
from typing import Dict, Any, List, Optional

# Configure logger
logger = logging.getLogger("DualGPUOpt.UI.Simple")

class SimpleApp(ttk.Frame):
    """Simple application frame with basic functionality"""
    
    def __init__(self, parent):
        """Initialize the simple application"""
        super().__init__(parent, padding=10)
        
        # Configure grid layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Create title
        ttk.Label(self, text="DualGPUOptimizer - Simple UI", 
                 font=("Arial", 16, "bold")).grid(row=0, column=0, pady=10)
        
        # Create info frame
        info_frame = ttk.LabelFrame(self, text="Information", padding=10)
        info_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        
        # Add explanation text
        info_text = """
This is a simple fallback UI for DualGPUOptimizer.

The application is running with limited functionality due to missing dependencies.
To enable all features, please install the required dependencies:

1. Core dependencies:
   - pynvml: For GPU monitoring
   - psutil: For system monitoring
   - numpy: For optimization algorithms

2. UI dependencies:
   - ttkbootstrap: For enhanced UI
   - ttkthemes: For additional themes
   - ttkwidgets: For additional widgets

3. Optional dependencies:
   - requests and sseclient-py: For chat functionality
   - torch, torchvision, torchaudio: For advanced features

Run the following command to install all dependencies:
pip install -r requirements.txt
        """
        
        text = tk.Text(info_frame, wrap="word", height=15, width=60)
        text.pack(fill="both", expand=True, pady=5)
        text.insert("1.0", info_text)
        text.config(state="disabled")
        
        # Create button frame
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        # Add exit button
        ttk.Button(btn_frame, text="Exit", command=parent.destroy).pack(side="right")

def run_simple_ui():
    """Run the simple UI"""
    # Create root window
    root = tk.Tk()
    root.title("DualGPUOptimizer")
    root.geometry("600x400")
    
    # Create app
    app = SimpleApp(root)
    app.pack(fill="both", expand=True)
    
    # Run app
    root.mainloop()

if __name__ == "__main__":
    run_simple_ui() 