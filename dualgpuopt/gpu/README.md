# GPU Module

## Overview

The GPU module provides functionality for interacting with GPUs, including:

- Querying GPU information (name, memory, utilization, temperature, etc.)
- Monitoring GPU metrics in real-time
- Mock GPU support for testing without actual hardware

## Module Structure

- `__init__.py`: Public API
- `common.py`: Shared functionality and constants
- `info.py`: GPU information querying
- `mock.py`: Mock GPU functionality for testing
- `monitor.py`: Specific GPU metrics monitoring functions
- `compat.py`: Backward compatibility with old gpu_info.py module

## Usage Examples

### Basic GPU Querying

```python
from dualgpuopt.gpu import query

# Get information about all GPUs
gpus = query()
for gpu in gpus:
    print(f"GPU {gpu['id']}: {gpu['name']}")
    print(f"  Memory: {gpu['mem_used']} / {gpu['mem_total']} MB")
    print(f"  Utilization: {gpu['util']}%")
    print(f"  Temperature: {gpu['temperature']}°C")
    print(f"  Power: {gpu['power_usage']}W")
```

### Getting Specific Metrics

```python
from dualgpuopt.gpu import get_memory_info, get_utilization, get_temperature, get_power_usage

# Get memory information for all GPUs
memory_info = get_memory_info()
print(f"Memory info: {memory_info}")

# Get utilization for a specific GPU (GPU 0)
util = get_utilization(gpu_id=0)
print(f"GPU 0 utilization: {util}%")

# Get temperature for all GPUs
temps = get_temperature()
print(f"GPU temperatures: {temps}")

# Get power usage for a specific GPU (GPU 1)
power = get_power_usage(gpu_id=1)
print(f"GPU 1 power usage: {power}W")
```

### Using Mock Mode

```python
from dualgpuopt.gpu import set_mock_mode, query

# Enable mock mode (for testing without actual GPUs)
set_mock_mode(True)

# Now all functions will return mock data
mock_gpus = query()
print(f"Mock GPUs: {mock_gpus}")

# Disable mock mode
set_mock_mode(False)
```

## Backward Compatibility

The module maintains backwards compatibility with the original `gpu_info.py` module, so existing code will continue to work without changes:

```python
from dualgpuopt import gpu_info

# This will use the refactored code transparently
gpus = gpu_info.query()
```
