import importlib.util
import sys
import os

print('Looking for constants.py in the project')

# Find all constants.py files in the project
constants_files = []
for root, dirs, files in os.walk('.'):
    for file in files:
        if file == 'constants.py':
            full_path = os.path.join(root, file)
            constants_files.append(full_path)
            print(f"Found: {full_path}")

if not constants_files:
    print("No constants.py files found!")
    sys.exit(1)

for constants_path in constants_files:
    print(f"\nTrying to import: {constants_path}")
    try:
        spec = importlib.util.spec_from_file_location("constants", constants_path)
        constants = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(constants)

        print("Successfully imported constants module!")

        # Try to access some attributes
        if hasattr(constants, 'APP_NAME'):
            print(f"APP_NAME: {constants.APP_NAME}")
        else:
            print("APP_NAME not found in module")

        if hasattr(constants, 'THEME'):
            print(f"THEME: {constants.THEME}")
        else:
            print("THEME not found in module")

        if hasattr(constants, 'GPU_COLORS'):
            print(f"GPU_COLORS: {constants.GPU_COLORS}")
        else:
            print("GPU_COLORS not found in module")
    except Exception as e:
        print(f"Error importing constants file: {e}")