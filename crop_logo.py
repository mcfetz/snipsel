import os
from PIL import Image

def process_logo():
    img_path = '/Users/daniel/.gemini/antigravity/brain/448dfc80-df36-470c-a77c-6151a0e8ee2b/snipsel_logo_concepts_1776974577866.png'
    out_dir = '/Users/daniel/development/snipsel-website/assets'
    
    img = Image.open(img_path).convert('RGB')
    w, h = img.size
    
    # Crop top right quadrant exactly
    box = (w // 2, 0, w, h // 2)
    quadrant = img.crop(box)
    
    # Sample background color from the top right corner
    bg_color = quadrant.getpixel((quadrant.width - 1, 0))
    threshold = 40
    
    left = quadrant.width
    top = quadrant.height
    right = 0
    bottom = 0
    
    for x in range(quadrant.width):
        for y in range(quadrant.height):
            p = quadrant.getpixel((x, y))
            diff = abs(p[0] - bg_color[0]) + abs(p[1] - bg_color[1]) + abs(p[2] - bg_color[2])
            if diff > threshold:
                if x < left: left = x
                if y < top: top = y
                if x > right: right = x
                if y > bottom: bottom = y

    # The bounding box dimensions
    bw = right - left
    bh = bottom - top
    
    # Make the box square
    size = max(bw, bh)
    
    # Calculate center of the bounding box
    cx = left + bw // 2
    cy = top + bh // 2
    
    # New box size including padding (e.g. 15%)
    pad = int(size * 0.15)
    final_size = size + pad * 2
    
    # Create an image filled with background color
    square = Image.new('RGB', (final_size, final_size), bg_color)
    
    # Extract coordinates
    ex_left = cx - final_size // 2
    ex_top = cy - final_size // 2
    ex_right = ex_left + final_size
    ex_bottom = ex_top + final_size
    
    # Valid region to copy over
    quad_left = max(0, ex_left)
    quad_top = max(0, ex_top)
    quad_right = min(quadrant.width, ex_right)
    quad_bottom = min(quadrant.height, ex_bottom)
    
    valid_region = quadrant.crop((quad_left, quad_top, quad_right, quad_bottom))
    
    dest_x = quad_left - ex_left
    dest_y = quad_top - ex_top
    square.paste(valid_region, (dest_x, dest_y))
    
    # Resize and save
    sizes = {
        'logo_512.png': 512,
        'logo_192.png': 192,
        'apple-touch-icon.png': 180,
        'favicon-32x32.png': 32
    }
    
    for filename, sz in sizes.items():
        resized = square.resize((sz, sz), Image.Resampling.LANCZOS)
        out_path = os.path.join(out_dir, filename)
        resized.save(out_path)
        print(f"Saved perfectly centered {filename}")

    # Create ICO
    ico_img = square.resize((32, 32), Image.Resampling.LANCZOS)
    ico_path = os.path.join(out_dir, 'favicon.ico')
    ico_img.save(ico_path, format='ICO')
    print("Saved perfectly centered favicon.ico")

if __name__ == "__main__":
    process_logo()
