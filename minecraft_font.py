"""
Minecraft-style pixel font renderer for the launcher GUI.
Handles loading and displaying custom Minecraft-themed pixel art fonts.
"""

import tkinter as tk
from PIL import Image, ImageTk
import os


class MinecraftFontRenderer:
    """Renders text using Minecraft-style pixel art font sprites"""
    
    def __init__(self, sprite_sheet_path=None, char_width=8, char_height=8):
        """
        Initialize the font renderer.
        
        Args:
            sprite_sheet_path: Path to the sprite sheet image
            char_width: Width of each character in pixels
            char_height: Height of each character in pixels
        """
        self.char_width = char_width
        self.char_height = char_height
        self.char_sprites = {}
        self.sprite_sheet = None
        
        if sprite_sheet_path and os.path.exists(sprite_sheet_path):
            self.load_sprite_sheet(sprite_sheet_path)
    
    def load_sprite_sheet(self, path):
        """Load the sprite sheet image"""
        try:
            self.sprite_sheet = Image.open(path)
            self.extract_characters()
        except Exception as e:
            print(f"Error loading sprite sheet: {e}")
    
    def extract_characters(self):
        """Extract individual character sprites from the sprite sheet"""
        if not self.sprite_sheet:
            return
        
        # Character mapping based on typical sprite sheet layout
        # Row 1: A-Z, Row 2: 0-9, Row 3: symbols
        chars = []
        
        # Uppercase letters A-Z
        for i in range(26):
            chars.append(chr(ord('A') + i))
        
        # Numbers 0-9
        for i in range(10):
            chars.append(chr(ord('0') + i))
        
        # Common symbols
        symbols = " !@#$%^&*()-_=+[]{}|\\;:'\",.<>/?~"
        chars.extend(list(symbols))
        
        # Extract sprites (assuming they're laid out in a grid)
        sheet_width, sheet_height = self.sprite_sheet.size
        
        # Try to auto-detect character dimensions if not provided
        # This is a simplified version - you may need to adjust based on your sprite sheet
        cols = min(26, sheet_width // self.char_width)  # Assume max 26 chars per row
        
        char_index = 0
        y = 0
        while y < sheet_height and char_index < len(chars):
            x = 0
            while x < sheet_width and char_index < len(chars):
                if char_index < len(chars):
                    char = chars[char_index]
                    left = x
                    top = y
                    right = min(x + self.char_width, sheet_width)
                    bottom = min(y + self.char_height, sheet_height)
                    
                    char_img = self.sprite_sheet.crop((left, top, right, bottom))
                    self.char_sprites[char] = char_img
                    char_index += 1
                
                x += self.char_width
                
                if x >= sheet_width:
                    break
            
            y += self.char_height
            if y >= sheet_height:
                break
    
    def get_char_image(self, char, scale=2):
        """
        Get a scaled image for a character.
        
        Args:
            char: The character to render
            scale: Scale factor for the character (1 = original size)
        
        Returns:
            ImageTk.PhotoImage object or None
        """
        char_upper = char.upper()
        
        # Handle space character
        if char == ' ':
            # Return a blank image of the right width
            space_img = Image.new('RGBA', (self.char_width * scale, self.char_height * scale), (0, 0, 0, 0))
            return ImageTk.PhotoImage(space_img)
        
        # Get the character sprite
        if char_upper in self.char_sprites:
            char_img = self.char_sprites[char_upper]
            if scale > 1:
                new_size = (self.char_width * scale, self.char_height * scale)
                char_img = char_img.resize(new_size, Image.NEAREST)  # Use NEAREST for pixel art
            return ImageTk.PhotoImage(char_img)
        
        return None
    
    def render_text(self, text, scale=2):
        """
        Render text as a sequence of character images.
        
        Args:
            text: The text to render
            scale: Scale factor for characters
        
        Returns:
            List of (ImageTk.PhotoImage, x_offset) tuples
        """
        images = []
        x_offset = 0
        
        for char in text:
            char_img = self.get_char_image(char, scale)
            if char_img:
                images.append((char_img, x_offset))
                x_offset += self.char_width * scale
            else:
                # Unknown character - add a space
                x_offset += self.char_width * scale
        
        return images
    
    def create_text_label(self, parent, text, scale=2, **kwargs):
        """
        Create a Tkinter label with Minecraft-style text.
        
        Args:
            parent: Parent widget
            text: Text to display
            scale: Scale factor
            **kwargs: Additional arguments for Canvas widget
        
        Returns:
            Canvas widget with rendered text
        """
        images = self.render_text(text, scale)
        
        if not images:
            # Fallback to regular label if font not loaded
            return tk.Label(parent, text=text, **kwargs)
        
        # Calculate canvas size
        total_width = sum(img[1] + self.char_width * scale for img in images) if images else 0
        total_height = self.char_height * scale
        
        canvas = tk.Canvas(parent, width=total_width, height=total_height, 
                          bg=kwargs.get('bg', parent.cget('bg') if hasattr(parent, 'cget') else 'white'),
                          highlightthickness=0, **{k: v for k, v in kwargs.items() 
                          if k not in ['text', 'image']})
        
        # Draw characters
        x = 0
        for char_img, offset in images:
            canvas.create_image(x, 0, anchor=tk.NW, image=char_img)
            canvas.image_refs = getattr(canvas, 'image_refs', [])
            canvas.image_refs.append(char_img)  # Keep reference to prevent garbage collection
            x += self.char_width * scale
        
        return canvas


def create_title_with_font(parent, text, font_renderer=None, fallback_text=None):
    """
    Create a title label, using Minecraft font if available, otherwise regular text.
    
    Args:
        parent: Parent widget
        text: Text to display
        font_renderer: MinecraftFontRenderer instance (optional)
        fallback_text: Fallback text for regular label
    
    Returns:
        Widget (Canvas or Label)
    """
    if font_renderer and font_renderer.char_sprites:
        try:
            return font_renderer.create_text_label(parent, text, scale=3)
        except:
            pass
    
    # Fallback to regular label
    return tk.Label(parent, text=fallback_text or text, 
                   font=('Segoe UI', 18, 'bold'), 
                   foreground='#2c3e50')


def load_font_renderer(assets_dir="assets"):
    """
    Try to load a Minecraft font renderer from assets directory.
    
    Args:
        assets_dir: Directory containing font assets
    
    Returns:
        MinecraftFontRenderer instance or None
    """
    if not os.path.exists(assets_dir):
        return None
    
    # Look for common sprite sheet filenames
    sprite_files = [
        "minecraft_font.png",
        "font_sprite.png",
        "pixel_font.png",
        "font.png"
    ]
    
    for filename in sprite_files:
        path = os.path.join(assets_dir, filename)
        if os.path.exists(path):
            try:
                renderer = MinecraftFontRenderer(path, char_width=8, char_height=8)
                if renderer.char_sprites:
                    return renderer
            except Exception as e:
                print(f"Error loading font from {path}: {e}")
                continue
    
    return None

