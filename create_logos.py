#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os

def create_bart_logo(width, height, output_path):
    """Create a placeholder BART logo with the specified dimensions"""
    # Create a new image with a blue background (BART colors)
    img = Image.new('RGB', (width, height), color=(0, 50, 98))
    draw = ImageDraw.Draw(img)
    
    # Try to use a built-in font, falling back to default if not available
    try:
        # Adjust font size based on image dimensions
        font_size = min(height // 2, width // 10)
        font = ImageFont.truetype("Arial", font_size)
    except IOError:
        # If truetype font is not available, use default
        font = ImageFont.load_default()
    
    # Add text "BART" in white
    bart_text = "BART"
    # Calculate text size to center it
    try:
        text_width, text_height = draw.textsize(bart_text, font=font)
    except:
        # For newer PIL versions
        try:
            text_width, text_height = font.getsize(bart_text)
        except:
            # If all else fails, estimate
            text_width, text_height = len(bart_text) * font_size // 2, font_size
            
    # Center the text
    position = ((width - text_width) // 2, (height - text_height) // 2)
    
    # Draw the text
    draw.text(position, bart_text, fill=(255, 255, 255), font=font)
    
    # Save the image
    img.save(output_path)
    print(f"Created logo: {output_path}")

# Ensure the directory exists
logo_dir = "assets/bart_logos"
os.makedirs(logo_dir, exist_ok=True)

# Create logos for all the standard dimensions
dimensions = [
    (32, 32),
    (64, 32),
    (64, 64),
    (128, 32),
    (128, 64)
]

for width, height in dimensions:
    # Create the logo filename in the format expected by main.py
    filename = f"bart-w{width}h{height}.png"
    output_path = os.path.join(logo_dir, filename)
    # Also create a copy in the assets root as that's what main.py expects
    root_output_path = os.path.join("assets", filename)
    
    # Generate the logo
    create_bart_logo(width, height, output_path)
    # Also save to root assets directory
    create_bart_logo(width, height, root_output_path)

print("All BART logo placeholders have been created.")