#!/usr/bin/env python3
"""
Simple direct build script for DualGPUOptimizer.
"""
import os
import subprocess
import sys
from pathlib import Path

def main():
    """
    Build the application using a direct approach (no spec file).
    """
    print("Building DualGPUOptimizer application with all features...")

    # Get the torch DLLs
    try:
        import torch
        torch_path = Path(torch.__file__).parent
        torch_lib_path = torch_path / "lib"
    except ImportError:
        print("WARNING: torch not found in environment")
        torch_lib_path = None

    # Get the absolute path of the nvml.dll
    nvml_path = os.path.abspath("C:\\Windows\\System32\\nvml.dll")

    # Get the absolute path of the assets and presets directories
    root_dir = Path(__file__).parent
    app_dir = root_dir / "dual_gpu_optimizer" / "dualgpuopt"
    assets_dir = os.path.abspath(app_dir / "assets")
    presets_dir = os.path.abspath(app_dir / "presets")
    icon_path = os.path.abspath(app_dir / "assets" / "app_icon.ico")
    main_py = os.path.abspath(app_dir / "__main__.py")

    # Basic command with key options
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name=DualGPUOptimizer",
        f"--add-binary={nvml_path};."
    ]

    # Add torch DLLs if available
    if torch_lib_path and torch_lib_path.exists():
        for dll in torch_lib_path.glob("*.dll"):
            cmd.append(f"--add-binary={dll};.")

    # Add data files
    cmd.extend([
        f"--add-data={assets_dir};dualgpuopt/assets",
        f"--add-data={presets_dir};dualgpuopt/presets",
        f"--icon={icon_path}"
    ])

    # Add essential hidden imports
    for module in [
        "pynvml", "rich", "rich.console", "rich.panel", "rich.table",
        "rich.progress", "rich.layout", "rich.text", "tomli_w",
        "tomllib", "argparse", "concurrent.futures", "psutil",
        "asyncio", "ttkbootstrap", "ttkbootstrap.style",
        "ttkbootstrap.widgets", "ttkbootstrap.tooltip",
        "dualgpuopt.gui.constants", "prometheus_client"
    ]:
        cmd.append(f"--hidden-import={module}")

    # Add torch modules if available
    if torch_lib_path:
        cmd.extend([
            "--hidden-import=torch",
            "--hidden-import=torch.cuda"
        ])

    # Add specific torch modules we know we need
    cmd.append("--collect-submodules=ttkbootstrap")

    # Exclude problematic modules
    cmd.extend([
        "--exclude-module=torch._dynamo",
        "--exclude-module=torch._inductor",
        "--exclude-module=torch._functorch",
        "--exclude-module=torch.distributed",
        "--exclude-module=torch.testing",
        "--exclude-module=torch.utils.tensorboard"
    ])

    # Add main script
    cmd.append(main_py)

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)

    if result.returncode != 0:
        print("❌ Build failed!")
        sys.exit(1)

    print("✅ Build completed successfully!")
    print(f"Application is available at: {os.path.abspath('dist/DualGPUOptimizer')}")

if __name__ == "__main__":
    main()