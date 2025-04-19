from pathlib import Path
APP_NAME        = "DualGPUOptimizer"
THEME           = "darkly"
ASSET_DIR       = Path(__file__).parent / "assets" # Use relative path from this file
VRAM_WARN_MB    = 256          # show yellow status if reclaim < 256 MB
STATUS_DURATION = 5000         # ms 