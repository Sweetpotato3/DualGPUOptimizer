"""
Unified preset system that combines model settings,
persona, and template in a single JSON format.
"""

from __future__ import annotations

import json
import logging
import pathlib
from typing import Any, Dict, List

from PySide6 import QtCore as QtC
from PySide6 import QtWidgets as QtW

logger = logging.getLogger("DualGPUOptimizer.Presets")


class PresetManager:
    def __init__(self):
        self.preset_dir = pathlib.Path.home() / ".dualgpuopt" / "presets"
        self.preset_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Preset directory: {self.preset_dir}")

    def get_all_presets(self) -> List[str]:
        """Return list of available preset names"""
        presets = [p.stem for p in self.preset_dir.glob("*.json")]
        logger.debug(f"Found {len(presets)} presets: {presets}")
        return presets

    def load_preset(self, name: str) -> Dict[str, Any]:
        """Load preset by name"""
        path = self.preset_dir / f"{name}.json"
        if not path.exists():
            logger.warning(f"Preset {name} not found at {path}")
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"Loaded preset '{name}' with {len(data)} keys")
                return data
        except Exception as e:
            logger.error(f"Error loading preset {name}: {e}")
            return {}

    def save_preset(self, name: str, data: Dict[str, Any]) -> None:
        """Save preset data"""
        path = self.preset_dir / f"{name}.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                logger.info(f"Saved preset '{name}' to {path}")
        except Exception as e:
            logger.error(f"Error saving preset {name}: {e}")

    def delete_preset(self, name: str) -> bool:
        """Delete preset by name"""
        path = self.preset_dir / f"{name}.json"
        if path.exists():
            try:
                path.unlink()
                logger.info(f"Deleted preset '{name}'")
                return True
            except Exception as e:
                logger.error(f"Error deleting preset {name}: {e}")
                return False
        else:
            logger.warning(f"Cannot delete preset {name}: File not found")
            return False


class PresetDock(QtW.QDockWidget):
    """Qt dock widget for preset management"""

    preset_selected = QtC.Signal(dict)
    preset_saved = QtC.Signal(str)  # Signal emitted when a preset is saved

    def __init__(self, parent=None):
        super().__init__("Presets", parent)
        self.manager = PresetManager()

        # Create list view with details
        main_layout = QtW.QVBoxLayout()

        # Add filter box
        filter_layout = QtW.QHBoxLayout()
        filter_layout.addWidget(QtW.QLabel("Filter:"))
        self.filter_edit = QtW.QLineEdit()
        self.filter_edit.setPlaceholderText("Search presets...")
        self.filter_edit.textChanged.connect(self._filter_presets)
        filter_layout.addWidget(self.filter_edit)
        main_layout.addLayout(filter_layout)

        # Create list widget with details
        self.preset_list = QtW.QListWidget()
        self.preset_list.setAlternatingRowColors(True)
        self.preset_list.doubleClicked.connect(self._on_preset_selected)
        self.preset_list.setSelectionMode(QtW.QAbstractItemView.SingleSelection)
        main_layout.addWidget(self.preset_list)

        # Create toolbar
        toolbar = QtW.QToolBar()
        toolbar.addAction(QtW.QAction("New", self, triggered=self._create_preset))
        toolbar.addAction(QtW.QAction("Delete", self, triggered=self._delete_preset))
        toolbar.addAction(QtW.QAction("Refresh", self, triggered=self._refresh_list))
        main_layout.addWidget(toolbar)

        # Create info panel
        info_group = QtW.QGroupBox("Preset Info")
        info_layout = QtW.QFormLayout(info_group)

        self.preset_type = QtW.QLabel("")
        info_layout.addRow("Type:", self.preset_type)

        self.preset_model = QtW.QLabel("")
        info_layout.addRow("Model:", self.preset_model)

        self.preset_framework = QtW.QLabel("")
        info_layout.addRow("Framework:", self.preset_framework)

        main_layout.addWidget(info_group)

        # Add load button
        self.load_btn = QtW.QPushButton("Load Selected Preset")
        self.load_btn.clicked.connect(self._on_preset_selected)
        self.load_btn.setEnabled(False)
        main_layout.addWidget(self.load_btn)

        # Connect selection changed
        self.preset_list.itemSelectionChanged.connect(self._selection_changed)

        # Create container and set layout
        container = QtW.QWidget()
        container.setLayout(main_layout)
        self.setWidget(container)

        # Refresh preset list
        self._refresh_list()

    def _refresh_list(self):
        """Refresh preset list"""
        self.preset_list.clear()
        for name in self.manager.get_all_presets():
            self.preset_list.addItem(name)

        # Clear info panel
        self.preset_type.setText("")
        self.preset_model.setText("")
        self.preset_framework.setText("")
        self.load_btn.setEnabled(False)

    def _filter_presets(self, text):
        """Filter presets by name"""
        for i in range(self.preset_list.count()):
            item = self.preset_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def _selection_changed(self):
        """Handle selection change in preset list"""
        if self.preset_list.selectedItems():
            self.load_btn.setEnabled(True)
            name = self.preset_list.currentItem().text()
            data = self.manager.load_preset(name)

            # Update info panel
            self.preset_type.setText(data.get("type", "Unknown"))
            self.preset_model.setText(data.get("model_name", data.get("model_path", "Unknown")))
            self.preset_framework.setText(data.get("framework", "Unknown"))
        else:
            self.load_btn.setEnabled(False)

    def _on_preset_selected(self, index=None):
        """Handle preset selection/loading"""
        if not self.preset_list.selectedItems():
            return

        name = self.preset_list.currentItem().text()
        data = self.manager.load_preset(name)
        self.preset_selected.emit(data)
        logger.info(f"Selected preset: {name}")

    def _create_preset(self):
        """Create new preset"""
        name, ok = QtW.QInputDialog.getText(self, "New Preset", "Enter preset name:")

        if ok and name:
            # Create template preset
            data = {
                "name": name,
                "type": "template",
                "model_path": "",
                "model_name": "",
                "framework": "llama.cpp",
                "context_size": 2048,
                "gpu_settings": {
                    "gpu0_allocation": "50%",
                    "gpu1_allocation": "50%",
                    "max_context": "2048",
                    "layer_distribution": "Auto",
                },
                "prompt_template": "",
                "persona": "",
            }

            self.manager.save_preset(name, data)
            self._refresh_list()
            self.preset_saved.emit(name)

    def _delete_preset(self):
        """Delete selected preset"""
        current = self.preset_list.currentItem()
        if not current:
            return

        name = current.text()
        response = QtW.QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete preset '{name}'?",
            QtW.QMessageBox.Yes | QtW.QMessageBox.No,
        )

        if response == QtW.QMessageBox.Yes:
            self.manager.delete_preset(name)
            self._refresh_list()

    def save_current_state(self, name: str, data: Dict[str, Any]):
        """Save current state as preset"""
        self.manager.save_preset(name, data)
        self._refresh_list()
        self.preset_saved.emit(name)
