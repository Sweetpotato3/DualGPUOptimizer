"""
Chat Compatibility Layer

Provides graceful fallbacks for chat-related dependencies like requests and sseclient.
"""
from __future__ import annotations
import logging
import tkinter as tk
from tkinter import ttk
import queue

# Configure logger
logger = logging.getLogger("DualGPUOpt.UI.ChatCompat")

# Track the status of optional dependencies
DEPENDENCIES = {
    "requests": {"available": False, "module": None},
    "sseclient": {"available": False, "module": None},
}

# Try to import optional dependencies and mark their availability
try:
    import requests
    DEPENDENCIES["requests"]["available"] = True
    DEPENDENCIES["requests"]["module"] = requests
    logger.info("requests is available")
except ImportError:
    logger.warning("requests is not installed - chat functionality will be limited")

try:
    import sseclient
    DEPENDENCIES["sseclient"]["available"] = True
    DEPENDENCIES["sseclient"]["module"] = sseclient
    logger.info("sseclient is available")
except ImportError:
    logger.warning("sseclient is not installed - chat streaming will be limited")

class MockChatTab(ttk.Frame):
    """A mock chat tab that shows installation instructions when dependencies are missing"""

    def __init__(self, master, out_q: queue.Queue):
        """Initialize the mock chat tab

        Args:
            master: Parent widget
            out_q: Output queue for messages
        """
        super().__init__(master, padding=10)
        self.out_q = out_q

        # Configure grid for responsive layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)  # Message area should expand

        # Create the message frame with instructions
        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")

        # Add explanatory text
        ttk.Label(frame, text="Chat Module Dependencies Missing",
                 font=('Arial', 16, 'bold')).pack(pady=(20, 10))

        # Create a text widget for the detailed message
        text = tk.Text(frame, wrap="word", height=15, width=60)
        text.pack(padx=20, pady=10, fill="both", expand=True)

        # Add the instructions
        message = """
The Chat functionality requires additional Python packages that are not currently installed:

Required packages:
- requests: For API communication
- sseclient-py: For streaming chat responses

To enable Chat functionality, please install these packages using pip:

```
pip install requests>=2.25.0 sseclient-py>=1.7.2
```

After installation, restart the application to use the Chat feature.

Note: You can continue to use other features of the application without these dependencies.
        """

        text.insert("1.0", message)
        text.configure(state="disabled")  # Make read-only

        # Add a button to copy the pip command
        def copy_to_clipboard():
            self.clipboard_clear()
            self.clipboard_append("pip install requests>=2.25.0 sseclient-py>=1.7.2")
            btn.configure(text="Copied!")
            self.after(2000, lambda: btn.configure(text="Copy pip command"))

        btn = ttk.Button(frame, text="Copy pip command", command=copy_to_clipboard)
        btn.pack(pady=(0, 20))

    def handle_queue(self, kind, val):
        """Stub method to handle messages from the queue

        Args:
            kind: Message type
            val: Message value
        """
        pass  # Nothing to do in mock implementation


def get_chat_tab(master, out_q: queue.Queue) -> ttk.Frame:
    """
    Get the best available chat tab implementation based on installed dependencies

    Args:
        master: Parent widget
        out_q: Output queue for messages

    Returns:
        ttk.Frame: A chat tab with the best available implementation
    """
    # Check if we have the required dependencies
    if DEPENDENCIES["requests"]["available"] and DEPENDENCIES["sseclient"]["available"]:
        # Try to import the real ChatTab
        try:
            from ..chat_tab import ChatTab
            return ChatTab(master, out_q)
        except ImportError:
            logger.warning("Failed to import ChatTab module - using mock implementation")
            return MockChatTab(master, out_q)
    else:
        # Use the mock implementation
        return MockChatTab(master, out_q)