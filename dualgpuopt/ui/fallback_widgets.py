"""
Fallback UI Widgets

Provides fallback implementations for UI widgets when optional dependencies are missing.
These implementations ensure the application can run with minimal dependencies.
"""
import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Configure logger
logger = logging.getLogger("DualGPUOpt.UI.Fallback")

# Default theme colors for fallback widgets
DEFAULT_THEME = {
    "bg": "#2b2b2b",
    "fg": "#e0e0e0",
    "primary": "#6d55c8",
    "secondary": "#7e68ca",
    "success": "#28a745",
    "info": "#17a2b8",
    "warning": "#ffc107",
    "danger": "#dc3545",
    "border": "#444444",
    "input_bg": "#3b3b3b"
}


class ScrolledFrame(ttk.Frame):
    """A frame with a scrollbar that scrolls another frame"""

    def __init__(self, parent, autohide=True, **kwargs):
        """Initialize the ScrolledFrame

        Args:
            parent: Parent widget
            autohide: Whether to hide the scrollbar when not needed
            **kwargs: Additional keyword arguments for the Frame
        """
        super().__init__(parent, **kwargs)

        # Create a canvas with scrollbar
        self.canvas = tk.Canvas(self, bg=DEFAULT_THEME["bg"],
                               highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical",
                                      command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self._scrollbar_set)

        # Create the scrollable frame
        self.inner_frame = ttk.Frame(self.canvas)
        self.inner_frame_id = self.canvas.create_window((0, 0),
                                                     window=self.inner_frame,
                                                     anchor="nw")

        # Pack the widgets
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Configure the canvas to expand the inner frame to its width
        def _configure_inner_frame(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            # Set the scrollable frame's width to match the canvas
            self.canvas.itemconfigure(self.inner_frame_id,
                                     width=event.width)

        # Bind to the configure event
        self.inner_frame.bind("<Configure>", _configure_inner_frame)
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self.inner_frame_id, width=e.width))
        
        # Add mousewheel support
        self._bind_mousewheel()
        
        # Set autohide property
        self.autohide = autohide

    def _scrollbar_set(self, first, last):
        """Custom scrollbar set method that supports auto-hiding

        Args:
            first: First position (0.0 to 1.0)
            last: Last position (0.0 to 1.0)
        """
        self.scrollbar.set(first, last)
        
        # Hide scrollbar if not needed and autohide is enabled
        if self.autohide:
            if float(first) <= 0.0 and float(last) >= 1.0:
                self.scrollbar.pack_forget()
            else:
                if not self.scrollbar.winfo_viewable():
                    self.scrollbar.pack(side="right", fill="y")
    
    def _bind_mousewheel(self):
        """Bind mousewheel events to the canvas"""
        def _on_mousewheel(event):
            # Handle different platforms
            if event.num == 4 or event.delta > 0:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                self.canvas.yview_scroll(1, "units")
        
        # Bind for different platforms
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows
        self.canvas.bind_all("<Button-4>", _on_mousewheel)    # Linux scroll up
        self.canvas.bind_all("<Button-5>", _on_mousewheel)    # Linux scroll down


