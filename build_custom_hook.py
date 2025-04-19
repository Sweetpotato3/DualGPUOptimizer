#!/usr/bin/env python3
"""
Build script with custom hooks to override built-in torch hook.
"""
import os
import subprocess
import sys
from pathlib import Path
import shutil

def create_custom_hook():
    """Create custom hooks directory with overridden torch hook."""
    hooks_dir = Path("custom_hooks")
    hooks_dir.mkdir(exist_ok=True)
    
    # Create a simplified torch hook that doesn't try to collect all submodules
    torch_hook_path = hooks_dir / "hook-torch.py"
    with open(torch_hook_path, "w") as f:
        f.write("""
# -*- coding: utf-8 -*-
# Simplified hook-torch.py that doesn't try to collect all submodules
# Instead, we just include the basic modules we need

hiddenimports = [
    'torch', 
    'torch.cuda',
    'torch.nn',
    'torch.utils.data',
    'torch.autocast',
]

excludedimports = [
    'torch._dynamo',
    'torch._inductor',
    'torch._functorch',
    'torch.distributed',
    'torch.testing',
    'torch.utils.tensorboard',
]
""")
    return hooks_dir

def main():
    """
    Build the application with PyInstaller using custom hooks.
    """
    print("Building DualGPUOptimizer application...")
    
    # Create custom hooks directory
    hooks_dir = create_custom_hook()
    
    # Get the absolute path of the nvml.dll
    nvml_path = os.path.abspath("C:\\Windows\\System32\\nvml.dll")
    
    # Get the absolute path of the assets and presets directories
    root_dir = Path(__file__).parent
    app_dir = root_dir / "dual_gpu_optimizer" / "dualgpuopt"
    assets_dir = os.path.abspath(app_dir / "assets")
    presets_dir = os.path.abspath(app_dir / "presets")
    icon_path = os.path.abspath(app_dir / "assets" / "app_icon.ico")
    main_py = os.path.abspath(app_dir / "__main__.py")
    
    # Run PyInstaller with explicit parameters
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name=DualGPUOptimizer",
        f"--add-binary={nvml_path};.",
        f"--add-data={assets_dir};dualgpuopt/assets",
        f"--add-data={presets_dir};dualgpuopt/presets",
        f"--icon={icon_path}",
        f"--additional-hooks-dir={hooks_dir}",
        "--hidden-import=pynvml",
        "--hidden-import=rich",
        "--hidden-import=rich.console",
        "--hidden-import=rich.panel",
        "--hidden-import=rich.table",
        "--hidden-import=rich.progress",
        "--hidden-import=rich.layout",
        "--hidden-import=rich.text",
        "--hidden-import=tomli_w",
        "--hidden-import=tomllib",
        "--hidden-import=argparse",
        "--hidden-import=concurrent.futures",
        "--hidden-import=psutil",
        "--hidden-import=asyncio",
        "--hidden-import=ttkbootstrap",
        "--hidden-import=ttkbootstrap.style",
        "--hidden-import=ttkbootstrap.widgets",
        "--hidden-import=ttkbootstrap.tooltip",
        "--hidden-import=dualgpuopt.gui.constants",
        "--collect-submodules=ttkbootstrap",
        main_py
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    
    if result.returncode != 0:
        print("❌ Build failed!")
        sys.exit(1)
    
    print("✅ Build completed successfully!")
    print(f"Application is available at: {os.path.abspath('dist/DualGPUOptimizer')}")
    
    # Clean up
    shutil.rmtree(hooks_dir)

if __name__ == "__main__":
    main() 