import torch
import sys

print(f"Python version: {sys.version}")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    device_count = torch.cuda.device_count()
    print(f"Number of GPU devices: {device_count}")

    for i in range(device_count):
        device_props = torch.cuda.get_device_properties(i)
        print(f"\nDevice {i}: {device_props.name}")
        print(f"  Compute capability: {device_props.major}.{device_props.minor}")
        print(f"  Total memory: {device_props.total_memory / 1024 / 1024:.0f} MB")

    # Try a simple tensor operation on GPU
    x = torch.rand(5, 3).cuda()
    print(f"\nSample tensor on GPU:\n{x}")
else:
    print("CUDA is not available")

input("Press Enter to exit...")