class Meter(ttk.Frame):
    """Fallback meter widget that mimics the ttkbootstrap Meter"""
    
    def __init__(
        self, 
        parent,
        metersize: int = 180,
        amountused: float = 25,
        amounttotal: float = 100,
        metertype: str = "full",
        subtext: str = "percent",
        interactive: bool = False,
        stripethickness: int = 0,
        bootstyle: str = "primary",
        **kwargs
    ):
        """Initialize the fallback Meter

        Args:
            parent: Parent widget
            metersize: Size of the meter
            amountused: Current value
            amounttotal: Maximum value
            metertype: Type of meter (ignored in fallback)
            subtext: Text to display below the value
            interactive: Whether the meter can be changed by the user
            stripethickness: Thickness of the stripes (ignored in fallback)
            bootstyle: Style of the meter (colors)
            **kwargs: Additional keyword arguments
        """
        super().__init__(parent, **kwargs)
        
        # Store parameters
        self.amountused = amountused
        self.amounttotal = amounttotal
        self.subtext = subtext
        self.interactive = interactive
        self.bootstyle = bootstyle
        
        # Create progress bar
        self.progress = ttk.Progressbar(
            self, 
            orient="horizontal", 
            length=metersize,
            mode="determinate",
            maximum=amounttotal,
            value=amountused
        )
        self.progress.pack(side="top", padx=5, pady=5, fill="x")
        
        # Create percentage display
        if subtext == "percent":
            display_text = f"{int((amountused / amounttotal) * 100)}%"
        else:
            display_text = f"{amountused} {subtext}"
            
        self.value_label = ttk.Label(self, text=display_text)
        self.value_label.pack(side="top", pady=(0, 5))
        
        # Add interactivity if requested
        if interactive:
            self.progress.bind("<Button-1>", self._on_click)
            
    def _on_click(self, event):
        """Handle click on the progress bar"""
        if not self.interactive:
            return
            
        # Calculate new value based on click position
        width = self.progress.winfo_width()
        click_pos = event.x
        new_value = (click_pos / width) * self.amounttotal
        self.configure(amountused=new_value)
        
        # Call the meter command if it exists
        if hasattr(self, "command") and callable(self.command):
            self.command(new_value)
    
    def configure(self, **kwargs):
        """Configure the meter with new values"""
        if "amountused" in kwargs:
            self.amountused = kwargs["amountused"]
            self.progress.configure(value=self.amountused)
            
            # Update the label
            if self.subtext == "percent":
                display_text = f"{int((self.amountused / self.amounttotal) * 100)}%"
            else:
                display_text = f"{self.amountused} {self.subtext}"
                
            self.value_label.configure(text=display_text)
            
        if "amounttotal" in kwargs:
            self.amounttotal = kwargs["amounttotal"]
            self.progress.configure(maximum=self.amounttotal)
            
        if "subtext" in kwargs:
            self.subtext = kwargs["subtext"]
            
        # Handle other configuration options
        super().configure(**{k: v for k, v in kwargs.items() 
                          if k not in ["amountused", "amounttotal", "subtext"]})


class Floodgauge(ttk.Progressbar):
    """Fallback Floodgauge widget that mimics the ttkbootstrap Floodgauge"""
    
    def __init__(
        self,
        parent,
        text: str = "",
        font: Tuple = None,
        bootstyle: str = "primary",
        mask: str = "{:.0f}%",
        **kwargs
    ):
        """Initialize the Floodgauge

        Args:
            parent: Parent widget
            text: Text to display
            font: Font to use
            bootstyle: Style to use
            mask: Format string for the value
            **kwargs: Additional keyword arguments
        """
        super().__init__(parent, **kwargs)
        
        # Create a label with the text that will overlay the progressbar
        self.text = text
        self.mask = mask
        self.font = font or ("TkDefaultFont", 10)
        
        # Create frame at same position as progressbar
        self.frame = ttk.Frame(parent)
        self.label = ttk.Label(
            self.frame, 
            text=self._format_text(), 
            background=DEFAULT_THEME["input_bg"],
            anchor="center",
            font=self.font
        )
        self.label.pack(expand=True, fill="both")
        
        # Position label on top of progressbar using place manager
        self.frame.place(in_=self, relwidth=1, relheight=1)
        
    def _format_text(self) -> str:
        """Format the display text based on the current value"""
        if not self.text and not self.mask:
            return ""
            
        value_part = ""
        if self.mask:
            try:
                value = float(self["value"])
                maximum = float(self["maximum"])
                if maximum > 0:
                    percent = (value / maximum) * 100
                    value_part = self.mask.format(percent)
            except (ValueError, ZeroDivisionError):
                value_part = self.mask.format(0)
                
        if self.text and value_part:
            return f"{self.text} {value_part}"
        elif self.text:
            return self.text
        else:
            return value_part
            
    def configure(self, **kwargs):
        """Configure the Floodgauge"""
        updates = {}
        
        if "text" in kwargs:
            self.text = kwargs.pop("text")
            updates["text"] = True
            
        if "mask" in kwargs:
            self.mask = kwargs.pop("mask")
            updates["text"] = True
            
        if "font" in kwargs:
            self.font = kwargs.pop("font")
            self.label.configure(font=self.font)
            
        # Update the base progressbar
        super().configure(**kwargs)
        
        # Update the label text if value changed or text/mask changed
        if "value" in kwargs or updates.get("text", False):
            self.label.configure(text=self._format_text())


