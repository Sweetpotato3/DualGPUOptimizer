"""
Generate a simple purple-themed icon for the DualGPUOptimizer
"""
from PIL import Image, ImageDraw
from pathlib import Path

# Create directory if it doesn't exist
icon_path = Path("dualgpuopt/assets/app_64.png")
icon_path.parent.mkdir(exist_ok=True)

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

# Save the image
img.save(icon_path)
print(f"Icon created at {icon_path}") 