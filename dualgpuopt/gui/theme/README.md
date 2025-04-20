# Theme System

The DualGPUOptimizer theme system provides a flexible, modular approach to styling the application UI. This module was refactored from a single 549-line file into a structured package with clear separation of concerns.

## Architecture

The theme system is organized into the following components:

### Colors (`colors.py`)
- Defines theme color palettes (Dark Purple, Light, Neon Dark)
- Manages current theme selection
- Provides theme lookup functions

### DPI and Font Scaling (`dpi.py`)
- Handles high DPI display support
- Implements font scaling for better readability
- Configures application-wide font settings

### Styling (`styling.py`)
- Applies theme styles to ttk widgets
- Configures widget-specific styling
- Manages option database for consistent theming

### Compatibility (`compatibility.py`)
- Integrates with third-party theming (ttkthemes)
- Provides fallback styling options
- Handles compatibility across different platforms

### Core Theme Management (`core.py`)
- Controls theme switching and persistence
- Loads themes from configuration
- Includes ThemeToggleButton widget

## Usage Examples

### Basic Theme Application

```python
import tkinter as tk
from dualgpuopt.gui.theme import apply_theme

root = tk.Tk()
apply_theme(root)
```

### Theme Switching

```python
from dualgpuopt.gui.theme import set_theme

# Switch to light theme
set_theme(root, "light")

# Toggle between light and dark themes
from dualgpuopt.gui.theme import toggle_theme
toggle_theme(root)
```

### Theme Selection Widget

```python
from dualgpuopt.gui.theme import ThemeToggleButton

# Add a theme toggle button to your UI
theme_btn = ThemeToggleButton(parent_widget)
theme_btn.pack()
```

### Custom Theme Integration

For more advanced scenarios, the theme system can be extended with custom theme palettes:

```python
from dualgpuopt.gui.theme.colors import AVAILABLE_THEMES

# Add a custom theme
AVAILABLE_THEMES["my_theme"] = {
    "bg": "#2A2A2A",
    "fg": "#FFFFFF",
    "accent": "#00BCD4",
    # ... other color definitions
}
```

## Backward Compatibility

To ensure a smooth transition from the previous monolithic theme module, a backward compatibility layer is provided in `compat.py`. This allows existing code to continue working without modification.

## Theming Custom Widgets

For custom widgets that need to respond to theme changes, use the `theme_observer.py` module to register your widgets for automatic updates when themes change.

## Integration with Event System

The theme system integrates with the application's event bus to publish theme change notifications:

```python
from dualgpuopt.services.event_service import event_bus

# Subscribe to theme change events
event_bus.subscribe("config_changed:theme", handle_theme_change)
``` 