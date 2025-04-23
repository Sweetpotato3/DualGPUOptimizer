# DualGPUOptimizer Migration Checklist

## Core Services Migration

- [x] Add Engine backend class
- [x] Add Alert Service
- [x] Add Telemetry Worker
- [x] Add Preset Service
- [x] Add Advanced Tools Dock

## UI Component Integration

- [x] Integrate Engine with Launcher Tab
- [x] Integrate Telemetry Worker with Dashboard Tab
- [x] Connect Memory Timeline to Advanced Tools Dock
- [x] Connect Alert Service to Main Application
- [ ] Connect Preset Service to tabs

## Testing

- [x] Create signal-based telemetry test
- [ ] Test the Engine integration with model loading
- [ ] Test the Alert Service with simulated alerts
- [ ] Test the Advanced Tools Dock with real memory data
- [ ] Test the interaction between components

## Code Cleanup

- [x] Fix linter errors in app_window.py
- [x] Fix linter errors in dashboard_tab.py
- [ ] Remove old polling-based telemetry code
- [ ] Remove deprecated command generation methods
- [ ] Cleanup old imports and remove unused code

## Documentation

- [x] Update README.md with new architecture details
- [ ] Add inline comments explaining signal-based integration
- [ ] Update developer documentation with new component descriptions
- [ ] Create diagrams of the new architecture
- [ ] Update user documentation with new UI instructions

## Final Steps

- [ ] Create a comprehensive test suite for the refactored components
- [ ] Perform end-to-end testing of the entire application
- [ ] Create a final report documenting the migration process
- [ ] Collect metrics comparing the performance before and after refactoring

## Additional Tasks

- [ ] Update the optimizer tab to use the Engine directly
- [ ] Update the settings tab to configure the unified services
- [ ] Implement a feedback mechanism for Engine operations
- [ ] Create a user guide for the new Advanced Tools Dock

## Known Issues to Address

- [ ] Engine unloading might not clean up all resources
- [ ] Telemetry Worker might have excessive CPU usage in some cases
- [ ] Advanced Tools Dock rendering might be slow with large datasets
- [ ] Alert Service might send duplicate alerts in some edge cases
