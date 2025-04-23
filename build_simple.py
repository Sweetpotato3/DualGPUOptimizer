#!/usr/bin/env python3
"""
Simple build script for DualGPUOptimizer using PyInstaller.
Bypasses the default torch hook that tries to collect all submodules.
"""
import os
import subprocess
import sys
from pathlib import Path


def main():
    """
    Build the application with PyInstaller bypassing the torch hook.
    """
    print("Building DualGPUOptimizer application...")

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
        "--hidden-import=torch.autocast",
        "--hidden-import=asyncio",
        "--hidden-import=ttkbootstrap",
        "--hidden-import=ttkbootstrap.style",
        "--hidden-import=ttkbootstrap.widgets",
        "--hidden-import=ttkbootstrap.tooltip",
        "--hidden-import=dualgpuopt.gui.constants",
        "--collect-submodules=ttkbootstrap",
        "--exclude-module=torch._dynamo",
        "--exclude-module=torch._inductor",
        "--exclude-module=torch._functorch.aot_autograd",
        "--exclude-module=torch.distributed",
        "--exclude-module=torch.testing",
        "--exclude-module=torch.utils.tensorboard",
        main_py,
    ]

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)

    if result.returncode != 0:
        print("❌ Build failed!")
        sys.exit(1)

    print("✅ Build completed successfully!")
    print(f"Application is available at: {os.path.abspath('dist/DualGPUOptimizer')}")


if __name__ == "__main__":
    main()
