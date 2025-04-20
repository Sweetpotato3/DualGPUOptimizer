import sys, types
from PyInstaller.utils.hooks import collect_dynamic_libs

def _lazy(name: str):
    mod = types.ModuleType(name)
    mod.__getattr__ = lambda *_: None    # any attr access returns None
    sys.modules[name] = mod

# Create lazy stubs for problematic modules
for m in (
    "torch._inductor",                # full package
    "torch._inductor.kernel",         # the crashing sub-module
    "torch._dynamo",
    "torch._functorch.aot_autograd",
):
    _lazy(m)

# Pattern-based DLL collection
patterns = ("cublas*", "cudart*", "cudnn*", "nccl*", "cusparse*")
binaries = sum((collect_dynamic_libs("torch", match=p) for p in patterns), [])

# Add any other torch modules we need but exclude the problematic ones
hiddenimports = []
excludedimports = [
    "torch._inductor",
    "torch._inductor.kernel",
    "torch._dynamo",
    "torch._functorch.aot_autograd",
    "torch.compiler",
    "torch.distributed.fsdp",
    "torch.distributed._tensor",
]