class DateEntry(ttk.Entry):
    """Fallback DateEntry widget that mimics the ttkbootstrap DateEntry"""
    
    def __init__(
        self,
        parent,
        firstweekday: int = 0,
        startdate: Optional[str] = None,
        bootstyle: str = "primary",
        **kwargs
    ):
        """Initialize the DateEntry

        Args:
            parent: Parent widget
            firstweekday: First day of the week
            startdate: Initial date (YYYY-MM-DD)
            bootstyle: Style to use
            **kwargs: Additional keyword arguments
        """
        super().__init__(parent, **kwargs)
        
        # Set initial value
        if startdate:
            self.insert(0, startdate)
        else:
            # Use current date
            from datetime import datetime
            today = datetime.today().strftime("%Y-%m-%d")
            self.insert(0, today)
            
        # Add a button to show calendar
        self.button_frame = ttk.Frame(parent)
        self.calendar_button = ttk.Button(
            self.button_frame,
            text="📅",
            width=3,
            command=self._show_calendar
        )
        self.calendar_button.pack(side="right", fill="y")
        
        # Position button next to entry using place manager
        self.button_frame.place(in_=self, relx=1, rely=0, anchor="ne",
                               x=5, rely=0.5, anchor="e")
        
        # Add validation
        self._validate()
        
    def _validate(self):
        """Add validation to ensure the entry contains a valid date"""
        def _validate_date(text):
            if not text:
                return True
                
            # Check format YYYY-MM-DD
            if not len(text) <= 10:
                return False
                
            # Simple validation - more complex validation could be added
            parts = text.split("-")
            if len(parts) > 3:
                return False
                
            return True
            
        validate_cmd = self.register(_validate_date)
        self.configure(validate="key", validatecommand=(validate_cmd, "%P"))
        
    def _show_calendar(self):
        """Show a simple calendar dialog"""
        # Simple message, normally would show a calendar widget
        tk.messagebox.showinfo(
            "DateEntry", 
            "In the full version, this would display a calendar for date selection.\n"
            "Please enter a date in YYYY-MM-DD format."
        )
        
    def get_date(self):
        """Get the current date as a string

        Returns:
            str: Current date in YYYY-MM-DD format
        """
        return self.get()


# Dictionary of fallback widgets to provide instead of missing optional widgets
FALLBACK_WIDGETS = {
    "ScrolledFrame": ScrolledFrame,
    "Meter": Meter,
    "Floodgauge": Floodgauge,
    "DateEntry": DateEntry
}


def get_widget_class(widget_name: str, original_module=None):
    """Get a widget class, using fallback if the original is not available

    Args:
        widget_name: Name of the widget class
        original_module: Original module that should contain the widget

    Returns:
        A widget class, either from the original module or a fallback
    """
    if original_module is not None:
        try:
            return getattr(original_module, widget_name)
        except (AttributeError, ImportError):
            logger.debug(f"Widget {widget_name} not found in module, using fallback")
    
    if widget_name in FALLBACK_WIDGETS:
        logger.debug(f"Using fallback implementation for {widget_name}")
        return FALLBACK_WIDGETS[widget_name]
    
    # If no fallback exists, try to use a basic ttk widget
    try:
        return getattr(ttk, widget_name)
    except AttributeError:
        logger.warning(f"No fallback for {widget_name}, using Frame")
        return ttk.Frame


def create_widget_safely(
    widget_class: str,
    parent: tk.Widget,
    module=None,
    fallback_class=None,
    **kwargs
) -> tk.Widget:
    """Create a widget with error handling and fallbacks

    Args:
        widget_class: Name of the widget class to create
        parent: Parent widget
        module: Module containing the widget class
        fallback_class: Fallback class to use if the widget_class fails
        **kwargs: Keyword arguments for the widget

    Returns:
        Created widget
    """
    # First try to get the requested class
    try:
        if module is not None:
            cls = getattr(module, widget_class)
        else:
            # Try to find in FALLBACK_WIDGETS
            if widget_class in FALLBACK_WIDGETS:
                cls = FALLBACK_WIDGETS[widget_class]
            else:
                # Try ttk
                cls = getattr(ttk, widget_class)
                
        return cls(parent, **kwargs)
    except (AttributeError, ImportError, tk.TclError) as e:
        logger.warning(f"Failed to create {widget_class}: {e}")
        
        # Try fallback class if provided
        if fallback_class is not None:
            try:
                if isinstance(fallback_class, str):
                    if fallback_class in FALLBACK_WIDGETS:
                        return FALLBACK_WIDGETS[fallback_class](parent, **kwargs)
                    else:
                        return getattr(ttk, fallback_class)(parent, **kwargs)
                else:
                    return fallback_class(parent, **kwargs)
            except Exception as e2:
                logger.error(f"Failed to create fallback widget: {e2}")
        
        # Last resort - return a basic frame
        logger.error(f"Using Frame as last resort fallback for {widget_class}")
        return ttk.Frame(parent) 