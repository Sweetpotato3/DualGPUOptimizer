"""
Generate a simple purple-themed icon for the DualGPUOptimizer
"""
from PIL import Image, ImageDraw
from pathlib import Path

# Create directory if it doesn't exist
assets_dir = Path("dualgpuopt/assets")
assets_dir.mkdir(exist_ok=True)
png_path = assets_dir / "app_64.png"
ico_path = assets_dir / "windowsicongpu.ico"

# Create a 64x64 image with a transparent background
img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw a gradient background square
for y in range(64):
    # Purple gradient
    color = (100 + int(155 * y / 64), 50, 200 - int(100 * y / 64), 255)
    draw.line([(0, y), (64, y)], fill=color)

# Draw simple GPU-like rectangles
draw.rectangle([10, 15, 54, 35], fill=(200, 80, 230, 255), outline=(255, 255, 255, 200), width=1)
draw.rectangle([10, 40, 54, 60], fill=(120, 200, 230, 255), outline=(255, 255, 255, 200), width=1)

# Draw connecting lines
draw.line([(32, 35), (32, 40)], fill=(255, 255, 255, 200), width=2)
draw.line([(22, 35), (22, 40)], fill=(255, 255, 255, 200), width=2)
draw.line([(42, 35), (42, 40)], fill=(255, 255, 255, 200), width=2)

# Save the PNG image
img.save(png_path)
print(f"PNG icon created at {png_path}")

# Save as ICO file (Windows icon format)
try:
    img.save(ico_path, format='ICO', sizes=[(64, 64)])
    print(f"ICO icon created at {ico_path}")
except Exception as e:
    print(f"Failed to create ICO file: {e}")
    # Try alternate method if the first one fails
    try:
        # Resize to common icon sizes
        img_16 = img.resize((16, 16), Image.LANCZOS)
        img_32 = img.resize((32, 32), Image.LANCZOS)
        img_48 = img.resize((48, 48), Image.LANCZOS)

        img_16.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
        print(f"ICO icon created at {ico_path} (alternative method)")
    except Exception as e2:
        print(f"Failed to create ICO file (alternative method): {e2}")