"""
Helper script to set up Minecraft font from image files.
This script helps extract and prepare font sprite sheets for the launcher.
"""

import os
from PIL import Image

def prepare_font_image(image_path, output_path="assets/minecraft_font.png", char_width=8, char_height=8):
    """
    Prepare a font sprite sheet image.
    
    Args:
        image_path: Path to your font image
        output_path: Where to save the prepared font
        char_width: Width of each character
        char_height: Height of each character
    """
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        return False
    
    try:
        # Create assets directory if it doesn't exist
        os.makedirs("assets", exist_ok=True)
        
        # Load and save the image
        img = Image.open(image_path)
        img.save(output_path)
        print(f"Font image saved to: {output_path}")
        print(f"Image size: {img.size[0]}x{img.size[1]} pixels")
        print("\nThe launcher will automatically use this font!")
        return True
    except Exception as e:
        print(f"Error processing image: {e}")
        return False


if __name__ == "__main__":
    print("=== Minecraft Font Setup ===")
    print("\nThis script helps you set up your custom Minecraft font for the launcher.")
    print("\nInstructions:")
    print("1. Save your font sprite sheet image")
    print("2. Run this script with: python setup_font.py")
    print("3. Or specify the image path as an argument")
    print("\nSupported image formats: PNG, JPG, JPEG")
    
    import sys
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        prepare_font_image(image_path)
    else:
        print("\nTo use this script:")
        print("  python setup_font.py <path_to_your_font_image.png>")
        print("\nOr simply copy your font image to:")
        print("  assets/minecraft_font.png")

