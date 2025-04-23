import sys

import torch

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
        print(f"  CUDA cores: {device_props.multi_processor_count}")

    # Run a simple test to verify everything works
    print("\nRunning test computation on GPU:")
    x = torch.randn(1000, 1000).cuda()
    y = torch.randn(1000, 1000).cuda()
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)

    start.record()
    z = torch.matmul(x, y)
    end.record()

    torch.cuda.synchronize()
    print(f"Matrix multiplication time: {start.elapsed_time(end):.2f} ms")
    print(f"Result shape: {z.shape}, Sum: {z.sum().item():.2f}")
else:
    print("CUDA is not available")

print("\nPress Enter to exit...")
input()
