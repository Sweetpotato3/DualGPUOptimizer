#!/usr/bin/env python3
"""
Build script for DualGPUOptimizer that disables built-in torch hook.
"""
import os
import subprocess
import sys
import shutil
import tempfile
from pathlib import Path

def create_empty_hook():
    """
    Create a temporary directory with an empty torch hook to override the built-in one.
    """
    temp_dir = tempfile.mkdtemp(prefix="pyinstaller_hooks_")
    
    # Create an empty hook for torch to bypass the problematic hook
    with open(os.path.join(temp_dir, "hook-torch.py"), "w") as f:
        f.write("""
# -*- coding: utf-8 -*-
# Minimal torch hook to avoid the built-in hook's subprocess issues
hiddenimports = [
    'torch', 
    'torch.cuda',
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
    
    # Create a hook for prometheus_client
    with open(os.path.join(temp_dir, "hook-prometheus_client.py"), "w") as f:
        f.write("""
# -*- coding: utf-8 -*-
# Hook for prometheus_client
hiddenimports = [
    'prometheus_client.core',
    'prometheus_client.exposition',
    'prometheus_client.metrics',
]
""")
    
    return temp_dir

def copy_required_dlls(dist_dir):
    """Copy required DLLs to the distribution directory."""
    # Check if torch is available
    try:
        import torch
        torch_lib_dir = Path(torch.__file__).parent / "lib"
        
        if not torch_lib_dir.exists():
            print(f"Warning: torch lib directory not found at {torch_lib_dir}")
            return
        
        # Create lib directory in dist
        torch_dist_dir = Path(dist_dir) / "torch" / "lib"
        torch_dist_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy essential DLLs
        for dll in torch_lib_dir.glob("*.dll"):
            shutil.copy2(dll, torch_dist_dir)
            print(f"Copied {dll.name} to {torch_dist_dir}")
    
    except ImportError:
        print("Warning: torch not found, skipping DLL copy")

def main():
    """
    Build the application with PyInstaller.
    """
    print("Building DualGPUOptimizer application with minimal torch integration...")
    
    # Create a temporary directory with an empty torch hook
    hooks_dir = create_empty_hook()
    
    try:
        # Get the absolute path of the nvml.dll
        nvml_path = os.path.abspath("C:\\Windows\\System32\\nvml.dll")
        
        # Get the absolute path of the assets and presets directories
        root_dir = Path(__file__).parent
        app_dir = root_dir / "dual_gpu_optimizer" / "dualgpuopt"
        assets_dir = os.path.abspath(app_dir / "assets")
        presets_dir = os.path.abspath(app_dir / "presets")
        icon_path = os.path.abspath(app_dir / "assets" / "app_icon.ico")
        main_py = os.path.abspath(app_dir / "__main__.py")
        
        # Build command with our custom hook directory
        cmd = [
            "pyinstaller",
            "--noconfirm",
            "--clean",
            "--windowed",
            "--name=DualGPUOptimizer",
            f"--additional-hooks-dir={hooks_dir}",
            f"--add-binary={nvml_path};.",
            f"--add-data={assets_dir};dualgpuopt/assets",
            f"--add-data={presets_dir};dualgpuopt/presets",
            f"--icon={icon_path}",
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
            "--hidden-import=torch",
            "--hidden-import=torch.cuda",
            "--hidden-import=asyncio",
            "--hidden-import=ttkbootstrap",
            "--hidden-import=ttkbootstrap.style",
            "--hidden-import=ttkbootstrap.widgets",
            "--hidden-import=ttkbootstrap.tooltip",
            "--hidden-import=dualgpuopt.gui.constants",
            "--hidden-import=prometheus_client",
            "--collect-submodules=ttkbootstrap",
            main_py
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=False)
        
        if result.returncode != 0:
            print("❌ Build failed!")
            sys.exit(1)
        
        print("✅ Build completed successfully!")
        dist_dir = os.path.abspath("dist/DualGPUOptimizer")
        print(f"Application is available at: {dist_dir}")
        
        # Copy required DLLs
        copy_required_dlls(dist_dir)
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(hooks_dir)

if __name__ == "__main__":
    main() 