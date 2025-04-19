"""
Custom PyInstaller hook for torch to exclude problematic modules
that require CUDA build tools at import time.
"""
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("torch")
excludedimports = [
    "torch._dynamo", 
    "torch._inductor", 
    "torch._functorch.aot_autograd"
] 