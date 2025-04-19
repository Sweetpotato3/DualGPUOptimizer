#!/usr/bin/env python3.13
# build.py – fail‑proof standalone builder for Dual‑GPU Optimiser
from __future__ import annotations

import ctypes.util as _ctu
import os, shutil, subprocess, sys, platform, re, pathlib
from typing import Optional, List

ROOT = pathlib.Path(__file__).parent.resolve()
LIB_DIR = ROOT / "build" / "libs"
LIB_DIR.mkdir(parents=True, exist_ok=True)


def _which(cmd: str) -> Optional[str]:
    for path in os.environ.get("PATH", "").split(os.pathsep):
        full = pathlib.Path(path) / cmd
        if full.exists():
            return str(full)
    return None


def _find_nvml() -> pathlib.Path:
    override = os.getenv("NVML_PATH")
    if override and pathlib.Path(override).exists():
        return pathlib.Path(override)

    cand = _ctu.find_library("nvidia-ml")
    if cand and pathlib.Path(cand).exists():
        return pathlib.Path(cand)

    sys_name = platform.system()
    if sys_name == "Windows":
        dll = pathlib.Path(os.getenv("WINDIR", "C:\\Windows")) / "System32" / "nvml.dll"
        if dll.exists():
            return dll
        # Check Program Files location
        program_files = os.getenv("ProgramFiles", "C:/Program Files")
        dll = pathlib.Path(program_files) / "NVIDIA Corporation" / "NVSMI" / "nvml.dll"
        if dll.exists():
            return dll
    elif sys_name == "Linux":
        for glib in ("/usr/lib", "/usr/lib64", "/usr/lib/x86_64-linux-gnu"):
            for so in pathlib.Path(glib).glob("libnvidia-ml.so*"):
                return so
    elif sys_name == "Darwin":
        dy = pathlib.Path("/usr/local/cuda/lib/libnvidia-ml.dylib")
        if dy.exists():
            return dy

    smi = _which("nvidia-smi")
    if smi:
        out = subprocess.run([smi, "-q"], capture_output=True, text=True, errors="ignore").stdout
        m = re.search(r"NVML Library\s*:\s*(.*)", out)
        if m and pathlib.Path(m.group(1)).exists():
            return pathlib.Path(m.group(1))

    raise RuntimeError("NVML library not found – set NVML_PATH or ensure NVIDIA driver is installed.")


def _linux_libcuda() -> Optional[pathlib.Path]:
    if platform.system() != "Linux":
        return None
    for p in ("/usr/lib", "/usr/lib64", "/usr/lib/x86_64-linux-gnu"):
        so = pathlib.Path(p) / "libcuda.so.1"
        if so.exists():
            return so
    return None


def _pyi_cmd(exe_name: str, nvml_path: pathlib.Path, extras: List[pathlib.Path]) -> List[str]:
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--clean",
        # "--windowed",  # Comment out the windowed flag to show console output
        "--name", exe_name,
        "--add-binary", f"{nvml_path}{os.pathsep}.",
        "--hidden-import", "pynvml",
        "--hidden-import", "rich",
        "--hidden-import", "rich.console",
        "--hidden-import", "rich.panel",
        "--hidden-import", "rich.table",
        "--hidden-import", "rich.progress",
        "--hidden-import", "rich.layout",
        "--hidden-import", "rich.text",
        "--hidden-import", "tomli_w",
        "--hidden-import", "tomllib",
        "--hidden-import", "argparse",
        "--hidden-import", "concurrent.futures",
        "--hidden-import", "psutil",
        "--hidden-import", "torch",
        "--hidden-import", "torch.cuda",
        "--hidden-import", "torch.autocast",
        "--hidden-import", "prometheus_client",
        "--hidden-import", "asyncio",
        "--hidden-import", "ttkbootstrap",
        "--hidden-import", "ttkbootstrap.style",
        "--hidden-import", "ttkbootstrap.widgets",
        "--hidden-import", "ttkbootstrap.tooltip",
        "--collect-submodules", "ttkbootstrap",
        "--hidden-import",
        "pystray._win32" if platform.system() == "Windows" else "pystray._xorg",
    ]
    for extra in extras:
        cmd.extend(["--add-binary", f"{extra}{os.pathsep}."])
    
    # Add assets directory if it exists
    assets_dir = ROOT / "dual_gpu_optimizer" / "dualgpuopt" / "assets"
    if assets_dir.exists():
        cmd.extend(["--add-data", f"{assets_dir}{os.pathsep}dualgpuopt/assets"])

    # Add presets directory if it exists
    presets_dir = ROOT / "dual_gpu_optimizer" / "dualgpuopt" / "presets"
    if presets_dir.exists():
        cmd.extend(["--add-data", f"{presets_dir}{os.pathsep}dualgpuopt/presets"])
    
    # Add icon if it exists
    icon_path = assets_dir / "app_icon.ico"
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    else:
        print(f"Warning: Icon file not found at {icon_path}")
    
    # Add entry point script last
    cmd.append(str(ROOT / "dual_gpu_optimizer" / "dualgpuopt" / "__main__.py"))
    
    return cmd


def main() -> None:
    print("🔍  Locating NVIDIA libraries …")
    nvml = _find_nvml()
    extras: List[pathlib.Path] = []
    cuda_so = _linux_libcuda()
    if cuda_so:
        extras.append(cuda_so)

    print(f"✅  NVML detected → {nvml}")
    for lib in [nvml, *extras]:
        shutil.copy2(lib, LIB_DIR)

    exe_name = "DualGPUOptimizer"
    cmd = _pyi_cmd(exe_name, nvml, extras)
    print("🚀  Running PyInstaller …")
    print(f"Command: {' '.join(cmd)}")
    subprocess.check_call(cmd)

    dist_path = ROOT / "dist" / (exe_name + (".exe" if platform.system() == "Windows" else ""))
    if dist_path.exists():
        print(f"🎉  Build complete → {dist_path}")
    else:
        print("⚠️  Build finished, but output missing – check PyInstaller logs.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"❌  Build failed: {exc}")
        sys.exit(1) 