import sys
import os

print(f"Python version: {sys.version}")

try:
    import torch
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"CUDA device count: {torch.cuda.device_count()}")
        print(f"Current CUDA device: {torch.cuda.current_device()}")
        print(f"CUDA device name: {torch.cuda.get_device_name(0)}")
        print(f"CUDA device properties: {torch.cuda.get_device_properties(0)}")
    else:
        print("CUDA is not available. Checking environment variables:")
        for var in ['CUDA_VISIBLE_DEVICES', 'CUDA_PATH', 'PATH']:
            print(f"  {var}: {os.environ.get(var, 'Not set')}")
except ImportError as e:
    print(f"Error importing torch: {e}")
except Exception as e:
    print(f"Error checking CUDA: {e}")

print("\nPress Enter to exit...")
input() 