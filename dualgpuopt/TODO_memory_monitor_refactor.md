# Memory Monitor Refactoring Plan

## Current Status

The `memory_monitor.py` module (769 lines) is our next refactoring target. This module handles GPU memory monitoring, alerts, and recovery strategies for the DualGPUOptimizer.

## Goals

1. Improve code organization through separation of concerns
2. Enhance testability of individual components
3. Make the module more maintainable and extensible
4. Preserve backward compatibility for existing integrations
5. Add comprehensive documentation

## Proposed Module Structure

```
dualgpuopt/memory/
├── __init__.py             # Public API exports
├── monitor.py              # Core memory monitoring logic
├── alerts.py               # Alert definitions and handling
├── recovery.py             # Recovery strategies (cache clearing, etc.)
├── metrics.py              # Memory metrics collection and processing
├── predictor.py            # Memory usage prediction and modeling
├── compat.py               # Backward compatibility layer
└── README.md               # Module documentation
```

## Component Responsibilities

### monitor.py
- `MemoryMonitor` class - Core monitoring functionality
- GPU memory tracking
- Alert threshold management
- Event dispatching for thresholds

### alerts.py
- `MemoryAlert` class and enum definitions
- Alert callbacks and event handling
- Alert severity levels and context information

### recovery.py
- `RecoveryStrategy` implementations
- CUDA cache clearing
- Batch size reduction
- Memory offloading
- Process termination logic

### metrics.py
- Memory usage data collection
- Historical data tracking
- Metric calculation (percentages, rates, etc.)
- Data formatting and normalization

### predictor.py
- Memory growth prediction
- Time-to-OOM estimation
- Model-specific memory profiles
- Adaptive threshold adjustment

## Implementation Strategy

1. **Analysis Phase**
   - Identify all public API functions/classes that must be preserved
   - Map out dependencies between components
   - Identify code that can be reused vs. needs rewriting

2. **Structure Creation**
   - Create the directory and file structure
   - Implement the `__init__.py` to define the public API
   - Create skeleton classes with proper interfaces

3. **Code Migration**
   - Extract core functionality to appropriate modules
   - Refactor tightly coupled code 
   - Apply dependency injection for better testability

4. **Compatibility Layer**
   - Implement the `compat.py` module
   - Ensure all original API functions work as expected
   - Add deprecation warnings for planned API changes

5. **Testing**
   - Add unit tests for each component
   - Add integration tests for common workflows
   - Verify backward compatibility

6. **Documentation**
   - Create comprehensive README.md
   - Add docstrings to all public methods
   - Create usage examples

## Backward Compatibility

To maintain backward compatibility:

```python
# Original code:
from dualgpuopt.memory_monitor import get_memory_monitor, MemoryAlertLevel

# After refactoring, this will still work:
from dualgpuopt.memory_monitor import get_memory_monitor, MemoryAlertLevel

# But users can also use the new imports:
from dualgpuopt.memory import MemoryMonitor, AlertLevel
```

## Timeline

1. Structure creation: 1 day
2. Core monitor.py implementation: 2 days
3. Supporting modules implementation: 3 days
4. Compatibility layer: 1 day
5. Testing and bug fixes: 2 days
6. Documentation: 1 day

Total estimated time: 10 working days 