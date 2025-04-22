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
    from dualgpuopt.qt.dashboard_tab import DashboardTab
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
        
        # --- Setup Main Dashboard Tab ---
        self.dashboard_tab = DashboardTab(parent=self)
        self.setCentralWidget(self.dashboard_tab)
        self.dashboard_tab.set_telemetry_worker(telemetry_worker)
        print("Dashboard tab initialized.")
        
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
        # Connect signals to UI update methods
        telemetry_worker.util_updated.connect(self._update_util_display)
        telemetry_worker.vram_updated.connect(self._update_vram_display)
        telemetry_worker.temp_updated.connect(self._update_temp_display)
        telemetry_worker.power_updated.connect(self._update_power_display)
        telemetry_worker.metrics_updated.connect(self._update_full_metrics)
        
        telemetry_worker.start() # Start collecting data
        print("Telemetry worker started and signals connected.")

    # --- Slot Methods for Signals ---
    
    def _apply_preset(self, preset_data: dict):
        print(f"Applying preset: {preset_data.get('name', 'Unnamed')}")
        # Apply the preset data to the engine
        if not preset_data:
            alert_service.alert("WARNING", "Empty preset data received")
            return
            
        try:
            # Update status to show we're applying preset
            self.statusBar().showMessage(f"Applying preset: {preset_data.get('name', 'Unnamed')}...")
            
            # Apply model path and settings to the engine
            if 'model_path' in preset_data:
                self.engine.set_model_path(preset_data['model_path'])
                
            if 'gpu_settings' in preset_data:
                self.engine.configure(**preset_data['gpu_settings'])
                
            # Apply any template or persona data if present
            if 'template' in preset_data:
                self.engine.set_prompt_template(preset_data['template'])
                
            if 'persona' in preset_data:
                self.engine.set_persona(preset_data['persona'])
                
            # Update status to success
            self.statusBar().showMessage(f"Preset '{preset_data.get('name', 'Unnamed')}' applied successfully", 3000)
        except Exception as e:
            alert_service.alert("CRITICAL", f"Failed to apply preset: {str(e)}")

    def _update_util_display(self, value: float):
        # Forward the utilization update to the dashboard tab
        self.statusBar().showMessage(f"GPU Utilization: {value:.1f}%", 2000)
        # In a real implementation, you might update a chart or other UI element here
        self.advanced_dock.memory_timeline.add_data_point(value)

    def _update_vram_display(self, value: float):
        # Forward the VRAM update and check thresholds for alerts
        if value > 90:
            alert_service.alert("CRITICAL", f"VRAM High: {value:.1f}%")
        elif value > 75:
            alert_service.alert("WARNING", f"VRAM Warn: {value:.1f}%")
            
        # Update status bar temporarily
        self.statusBar().showMessage(f"VRAM Usage: {value:.1f}%", 2000)

    def _update_temp_display(self, value: float):
        # Forward the temperature update and check for critical temps
        if value > 85:
            alert_service.alert("CRITICAL", f"GPU Temperature High: {value:.1f}°C")
        elif value > 75:
            alert_service.alert("WARNING", f"GPU Temperature Elevated: {value:.1f}°C")
        
        # Update status bar temporarily
        self.statusBar().showMessage(f"GPU Temperature: {value:.1f}°C", 2000)
        
    def _update_power_display(self, value: float):
        # Forward the power update and check for high power consumption
        if value > 95:
            alert_service.alert("CRITICAL", f"Power Usage High: {value:.1f}%")
        
        # Update status bar temporarily
        self.statusBar().showMessage(f"Power Usage: {value:.1f}%", 2000)
        
    def _update_full_metrics(self, metrics: dict):
        # This signal provides per-GPU data - update the advanced dock
        # and also pass through to the dashboard tab's components
        
        # If memory timeline is available, add data points based on average memory usage
        if hasattr(self.advanced_dock, 'memory_timeline') and metrics:
            # Calculate average memory usage across all GPUs
            avg_memory = sum(m.memory_percent for m in metrics.values()) / len(metrics)
            self.advanced_dock.memory_timeline.add_data_point(avg_memory)
        
    def _export_current_view(self):
        print("Exporting current view...")
        
        # Determine which view is active and call the appropriate export method
        if self.advanced_dock.isVisible():
            # If advanced dock is visible, export from it
            self.advanced_dock._export_png()
        else:
            # Export the main dashboard view
            from PySide6.QtGui import QPixmap
            from PySide6.QtWidgets import QFileDialog
            
            # Capture the current central widget (dashboard tab)
            pixmap = self.dashboard_tab.grab()
            
            # Ask for save location
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Dashboard View", "dashboard.png", "PNG Files (*.png)"
            )
            
            if file_path:
                pixmap.save(file_path, "PNG")
                self.statusBar().showMessage(f"Dashboard exported to {file_path}", 3000)
        
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