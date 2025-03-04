#!/usr/bin/python
# -*- coding: UTF-8 -*-
import time
import logging
import st7789
import cst816d  # if needed for later touch tests
from PIL import Image, ImageDraw, ImageFont

# -------------------------
# Configuration Parameters
# -------------------------
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240

# Use default font (or load a TTF if you prefer)
font = ImageFont.load_default()

# -------------------------
# Define test cases
# -------------------------
# Each test case defines a rotation (degrees, counterclockwise) and a flip mode.
# flip can be None, "horizontal", "vertical", or "both"
test_cases = [
    {"rotation": 0,   "flip": None,         "description": "Rotation 0°, no flip"},
    {"rotation": 0,   "flip": "horizontal",   "description": "Rotation 0°, horizontal flip"},
    {"rotation": 90,  "flip": None,         "description": "Rotation 90°, no flip"},
    {"rotation": 90,  "flip": "horizontal",   "description": "Rotation 90°, horizontal flip"},
    {"rotation": 180, "flip": None,         "description": "Rotation 180°, no flip"},
    {"rotation": 180, "flip": "horizontal",   "description": "Rotation 180°, horizontal flip"},
    {"rotation": 270, "flip": None,         "description": "Rotation 270°, no flip"},
    {"rotation": 270, "flip": "horizontal",   "description": "Rotation 270°, horizontal flip"}
]

# -------------------------
# Functions to draw the test image
# -------------------------
def create_base_image():
    """
    Create a base image that shows the four screen corners.
    In each corner the program prints a label:
      TL - Top Left
      TR - Top Right
      BL - Bottom Left
      BR - Bottom Right
    Additionally, red arrow lines point from near the corner toward the actual corner.
    """
    image = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw corner labels in yellow
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
    
    return image

def overlay_test_text(image, text):
    """
    Overlay the test case description text in the center of the image.
    """
    draw = ImageDraw.Draw(image)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (SCREEN_WIDTH - text_width) / 2
    y = (SCREEN_HEIGHT - text_height) / 2
    draw.text((x, y), text, font=font, fill=(0, 255, 0))
    return image

def apply_transformations(image, rotation, flip):
    """
    Apply a rotation (in degrees, counterclockwise) and an optional flip to the image.
    The order is: first rotate, then flip if specified.
    """
    transformed = image.rotate(rotation, expand=False)
    if flip is not None:
        if flip == "horizontal":
            transformed = transformed.transpose(Image.FLIP_LEFT_RIGHT)
        elif flip == "vertical":
            transformed = transformed.transpose(Image.FLIP_TOP_BOTTOM)
        elif flip == "both":
            transformed = transformed.transpose(Image.FLIP_LEFT_RIGHT)
            transformed = transformed.transpose(Image.FLIP_TOP_BOTTOM)
    return transformed

# -------------------------
# Main test loop
# -------------------------
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    disp = st7789.st7789()  # Initialize your display
    disp.clear()

    print("Starting display orientation test.")
    print("For each test image, note the corner labels and arrows and then input if it looks correct (y/n).")
    
    for test in test_cases:
        # Create the base image and overlay the test description text.
        base = create_base_image()
        text = test["description"]
        base = overlay_test_text(base, text)
        
        # Apply the specified rotation and flip.
        transformed = apply_transformations(base, test["rotation"], test["flip"])
        
        # Show the image on the display.
        disp.show_image(transformed)
        
        # Print test case info to the console.
        print("============================================")
        print("Test case: " + test["description"])
        print("Rotation: {}°, Flip: {}".format(test["rotation"], test["flip"]))
        user_input = input("Does the printed text and arrows point correctly? (y/n) [Press Enter to continue]: ").strip().lower()
        if user_input == "y":
            print("Test confirmed as correct for this case.")
        else:
            print("Test reported as not correct for this case.")
        print("============================================\n")
        time.sleep(1)  # Pause before next test

    print("Display orientation test complete.")
