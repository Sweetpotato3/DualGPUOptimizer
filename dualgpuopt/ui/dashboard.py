"""
Main dashboard integrating the refactored components.
"""
from __future__ import annotations
import sys
from PySide6.QtWidgets import QMainWindow, QApplication, QStatusBar, QMenuBar
from PySide6.QtCore import Qt

# --- Import refactored components ---
# Assuming these files are now in the correct locations:
# dualgpuopt/services/alerts.py
# dualgpuopt/services/presets.py
# dualgpuopt/ui/advanced.py
# dualgpuopt/services/telemetry.py
# dualgpuopt/engine/backend.py

try:
    from dualgpuopt.services.alerts import alert_service
    from dualgpuopt.services.presets import PresetDock
    from dualgpuopt.ui.advanced import AdvancedDock
    from dualgpuopt.services.telemetry import telemetry_worker
    from dualgpuopt.engine.backend import Engine
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Ensure the files exist in the expected dualgpuopt/services and dualgpuopt/ui directories.")
    sys.exit(1)

# --- Main Dashboard Class ---

class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DualGPUOptimizer")
        self.resize(1200, 800)
        
        # --- Initialize Core Components ---
        self.engine = Engine() # Instantiate the backend engine
        self.setStatusBar(QStatusBar(self))
        self.setMenuBar(QMenuBar(self))
        
        # --- Setup Alerts --- 
        # Pass the status bar and app instance
        alert_service.setup(self.statusBar(), QApplication.instance())
        print("Alert service initialized.")

        # --- Setup Presets Dock ---
        self.presets_dock = PresetDock(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.presets_dock)
        self.presets_dock.preset_selected.connect(self._apply_preset)
        print("Presets dock added.")
        
        # --- Setup Advanced Tools Dock ---
        self.advanced_dock = AdvancedDock(self)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.advanced_dock)
        self.advanced_dock.hide() # Hidden by default
        print("Advanced tools dock added (hidden).")
        
        # --- Setup View Menu ---
        view_menu = self.menuBar().addMenu("&View")
        advanced_action = view_menu.addAction("&Advanced Tools")
        advanced_action.setCheckable(True)
        advanced_action.setChecked(False)
        # Use a lambda to capture the correct state for setVisible
        advanced_action.toggled.connect(lambda checked: self.advanced_dock.setVisible(checked))
        print("View menu created.")

        # --- Setup Export Menu ---
        export_menu = self.menuBar().addMenu("&Export")
        export_menu.addAction("Export Current View", self._export_current_view)
        print("Export menu created.")

        # --- Start Telemetry Worker ---
        # The telemetry_worker instance is created in services/telemetry.py
        # Connect signals to placeholder methods
        telemetry_worker.util_updated.connect(self._update_util_display)
        telemetry_worker.vram_updated.connect(self._update_vram_display)
        telemetry_worker.temp_updated.connect(self._update_temp_display)
        telemetry_worker.power_updated.connect(self._update_power_display)
        telemetry_worker.metrics_updated.connect(self._update_full_metrics)
        
        telemetry_worker.start() # Start collecting data
        print("Telemetry worker started and signals connected.")

        # --- Placeholder for central widget / other UI elements ---
        # Example: self.setCentralWidget(YourMainChatWidget())

    # --- Slot Methods for Signals ---
    
    def _apply_preset(self, preset_data: dict):
        print(f"Applying preset: {preset_data.get('name', 'Unnamed')}")
        # TODO: Implement logic to apply model_path, gpu_settings etc.
        # Example: self.engine.load(preset_data['model_path'], **preset_data['gpu_settings'])
        pass

    def _update_util_display(self, value: float):
        # TODO: Update your UI element showing overall utilization
        # print(f"Overall Util: {value:.1f}%")
        pass

    def _update_vram_display(self, value: float):
        # TODO: Update your UI element showing overall VRAM %
        # print(f"Overall VRAM: {value:.1f}%")
        # Check thresholds for alerts
        if value > 90:
            alert_service.alert("CRITICAL", f"VRAM High: {value:.1f}%")
        elif value > 75:
            alert_service.alert("WARNING", f"VRAM Warn: {value:.1f}%")

    def _update_temp_display(self, value: float):
        # TODO: Update your UI element showing overall Temperature
        # print(f"Overall Temp: {value:.1f}°C")
        pass
        
    def _update_power_display(self, value: float):
        # TODO: Update your UI element showing overall Power %
        # print(f"Overall Power: {value:.1f}%")
        pass
        
    def _update_full_metrics(self, metrics: dict):
        # This signal provides per-GPU data if needed
        # TODO: Update more detailed UI elements if necessary
        # print(f"Full metrics received for {len(metrics)} GPUs")
        pass
        
    def _export_current_view(self):
        print("Exporting current view...")
        # TODO: Determine active widget/view and call its export method
        # Example: 
        # if self.advanced_dock.isVisible():
        #    self.advanced_dock._export_png()
        # else:
        #    pass # Export main dashboard view? 
        pass
        
    def closeEvent(self, event):
        """Ensure telemetry thread stops on close."""
        print("Stopping telemetry worker...")
        telemetry_worker.stop()
        print("Telemetry worker stopped.")
        event.accept()

# --- Application Entry Point --- 

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # You might need to load icons/resources here
    # Example: load_resources()
    
    window = Dashboard()
    window.show()
    
    sys.exit(app.exec()) 