# DualGPUOptimizer Refactored Architecture

## Overview

The DualGPUOptimizer has been refactored with a modern, signal-based architecture to improve performance, maintainability, and extensibility. This document explains the core components of the new architecture and how they interact.

## Core Components

### 1. Unified Engine (`engine/backend.py`)

The Engine class provides a unified interface for all model operations, replacing the previous command generation approach:

```python
# Before refactoring - command string generation
command = generate_llama_command(model_path, ctx_size, gpu_layers)

# After refactoring - unified engine interface
engine = Engine()
command = engine.generate_command(model_path, model_format, framework, context_size, gpu_split)
# Or direct operations
engine.load_model(model_path, model_format)
result = engine.generate(prompt)
```

**Key Features:**
- Auto-detection of model formats (GGUF, AWQ, HF)
- Unified interface for different backends (llama.cpp, vLLM, Transformers)
- Streaming response support
- Memory-efficient operation

### 2. Signal-Based Telemetry (`services/telemetry.py`)

The TelemetryWorker class provides real-time GPU metrics through Qt signals:

```python
# Before refactoring - polling-based updates
metrics = telemetry_service.get_metrics()
update_ui(metrics)

# After refactoring - signal-based updates
worker = TelemetryWorker()
worker.util_updated.connect(self._handle_util_update)
worker.vram_updated.connect(self._handle_vram_update)
worker.start()
```

**Key Features:**
- Dedicated signals for each metric type
- Background thread for efficient collection
- Reduced CPU usage compared to polling
- Automatic GPU detection and monitoring

### 3. Simplified Alert System (`services/alerts.py`)

The AlertService provides a two-tier alert system for monitoring GPU conditions:

```python
# Before refactoring - complex alert levels
if condition == ALERT_CRITICAL:
    show_critical_alert(message)
elif condition == ALERT_HIGH:
    show_high_alert(message)
# ...etc.

# After refactoring - simplified alert levels
alert_service = AlertService()
alert_service.warning_alert.connect(self._handle_warning)
alert_service.critical_alert.connect(self._handle_critical)
```

**Key Features:**
- Two clear alert levels (WARNING, CRITICAL)
- Direct integration with system tray and status bar
- Comprehensive metrics-based alert conditions
- Customizable thresholds

### 4. Unified Preset System (`services/presets.py`)

The PresetService manages all presets in a single JSON-based format:

```python
# Before refactoring - multiple preset systems
model_config = load_model_config(model_name)
prompt_template = load_template(template_name)
persona = load_persona(persona_name)

# After refactoring - unified preset system
preset_service = PresetService()
preset = preset_service.load_preset(preset_name)
# preset contains model, template, and persona configurations
```

**Key Features:**
- Single JSON format for all settings
- Persistent storage in `~/.dualgpuopt/presets/`
- Easy sharing and management
- One-click application of complete configurations

### 5. Advanced Tools Dock (`ui/advanced.py`)

The AdvancedToolsDock provides diagnostic tools in a hideable dock:

```python
# Integration with main window
advanced_dock = AdvancedToolsDock(self)
self.addDockWidget(Qt.RightDockWidgetArea, advanced_dock)
advanced_dock.hide()  # Hidden by default
```

**Key Features:**
- Memory Timeline visualization
- Performance monitoring tools
- Hidden by default to simplify the main UI
- Component sharing with main tabs

## Communication Flow

The refactored architecture uses a hybrid communication approach:

1. **Direct Qt Signals** for high-frequency data:
   - GPU metrics from TelemetryWorker
   - Alerts from AlertService
   - Engine status updates

2. **Event Bus** for less frequent or complex events:
   - Configuration changes
   - User preference updates
   - Preset loading requests

## Diagram

```
┌───────────────────┐     ┌───────────────────┐
│  Main Application │     │   System Tray     │
└─────────┬─────────┘     └────────┬──────────┘
          │                        │
          │     ┌───────────────────────────┐
          └─────┤     Alert Service         │
          │     └───────────────────────────┘
          │
┌─────────▼────────┐      ┌───────────────────┐
│                  │      │                   │
│     Engine       ◄──────┤    Launcher Tab   │
│                  │      │                   │
└──────────────────┘      └───────────────────┘
          │
          │     ┌───────────────────────────┐
          └─────►     Telemetry Worker      │
                └─────────────┬─────────────┘
                              │
                ┌─────────────▼───────────────┐
                │       Dashboard Tab          │
                └───────────────┬─────────────┘
                                │
                ┌───────────────▼───────────────┐
                │    Advanced Tools Dock        │
                └───────────────────────────────┘
```

## Implementation Details

### Signal Connections

The `qt/app_window.py` initializes services and connects them to UI components:

```python
# Initialize services
self.engine = Engine()
self.alert_service = AlertService()
self.telemetry_worker = TelemetryWorker(mock_mode=self.mock_mode)
self.telemetry_worker.start()

# Connect alert service to UI
self.alert_service.warning_alert.connect(self._handle_warning_alert)
self.alert_service.critical_alert.connect(self._handle_critical_alert)

# Connect telemetry worker to dashboard
self.dashboard_tab.set_telemetry_worker(self.telemetry_worker)

# Connect engine to launcher
self.launcher_tab.set_engine(self.engine)
```

### Memory Timeline Sharing

The memory timeline is shared between the Memory Profiler tab and Advanced Tools dock:

```python
# Initialize memory profiler tab
self.memory_tab = MemoryProfilerTab()

# Connect memory tab to advanced dock
if hasattr(self, 'advanced_dock') and self.advanced_dock:
    # Memory timeline is shared between memory tab and advanced dock
    self.advanced_dock.set_memory_timeline(self.memory_tab.memory_timeline)
```

## Benefits of the New Architecture

1. **Improved Responsiveness**: Signal-based updates provide immediate UI updates
2. **Reduced CPU Usage**: Polling is eliminated in favor of event-driven updates
3. **Better Separation of Concerns**: Each component has a clear responsibility
4. **Simplified UI**: Advanced tools are hidden by default
5. **Unified Interface**: Single consistent interface for different model types
6. **Enhanced Extensibility**: New model formats can be added easily
7. **Better Resource Management**: Proper cleanup of resources on application exit

## Migration Guide

See the `migration_checklist.md` for a detailed plan to complete the migration to the new architecture.

## Testing

The `test_signal_telemetry.py` script demonstrates how to test the signal-based architecture:

```python
# Create telemetry worker in mock mode
self.telemetry_worker = TelemetryWorker(mock_mode=True)

# Connect signals
self.telemetry_worker.util_updated.connect(self._handle_util)
self.telemetry_worker.vram_updated.connect(self._handle_vram)
# ... connect other signals ...

# Start telemetry worker
self.telemetry_worker.start()
```

Run the test script using the provided batch or shell script:
- Windows: `run_integration_test.bat`
- Linux/Mac: `./run_integration_test.sh` 