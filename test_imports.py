import sys
print(f'Python version: {sys.version}')

# Test ctx_size import
try:
    print('CTX_SIZE module OK')
except ImportError as e:
    print(f'CTX_SIZE import error: {e}')

# Test layer_balance import
try:
    print('LAYER_BALANCE module OK')
except ImportError as e:
    print(f'LAYER_BALANCE import error: {e}')

# Test vram_reset import
try:
    print('VRAM_RESET module OK')
except ImportError as e:
    print(f'VRAM_RESET import error: {e}')

# Test mpolicy import
try:
    print('MPOLICY module OK')
except ImportError as e:
    print(f'MPOLICY import error: {e}')