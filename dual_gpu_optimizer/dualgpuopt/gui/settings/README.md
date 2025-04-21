# Settings Module

## Overview

The Settings module provides a modular, maintainable architecture for managing application settings in the DualGPUOptimizer. It handles appearance themes, GPU overclocking, and general application settings through a clean, component-based approach.

## Module Structure

The module is organized into the following components:

- `settings_tab.py`: Main container that orchestrates all settings components
- `appearance.py`: Manages theme and visual appearance settings
- `overclocking.py`: Handles GPU overclocking configuration
- `application_settings.py`: Manages general application settings
- `compat.py`: Provides backward compatibility with the previous monolithic structure
- `__init__.py`: Exports the public API

## Components

### SettingsTab

The main settings container that coordinates all settings components and provides:
- Scrollable content area
- Status updates
- Save and reset functionality
- Event handling

```python
from dualgpuopt.gui.settings import SettingsTab

# Create a settings tab
settings_tab = SettingsTab(parent_frame, gpus)
```

### AppearanceFrame

Manages theme settings including:
- Color theme selection
- TTK theme configuration
- Theme previews

```python
from dualgpuopt.gui.settings import AppearanceFrame

# Create an appearance settings frame
appearance = AppearanceFrame(parent_frame, on_theme_change=callback_function)
```

### OverclockingFrame

Provides GPU overclocking controls:
- GPU selection
- Core and memory clock adjustment
- Power limit configuration
- Fan speed control

```python
from dualgpuopt.gui.settings import OverclockingFrame

# Create an overclocking settings frame
overclocking = OverclockingFrame(parent_frame, gpus, on_status_change=callback_function)
```

### ApplicationSettingsFrame

Manages general application settings:
- Startup behavior
- GPU idle detection and alerts
- Threshold configuration

```python
from dualgpuopt.gui.settings import ApplicationSettingsFrame

# Create an application settings frame
app_settings = ApplicationSettingsFrame(parent_frame, on_settings_change=callback_function)
```

## Backward Compatibility

The module maintains backward compatibility with code that imports from the original monolithic `settings.py` file. However, new code should import directly from the modular structure:

```python
# Legacy import (still works but deprecated)
from dualgpuopt.gui.settings import SettingsTab

# Preferred import
from dualgpuopt.gui.settings.settings_tab import SettingsTab
```

## Usage Example

```python
import tkinter as tk
from tkinter import ttk
from dualgpuopt.gui.settings import SettingsTab
from dualgpuopt.gpu_info import get_gpus

root = tk.Tk()
frame = ttk.Frame(root)
frame.pack(fill="both", expand=True)

# Get available GPUs
gpus = get_gpus()

# Create settings tab
settings = SettingsTab(frame, gpus)
settings.pack(fill="both", expand=True)

root.mainloop()
```

## Configuration

Settings are persisted through the application's configuration service:

```python
from dualgpuopt.services.config_service import config_service

# Get a saved setting
theme = config_service.get("theme", "dark_purple")  # Default to dark_purple if not set

# Save a setting
config_service.set("idle_threshold", 30)
``` 