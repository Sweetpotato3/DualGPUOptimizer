"""
Unified preset system that combines model settings, 
persona, and template in a single JSON format.
"""
from __future__ import annotations
import json
import pathlib
from typing import Dict, Any, Optional, List
from PySide6 import QtWidgets as QtW, QtCore as QtC

class PresetManager:
    def __init__(self):
        self.preset_dir = pathlib.Path.home() / ".dualgpuopt" / "presets"
        self.preset_dir.mkdir(parents=True, exist_ok=True)
        
    def get_all_presets(self) -> List[str]:
        """Return list of available preset names"""
        return [p.stem for p in self.preset_dir.glob("*.json")]
        
    def load_preset(self, name: str) -> Dict[str, Any]:
        """Load preset by name"""
        path = self.preset_dir / f"{name}.json"
        if not path.exists():
            return {}
            
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    def save_preset(self, name: str, data: Dict[str, Any]) -> None:
        """Save preset data"""
        path = self.preset_dir / f"{name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
    def delete_preset(self, name: str) -> bool:
        """Delete preset by name"""
        path = self.preset_dir / f"{name}.json"
        if path.exists():
            path.unlink()
            return True
        return False

class PresetDock(QtW.QDockWidget):
    """Qt dock widget for preset management"""
    preset_selected = QtC.Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__("Presets", parent)
        self.manager = PresetManager()
        
        # Create list view
        self.preset_list = QtW.QListWidget()
        self.preset_list.doubleClicked.connect(self._on_preset_selected)
        self._refresh_list()
        
        # Create toolbar
        toolbar = QtW.QToolBar()
        toolbar.addAction(QtW.QAction("New", self, triggered=self._create_preset))
        toolbar.addAction(QtW.QAction("Delete", self, triggered=self._delete_preset))
        toolbar.addAction(QtW.QAction("Refresh", self, triggered=self._refresh_list))
        
        # Layout
        layout = QtW.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.preset_list)
        
        container = QtW.QWidget()
        container.setLayout(layout)
        self.setWidget(container)
        
    def _refresh_list(self):
        """Refresh preset list"""
        self.preset_list.clear()
        for name in self.manager.get_all_presets():
            self.preset_list.addItem(name)
            
    def _on_preset_selected(self, index):
        """Handle preset selection"""
        name = self.preset_list.currentItem().text()
        data = self.manager.load_preset(name)
        self.preset_selected.emit(data)
        
    def _create_preset(self):
        """Create new preset"""
        name, ok = QtW.QInputDialog.getText(
            self, "New Preset", "Enter preset name:"
        )
        
        if ok and name:
            # Create template preset
            data = {
                "model_path": "",
                "prompt_template": "",
                "persona": "",
                "gpu_settings": {
                    "gpu_layers": 32,
                    "tensor_parallel": 2
                }
            }
            
            self.manager.save_preset(name, data)
            self._refresh_list()
            
    def _delete_preset(self):
        """Delete selected preset"""
        current = self.preset_list.currentItem()
        if not current:
            return
            
        name = current.text()
        response = QtW.QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete preset '{name}'?",
            QtW.QMessageBox.Yes | QtW.QMessageBox.No
        )
        
        if response == QtW.QMessageBox.Yes:
            self.manager.delete_preset(name)
            self._refresh_list()
            
    def save_current_state(self, name: str, data: Dict[str, Any]):
        """Save current state as preset"""
        self.manager.save_preset(name, data)
        self._refresh_list() 