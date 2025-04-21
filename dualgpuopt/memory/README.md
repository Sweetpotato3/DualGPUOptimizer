# Memory Monitoring System

This module provides a comprehensive system for monitoring GPU memory usage, alerting on memory conditions, and implementing recovery strategies to prevent out-of-memory (OOM) errors.

## Structure

The memory monitoring system is organized into several focused components:

- **monitor.py**: Core memory monitoring functionality with real-time GPU memory tracking
- **metrics.py**: Memory statistics collection and processing
- **alerts.py**: Alert definitions and handling based on memory thresholds
- **recovery.py**: Recovery strategies to prevent OOM conditions
- **predictor.py**: Memory usage prediction based on model profiles
- **compat.py**: Backward compatibility layer for original API

## Key Components

### MemoryMonitor

The central class that orchestrates memory monitoring and management:

```python
from dualgpuopt.memory import get_memory_monitor

# Get singleton memory monitor instance
monitor = get_memory_monitor()

# Start monitoring
monitor.start_monitoring()

# Get memory stats in GB
stats = monitor.get_memory_stats(gpu_id=0)
print(f"Total memory: {stats['total']:.2f} GB")
print(f"Used memory: {stats['used']:.2f} GB")
print(f"Free memory: {stats['free']:.2f} GB")

# Stop monitoring
monitor.stop_monitoring()
```

### Memory Profiles

Profiles for different models that estimate memory requirements:

```python
from dualgpuopt.memory import MemoryProfile

# Create a custom profile
my_profile = MemoryProfile(
    name="my-model-7b",
    base_usage=7 * 1024**3,      # 7 GB base
    per_batch_usage=50 * 1024**2,  # 50 MB per batch
    per_token_usage=3 * 1024,    # 3 KB per token
)

# Register with monitor
monitor.register_profile(my_profile)
monitor.set_active_profile("my-model-7b")

# Estimate maximum batch size for 2048 tokens
max_batch = monitor.estimate_max_batch(gpu_id=0, token_count=2048)
print(f"Maximum batch size: {max_batch}")
```

### Memory Alerts

Register callbacks for memory alerts:

```python
from dualgpuopt.memory import MemoryAlertLevel

# Register alert callback
def handle_critical_alert(alert):
    print(f"CRITICAL ALERT: {alert.message}")
    print(f"GPU {alert.gpu_id}: {alert.current_usage:.1f}% > {alert.threshold:.1f}%")
    print("Recommendations:")
    for rec in alert.recommendations:
        print(f"- {rec}")

monitor.register_alert_callback(MemoryAlertLevel.CRITICAL, handle_critical_alert)
```

### Recovery Strategies

Register recovery strategies to handle OOM conditions:

```python
from dualgpuopt.memory import MemoryRecoveryStrategy

# Register custom recovery function
def reduce_batch_size(gpu_id, memory_stats):
    # Implement batch size reduction logic
    print(f"Reducing batch size for GPU {gpu_id}")
    return True  # Return True if successful

monitor.register_recovery_strategy(MemoryRecoveryStrategy.REDUCE_BATCH, reduce_batch_size)
```

## Usage Example

Complete example with all components:

```python
from dualgpuopt.memory import (
    get_memory_monitor, MemoryAlertLevel, MemoryRecoveryStrategy, 
    DEFAULT_PROFILES, initialize_memory_profiles
)

# Initialize memory monitor with default profiles
initialize_memory_profiles()
monitor = get_memory_monitor()

# Register alert callbacks
def on_warning(alert):
    print(f"WARNING: {alert.message}")

def on_critical(alert):
    print(f"CRITICAL: {alert.message}")

def on_emergency(alert):
    print(f"EMERGENCY: {alert.message}")

monitor.register_alert_callback(MemoryAlertLevel.WARNING, on_warning)
monitor.register_alert_callback(MemoryAlertLevel.CRITICAL, on_critical)
monitor.register_alert_callback(MemoryAlertLevel.EMERGENCY, on_emergency)

# Register recovery strategies
monitor.register_recovery_strategy(
    MemoryRecoveryStrategy.CLEAR_CACHE,
    lambda gpu_id, stats: clear_cuda_cache(gpu_id)
)

# Set active profile for a model
monitor.set_active_profile("llama2-13b")

# Start monitoring
monitor.start_monitoring()

# Run your application...

# Get memory predictions
projected_usage = monitor.project_memory_usage(gpu_id=0, seconds_ahead=60)
if projected_usage and projected_usage > 90:
    print(f"WARNING: Projected to reach {projected_usage:.1f}% memory usage in 60 seconds")

# Estimate safe context size
safe_ctx = monitor.estimate_safe_context_size(gpu_id=0, batch_size=4)
print(f"Safe context size: {safe_ctx} tokens")

# Stop monitoring when done
monitor.stop_monitoring()
```

## Backward Compatibility

This refactored module maintains backward compatibility with the original `memory_monitor.py` module, so existing code will continue to work without changes. The original imports will still work:

```python
from dualgpuopt.memory_monitor import get_memory_monitor, MemoryAlertLevel
``` 