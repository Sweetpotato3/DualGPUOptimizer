"""
Create an icon for DualGPUOptimizer
This script generates a basic GPU icon with purple colors
"""
import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def create_gpu_icon(size=256, bg_color="#2D1E40", fg_color="#8A54FD", save_to=None):
    """Create a simple GPU icon
    
    Args:
        size: Icon size in pixels
        bg_color: Background color
        fg_color: Foreground color
        save_to: Path to save the icon, defaults to dualgpuopt/resources
        
    Returns:
        Path to the saved icon
    """
    # Create a blank image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a gradient background - rounded rectangle
    bg_rect = [(size//8, size//8), (size - size//8, size - size//8)]
    draw.rounded_rectangle(bg_rect, fill=bg_color, radius=size//10)
    
    # Draw stylized dual GPU representation
    # First GPU
    gpu1_rect = [(size//4, size//4), (size*3//4, size//2)]
    draw.rounded_rectangle(gpu1_rect, fill=fg_color, radius=size//20)
    
    # Second GPU
    gpu2_rect = [(size//4, size*9//16), (size*3//4, size*3//4)]
    draw.rounded_rectangle(gpu2_rect, fill=fg_color, radius=size//20)
    
    # Draw connection lines
    line_width = size//30
    line_padding = size//16
    
    # Connection points
    draw.rounded_rectangle(
        [(size//2 - line_width//2, size//2), 
         (size//2 + line_width//2, size*9//16)],
        fill=fg_color, radius=line_width//2
    )
    
    # "Ports" on GPUs
    for i, y_pos in enumerate([size//3, size*5//8]):
        for j in range(3):
            port_x = size*5//16 + j*size//8
            port_size = size//40
            draw.rectangle(
                [(port_x - port_size, y_pos - port_size), 
                 (port_x + port_size, y_pos + port_size)],
                fill="#FFFFFF"
            )
    
    # Save locations
    if save_to is None:
        # Use default resources directory
        resources_dir = Path("dualgpuopt") / "resources"
        resources_dir.mkdir(exist_ok=True, parents=True)
        save_to = resources_dir
    else:
        save_to = Path(save_to)
        save_to.mkdir(exist_ok=True, parents=True)
    
    # Save PNG version
    png_path = save_to / "icon.png"
    img.save(png_path)
    
    # Save ICO version (Windows)
    ico_path = save_to / "icon.ico"
    # Create different sizes for the ico file
    sizes = [16, 32, 48, 64, 128, 256]
    imgs = [img.resize((s, s), Image.LANCZOS) for s in sizes]
    imgs[0].save(ico_path, format='ICO', sizes=[(s, s) for s in sizes], append_images=imgs[1:])
    
    print(f"Icon saved to {png_path} and {ico_path}")
    return ico_path

if __name__ == "__main__":
    # Create icons in different locations to ensure they're available
    create_gpu_icon(save_to="dualgpuopt/resources")
    create_gpu_icon(save_to="assets")
    print("Icons created successfully!") 