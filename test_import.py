try:
    import PySide6
    print(f'Successfully imported PySide6 {PySide6.__version__}')
except Exception as e:
    print(f'Error importing PySide6: {type(e).__name__}: {e}')
