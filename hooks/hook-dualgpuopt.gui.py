"""
Hook for dualgpuopt.gui to ensure all files are collected
"""
import os
from pathlib import Path
from PyInstaller.utils.hooks import get_module_file_attribute, collect_data_files

# Get the location of the dualgpuopt.gui package
try:
    gui_path = Path(get_module_file_attribute('dualgpuopt.gui'))
    package_path = gui_path.parent
    
    # Collect all Python files in the gui directory
    datas = []
    if gui_path.exists():
        for py_file in gui_path.glob("*.py"):
            datas.append((str(py_file), os.path.join("dualgpuopt", "gui")))
except (ImportError, ModuleNotFoundError):
    # Package not found - might be in development mode
    datas = []

# Collect all data files too
datas.extend(collect_data_files('dualgpuopt.gui', includes=['*.py', '*.png', '*.json'])) 