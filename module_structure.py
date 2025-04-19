#!/usr/bin/env python3
"""
Module structure definition for DualGPUOptimizer.
This file defines the dependency hierarchy to avoid circular imports.

Dependency Order (Higher levels depend on lower ones):

Level 1 (Base/Constants):
- constants modules (gui_constants.py)
- utility modules (no dependencies)

Level 2 (Core Services):
- gpu_info.py (depends on constants)
- logconfig.py (depends on constants)
- configio.py (depends on constants)

Level 3 (Business Logic):
- telemetry.py (depends on gpu_info, logconfig)
- optimizer.py (depends on gpu_info)
- layer_balance.py (depends on gpu_info)
- metrics.py (depends on gpu_info, telemetry)

Level 4 (Controllers):
- services/* (depends on business logic)
- commands/* (depends on business logic)

Level 5 (UI):
- gui/* (depends on controllers and business logic)

Level 6 (Application):
- __main__.py (orchestrates everything)
"""

# This is the recommended import order to follow when refactoring
RECOMMENDED_IMPORT_ORDER = [
    # Level 1
    "gui_constants",
    
    # Level 2
    "logconfig",
    "gpu_info",
    "configio",
    
    # Level 3
    "metrics",
    "telemetry", 
    "optimizer",
    "layer_balance",
    "ctx_size",
    "mpolicy",
    
    # Level 4
    "services.state_service",
    "services.event_bus",
    "commands.gpu_commands",
    
    # Level 5
    "gui.dashboard",
    "gui.launcher",
    "gui.optimizer_tab",
    
    # Level 6
    "__main__"
]

# Integration phases
INTEGRATION_PHASES = [
    {
        "name": "Phase 1: Core GPU Information",
        "modules": ["gui_constants", "logconfig", "gpu_info"]
    },
    {
        "name": "Phase 2: Telemetry and Metrics",
        "modules": ["metrics", "telemetry"]
    },
    {
        "name": "Phase 3: Optimization Logic",
        "modules": ["optimizer", "layer_balance", "ctx_size", "mpolicy"]
    },
    {
        "name": "Phase 4: Services and Commands",
        "modules": ["services.state_service", "services.event_bus", "commands.gpu_commands"]
    },
    {
        "name": "Phase 5: UI Components",
        "modules": ["gui.dashboard", "gui.launcher", "gui.optimizer_tab"]
    },
    {
        "name": "Phase 6: Main Application",
        "modules": ["__main__"]
    }
] 