import importlib.util
import sys
from pathlib import Path
print('Looking for constants.py in the project')
for root, dirs, files in Path('.').glob('**/constants.py'):
