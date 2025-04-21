#!/usr/bin/env python3
"""
Build script with custom hooks to override built-in torch hook.
"""
import os
import subprocess
import sys
from pathlib import Path
import shutil

# Increase Python's recursion limit for analyzing deep modules
sys.setrecursionlimit(5000)

def create_custom_hook():
    """Create custom hooks directory with overridden torch hook."""
    hooks_dir = Path("custom_hooks")
    hooks_dir.mkdir(exist_ok=True)

    # Create a simplified torch hook that doesn't try to collect all submodules
    torch_hook_path = hooks_dir / "hook-torch.py"
    with open(torch_hook_path, "w") as f:
        f.write("""
# -*- coding: utf-8 -*-
# Simplified hook-torch.py that includes necessary torch modules
# while avoiding problematic ones that cause PyInstaller to crash

import sys
sys.setrecursionlimit(5000)  # Increase recursion limit for torch analysis

from PyInstaller.utils.hooks import collect_data_files

# Explicitly list the torch modules we need
hiddenimports = [
    'torch',
    'torch.cuda',
    'torch.nn',
    'torch.utils.data',
    'torch.autocast',
    'torch.jit',
    'torch.fx',
    'torch.backends',
    'torch.backends.cudnn',
    'torch.backends.cuda',
    'torch._C',
    'torch.cuda._utils',
    'torch.cuda.amp',
    'torch.cuda.comm',
]

# Always exclude these problematic modules
excludedimports = [
    'torch._dynamo',
    'torch._inductor',
    'torch._functorch',
    'torch.distributed',
    'torch.testing',
    'torch.utils.tensorboard',
]

# Collect all necessary data files including DLLs
datas = collect_data_files('torch')
""")

    # Create a prometheus_client hook
    prometheus_hook_path = hooks_dir / "hook-prometheus_client.py"
    with open(prometheus_hook_path, "w") as f:
        f.write("""
# -*- coding: utf-8 -*-
# Hook for prometheus_client

# Include all submodules
hiddenimports = [
    'prometheus_client',
    'prometheus_client.core',
    'prometheus_client.exposition',
    'prometheus_client.metrics',
    'prometheus_client.metrics_core',
    'prometheus_client.utils',
    'prometheus_client.registry',
]
""")

    return hooks_dir

def find_torch_dlls():
    """Find torch DLLs to include in the build."""
    try:
        import torch
        torch_path = Path(torch.__file__).parent
        dll_paths = []

        # Add primary torch lib directory
        lib_path = torch_path / "lib"
        if lib_path.exists():
            dll_paths.extend([(str(dll), ".") for dll in lib_path.glob("*.dll")])

        # Add cuda DLLs if available
        cuda_lib_path = torch_path / "lib" / "cuda"
        if cuda_lib_path.exists():
            dll_paths.extend([(str(dll), "lib/cuda") for dll in cuda_lib_path.glob("*.dll")])

        return dll_paths
    except ImportError:
        print("Warning: torch not found in environment")
        return []

def create_spec_file(hooks_dir, torch_dlls, nvml_path, assets_dir, presets_dir, icon_path, main_py):
    """Create a custom .spec file with proper configuration."""
    spec_path = Path("DualGPUOptimizer_full.spec")

    # Format the binaries and data for the spec file
    binaries_str = f"[('C:\\\\Windows\\\\System32\\\\nvml.dll', '.')]"
    for dll_path, target_dir in torch_dlls:
        binaries_str = binaries_str[:-1] + f", (r'{dll_path}', '{target_dir}')]"

    datas_str = f"[(r'{assets_dir}', 'dualgpuopt/assets'), (r'{presets_dir}', 'dualgpuopt/presets')]"

    with open(spec_path, "w") as f:
        f.write(f"""# -*- mode: python ; coding: utf-8 -*-
import sys
sys.setrecursionlimit(5000)  # Increase recursion limit
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

a = Analysis(
    [r'{main_py}'],
    pathex=['.'],
    binaries={binaries_str},
    datas={datas_str},
    hiddenimports=[
        'pynvml', 'rich', 'rich.console', 'rich.panel', 'rich.table',
        'rich.progress', 'rich.layout', 'rich.text', 'tomli_w',
        'tomllib', 'argparse', 'concurrent.futures', 'psutil',
        'asyncio', 'ttkbootstrap', 'ttkbootstrap.style',
        'ttkbootstrap.widgets', 'ttkbootstrap.tooltip',
        'dualgpuopt.gui.constants', 'prometheus_client',
        'torch', 'torch.cuda', 'torch.autocast'
    ],
    hookspath=[r'{hooks_dir.resolve()}'],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add torch and other package data files
a.datas += collect_data_files('torch')
a.datas += collect_data_files('ttkbootstrap')

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DualGPUOptimizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r'{icon_path}',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DualGPUOptimizer',
)
""")

    return spec_path

def main():
    """
    Build the application with PyInstaller using custom hooks.
    """
    print("Building DualGPUOptimizer application with all features...")

    # Create custom hooks directory
    hooks_dir = create_custom_hook()

    # Get the torch DLLs
    torch_dlls = find_torch_dlls()

    # Get the absolute path of the nvml.dll
    nvml_path = os.path.abspath("C:\\Windows\\System32\\nvml.dll")

    # Get the absolute path of the assets and presets directories
    root_dir = Path(__file__).parent
    app_dir = root_dir / "dual_gpu_optimizer" / "dualgpuopt"
    assets_dir = os.path.abspath(app_dir / "assets")
    presets_dir = os.path.abspath(app_dir / "presets")
    icon_path = os.path.abspath(app_dir / "assets" / "app_icon.ico")
    main_py = os.path.abspath(app_dir / "__main__.py")

    # Create a spec file with the right configuration
    spec_path = create_spec_file(
        hooks_dir, torch_dlls, nvml_path, assets_dir, presets_dir, icon_path, main_py
    )

    # Run PyInstaller with the spec file
    cmd = [
        "pyinstaller",
        str(spec_path),
        "--noconfirm",
        "--clean"
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