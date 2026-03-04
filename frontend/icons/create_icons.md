# Icon Files Needed

The extension requires icon files. You can either:

1. **Create your own icons** (16x16, 48x48, 128x128 pixels) with a shield/security theme
2. **Use online icon generators** (e.g., favicon.io)
3. **Temporarily remove icon references** from manifest.json for testing

Place icon files here:
- `icon16.png` (16x16 pixels)
- `icon48.png` (48x48 pixels)  
- `icon128.png` (128x128 pixels)

Alternatively, you can use a simple Python script to generate placeholder icons:

```python
from PIL import Image, ImageDraw, ImageFont

for size in [16, 48, 128]:
    img = Image.new('RGB', (size, size), color='#1976d2')
    draw = ImageDraw.Draw(img)
    # Draw simple shield icon
    draw.ellipse([size//4, size//4, 3*size//4, 3*size//4], fill='white')
    img.save(f'icon{size}.png')
```
