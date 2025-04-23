# Simplified hook-torch.py that includes necessary torch modules
# while avoiding problematic ones that cause PyInstaller to crash

import sys

sys.setrecursionlimit(5000)  # Increase recursion limit for torch analysis

from PyInstaller.utils.hooks import collect_data_files

# Explicitly list the torch modules we need
hiddenimports = [
    "torch",
    "torch.cuda",
    "torch.nn",
    "torch.utils.data",
    "torch.autocast",
    "torch.jit",
    "torch.fx",
    "torch.backends",
    "torch.backends.cudnn",
    "torch.backends.cuda",
    "torch._C",
    "torch.cuda._utils",
    "torch.cuda.amp",
    "torch.cuda.comm",
]

# Always exclude these problematic modules
excludedimports = [
    "torch._dynamo",
    "torch._inductor",
    "torch._functorch",
    "torch.distributed",
    "torch.testing",
    "torch.utils.tensorboard",
]

# Collect all necessary data files including DLLs
datas = collect_data_files("torch")
