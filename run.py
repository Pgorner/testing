#!/usr/bin/python
# -*- coding: UTF-8 -*-
import time
import logging
import st7789
from PIL import Image, ImageDraw, ImageFont

# -------------------------
# Configuration Parameters
# -------------------------
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240

# Use the default PIL font (or load a TTF font if desired)
font = ImageFont.load_default()

# -------------------------
# Function to create the base test image
# -------------------------
def create_base_image():
    """
    Create a base image with corner labels and arrows.
    """
    image = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw corner labels (in yellow)
    draw.text((5, 5), "TL", font=font, fill=(255, 255, 0))
    draw.text((SCREEN_WIDTH - 30, 5), "TR", font=font, fill=(255, 255, 0))
    draw.text((5, SCREEN_HEIGHT - 15), "BL", font=font, fill=(255, 255, 0))
    draw.text((SCREEN_WIDTH - 30, SCREEN_HEIGHT - 15), "BR", font=font, fill=(255, 255, 0))
    
    # Draw red arrows pointing toward the corners
    arrow_color = (255, 0, 0)
    line_width = 3
    # Top left arrow: from (20,20) to (0,0)
    draw.line([(20, 20), (0, 0)], fill=arrow_color, width=line_width)
    # Top right arrow: from (SCREEN_WIDTH-20,20) to (SCREEN_WIDTH,0)
    draw.line([(SCREEN_WIDTH - 20, 20), (SCREEN_WIDTH, 0)], fill=arrow_color, width=line_width)
    # Bottom left arrow: from (20, SCREEN_HEIGHT-20) to (0, SCREEN_HEIGHT)]
    draw.line([(20, SCREEN_HEIGHT - 20), (0, SCREEN_HEIGHT)], fill=arrow_color, width=line_width)
    # Bottom right arrow: from (SCREEN_WIDTH-20, SCREEN_HEIGHT-20) to (SCREEN_WIDTH, SCREEN_HEIGHT)]
    draw.line([(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20), (SCREEN_WIDTH, SCREEN_HEIGHT)], fill=arrow_color, width=line_width)
    
    # Overlay transformation text in the center (in green)
    text = "180° + horizontal flip (preferred)"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (SCREEN_WIDTH - text_width) / 2
    y = (SCREEN_HEIGHT - text_height) / 2
    draw.text((x, y), text, font=font, fill=(0, 255, 0))
    
    return image

# -------------------------
# Function to apply the preferred transformation
# -------------------------
def apply_preferred_transformation(image):
    """
    Apply the transformation:
      1. Rotate the image 180°.
      2. Flip it horizontally.
    """
    transformed = image.rotate(180, expand=False)
    transformed = transformed.transpose(Image.FLIP_LEFT_RIGHT)
    return transformed

# -------------------------
# Main routine
# -------------------------
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    disp = st7789.st7789()  # Initialize the display
    disp.clear()
    
    base_image = create_base_image()
    final_image = apply_preferred_transformation(base_image)
    
    # Display the image with the preferred orientation
    disp.show_image(final_image)
    
    print("Preferred orientation (180° rotation + horizontal flip) is displayed.")
    input("Press Enter to exit.")
