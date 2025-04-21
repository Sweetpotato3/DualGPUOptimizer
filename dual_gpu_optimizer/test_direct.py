import importlib.util
import pathlib
path = pathlib.Path("dualgpuopt/gui/constants.py")
print(f"Constants path: {path}, exists: {path.exists()}")
if path.exists():
    spec = importlib.util.spec_from_file_location("constants", str(path))
    constants = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(constants)
    print(f"APP_NAME: {constants.APP_NAME}")
