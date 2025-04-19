import torch
import sys

# Redirect output to file
with open('torch_test_output.txt', 'w') as f:
    f.write(f"Python version: {sys.version}\n")
    f.write(f"PyTorch version: {torch.__version__}\n")
    f.write(f"CUDA available: {torch.cuda.is_available()}\n")
    if torch.cuda.is_available():
        f.write(f"CUDA version: {torch.version.cuda}\n")
        f.write(f"GPU devices: {torch.cuda.device_count()}\n")
        f.write(f"Current device: {torch.cuda.current_device()}\n")
        f.write(f"Device name: {torch.cuda.get_device_name(0)}\n")
    else:
        f.write("CUDA not available\n")

print("Test completed. Results saved to torch_test_output.txt")
input("Press Enter to continue...") 