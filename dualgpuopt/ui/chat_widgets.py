"""
Chat UI Widgets

Simple implementation of chat widgets that don't depend on advanced UI libraries
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
import logging

# Configure logger
logger = logging.getLogger("DualGPUOpt.UI.ChatWidgets")

# Try to import HTML and Markdown libraries for rich text, but provide fallbacks
try:
    HTML_SUPPORT = True
except ImportError:
    HTML_SUPPORT = False
    logger.warning("html module not available - HTML formatting will be limited")

class Bubble(ttk.Frame):
    """Chat message bubble widget"""

    def __init__(self, master, content: str, is_user: bool = False, **kwargs):
        """Create a new message bubble

        Args:
            master: Parent widget
            content: Message content (potentially with HTML formatting)
            is_user: Whether this is a user message (affects styling)
            **kwargs: Additional arguments to pass to ttk.Frame
        """
        super().__init__(master, **kwargs)

        # Configure style based on message type
        padding = (15, 10)

        if is_user:
            # User message styling
            frame = ttk.Frame(self, style="UserMsg.TFrame")
            bubble_bg = "#4e6a9a"  # Darker blue for user messages
            text_fg = "#ffffff"    # White text
            align = "right"
        else:
            # Assistant message styling
            frame = ttk.Frame(self, style="AssistantMsg.TFrame")
            bubble_bg = "#2d2d2d"  # Dark gray for assistant messages
            text_fg = "#e0e0e0"    # Light gray text
            align = "left"

        # Create bubble frame with padding
        frame.pack(side=align, fill="x", padx=10, pady=5)

        # Create text widget for message content
        text = tk.Text(frame, wrap="word", width=50, height=1,
                     bg=bubble_bg, fg=text_fg,
                     relief="flat", borderwidth=0,
                     highlightthickness=0, padx=padding[0], pady=padding[1])
        text.pack(fill="both", expand=True)

        # Render content (handle HTML tags if supported)
        self._render_content(text, content)

        # Calculate required height based on content and make widget read-only
        self._adjust_height(text)
        text.configure(state="disabled")

    def _render_content(self, text_widget: tk.Text, content: str) -> None:
        """Render content in the text widget, handling HTML if supported

        Args:
            text_widget: The text widget to render content in
            content: Text content with optional HTML formatting
        """
        # For simplicity, we'll just display the text without HTML parsing
        # In a more advanced implementation, we would convert HTML to Tk text tags

        # Basic HTML tag replacement
        if "<b>" in content or "<i>" in content:
            # Handle basic bold and italic tags
            parts = []
            current_text = content

            # Process bold tags
            while "<b>" in current_text and "</b>" in current_text:
                start = current_text.find("<b>")
                end = current_text.find("</b>")

                if start < end:
                    # Add text before the tag
                    if start > 0:
                        parts.append(("normal", current_text[:start]))

                    # Add the bold text
                    bold_text = current_text[start+3:end]
                    parts.append(("bold", bold_text))

                    # Update current_text to continue processing
                    current_text = current_text[end+4:]
                else:
                    # Malformed tags, stop processing
                    break

            # Add any remaining text
            if current_text:
                parts.append(("normal", current_text))

            # Insert the parts with appropriate tags
            for tag, part in parts:
                if tag == "bold":
                    # Insert with bold formatting
                    pos = text_widget.index("end-1c")
                    text_widget.insert("end", part)
                    end_pos = text_widget.index("end-1c")
                    text_widget.tag_add("bold", pos, end_pos)
                    text_widget.tag_configure("bold", font=("TkDefaultFont", 10, "bold"))
                else:
                    # Insert normal text
                    text_widget.insert("end", part)
        else:
            # No special formatting, just insert the text
            text_widget.insert("1.0", content)

    def _adjust_height(self, text_widget: tk.Text) -> None:
        """Adjust the height of the text widget based on its content

        Args:
            text_widget: The text widget to adjust
        """
        # Calculate required height - add extra line for safety
        line_count = int(text_widget.index('end-1c').split('.')[0])

        # Ensure at least one line and not too many lines
        height = max(1, min(line_count, 20))

        # Apply the height
        text_widget.configure(height=height)

        # If content is large, make the widget scrollable
        if line_count > 20:
            logger.debug(f"Large message detected ({line_count} lines), making scrollable")
            text_widget.configure(state="normal")  # Temporarily enable for scrollbar
            text_widget.configure(yscrollcommand=ttk.Scrollbar(
                text_widget.master, command=text_widget.yview).set)
            text_widget.configure(state="disabled")  # Back to disabled

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