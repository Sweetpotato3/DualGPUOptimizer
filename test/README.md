# DualGPUOptimizer Testing Guide

This document provides guidelines for writing and running tests for the DualGPUOptimizer project.

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Directory Structure](#test-directory-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Mocking Strategy](#mocking-strategy)
- [Test Fixtures](#test-fixtures)
- [Coverage Guidelines](#coverage-guidelines)
- [CI/CD Integration](#cicd-integration)

## Testing Philosophy

The DualGPUOptimizer testing strategy follows these principles:

1. **Test Early, Test Often**: Write tests as you develop, not after
2. **Component Isolation**: Unit tests should test only one component at a time
3. **Mock Dependencies**: Use mocks for external dependencies
4. **Test Behavior, Not Implementation**: Focus on what code does, not how it does it
5. **Coverage Matters**: Aim for high coverage in critical paths
6. **Performance Matters**: Tests should run quickly to enable frequent execution

## Test Directory Structure

```
test/
├── conftest.py           # Shared fixtures and configuration
├── unit/                 # Unit tests
│   ├── gpu/              # GPU component tests
│   ├── memory/           # Memory component tests
│   ├── optimizer/        # Optimizer component tests
│   └── telemetry/        # Telemetry component tests
├── integration/          # Integration tests
└── functional/           # End-to-end functional tests
```

## Running Tests

### Using pytest Directly

```bash
# Run all tests
pytest

# Run specific test file
pytest test/unit/memory/test_memory_predictor.py

# Run tests with specific marker
pytest -m "not gpu"  # Skip tests that require an actual GPU
```

### Using Makefile

```bash
# Run all unit tests
make test-unit

# Run integration tests
make test-integration

# Run all tests
make test-all

# Run tests with coverage report
make test-coverage
```

## Writing Tests

### Unit Test Example

```python
def test_memory_prediction():
    # Arrange
    model_size_gb = 7
    context_length = 4096

    # Act
    result = predict_memory_requirements(model_size_gb, context_length)

    # Assert
    assert result > model_size_gb * 1024 * 1024 * 1024  # Should be larger than model
```

### Integration Test Example

```python
def test_gpu_monitor_and_telemetry():
    # Arrange - Create components
    event_bus = EventBus()
    telemetry = TelemetryService(event_bus=event_bus)
    monitor = GPUMonitor(event_bus=event_bus)

    # Act - Run the integration
    telemetry.start()
    time.sleep(0.3)  # Allow events to flow
    telemetry.stop()

    # Assert - Verify expected behavior
    assert monitor.received_metrics_count > 0
```

## Mocking Strategy

We use several mocking approaches:

1. **Mock GPU**: The `mock_gpu_info` fixture provides a controllable GPU for testing
2. **Mock Telemetry**: The `mock_telemetry` fixture provides predefined metrics
3. **Event Bus Mocking**: For testing event-driven components in isolation
4. **Environment Variables**: Using the `clean_env` fixture for environment manipulation

### Example of Mocking

```python
def test_with_mocked_gpu(mock_gpu_list):
    # The mock_gpu_list fixture provides controlled GPU data
    gpu_monitor = GPUMonitor()
    metrics = gpu_monitor.get_metrics()

    # We can make assertions based on the known mock data
    assert metrics['temperature'][0] == 65
```

## Test Fixtures

Key fixtures provided in `conftest.py`:

- `mock_gpu_info`: Single GPU with controlled properties
- `mock_gpu_list`: List of GPUs with different properties
- `mock_event_bus`: Mock event bus for testing event-driven components
- `mock_telemetry`: Mock telemetry service
- `clean_env`: Environment with relevant variables cleared

## Coverage Guidelines

We aim for the following coverage targets:

- Core GPU optimization logic: >90%
- Memory management system: >85%
- Command generation: >80%
- Event system: >85%
- Error handling: >90%

Check coverage with:

```bash
make test-coverage
```

This will generate a coverage report in `htmlcov/index.html`.

## CI/CD Integration

Tests are automatically run in CI/CD pipelines:

1. All PRs trigger the test suite
2. Merges to main trigger full test suite with coverage report
3. Nightly builds run full test suite including slow tests

### Special Test Markers

- `gpu`: Tests requiring actual GPU hardware (skipped in most CI runs)
- `slow`: Tests that take a long time to run (only run in nightly builds)
- `unit`: Unit tests that test a single component
- `integration`: Tests that verify multiple components working together
- `functional`: End-to-end tests
