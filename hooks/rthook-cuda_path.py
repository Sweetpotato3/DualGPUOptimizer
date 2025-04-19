# Ensures DLL search-path contains PyInstaller's temp dir (Windows)
import os, sys, pathlib
root = pathlib.Path(getattr(sys, "_MEIPASS", ".")).resolve()
if hasattr(os, "add_dll_directory"):
    os.add_dll_directory(str(root))
os.environ["PATH"] = f"{root}{os.pathsep}{os.environ.get('PATH','')}" 