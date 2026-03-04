"""
Generate placeholder icons for VeriSight extension
Creates simple shield icons in 3 sizes
"""
try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Pillow not installed. Install with: pip install Pillow")
    exit(1)

import os

def create_icon(size, output_path):
    """Create a simple shield icon"""
    img = Image.new('RGB', (size, size), color='#1976d2')
    draw = ImageDraw.Draw(img)
    
    # Draw shield shape (simplified)
    # Shield outline
    shield_points = [
        (size // 2, size // 8),  # Top
        (size // 4, size // 4),
        (size // 4, 3 * size // 4),
        (size // 2, 7 * size // 8),  # Bottom point
        (3 * size // 4, 3 * size // 4),
        (3 * size // 4, size // 4),
    ]
    draw.polygon(shield_points, fill='white')
    
    # Add checkmark inside
    check_color = '#4caf50'
    line_width = max(1, size // 16)
    # Draw simple checkmark
    draw.line([
        (size // 2 - size // 8, size // 2),
        (size // 2 - size // 16, size // 2 + size // 8)
    ], fill=check_color, width=line_width)
    draw.line([
        (size // 2 - size // 16, size // 2 + size // 8),
        (size // 2 + size // 6, size // 2 - size // 8)
    ], fill=check_color, width=line_width)
    
    img.save(output_path)
    print(f"Created {output_path}")

if __name__ == '__main__':
    # Create icons directory if it doesn't exist
    icon_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'icons')
    os.makedirs(icon_dir, exist_ok=True)
    
    # Generate icons
    for size in [16, 48, 128]:
        output_path = os.path.join(icon_dir, f'icon{size}.png')
        create_icon(size, output_path)
    
    print("Icons generated successfully!")
