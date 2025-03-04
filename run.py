#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys 
import time
import logging
import st7789
import cst816d
from PIL import Image, ImageDraw, ImageFont

# -------------------------
# Configuration Parameters
# -------------------------
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240
INPUT_LINE_HEIGHT = 40  # Top area for displaying input (for visual reference)

NUM_ROWS = 4
NUM_COLS = 3
KEY_WIDTH = SCREEN_WIDTH // NUM_COLS
KEY_HEIGHT = (SCREEN_HEIGHT - INPUT_LINE_HEIGHT) // NUM_ROWS

# Define numpad layout. Last row: "0", "Del" (delete), "Enter" (submit/clear)
KEY_LAYOUT = [
    ["7", "8", "9"],
    ["4", "5", "6"],
    ["1", "2", "3"],
    ["0", "Del", "Enter"]
]

# Colors (in RGB)
BG_COLOR = (0, 0, 0)              # Background: Black
INPUT_BG_COLOR = (255, 255, 255)    # Input line background: White
INPUT_TEXT_COLOR = (0, 0, 0)        # Input text: Black
KEY_FILL_COLOR = (50, 50, 50)       # Key background: Dark gray
KEY_OUTLINE_COLOR = (255, 255, 255) # Key outline: White
KEY_TEXT_COLOR = (255, 255, 255)    # Key text: White

# Use default font from PIL (you can load a TTF font if desired)
font = ImageFont.load_default()

# -------------------------
# Function to draw the interface
# -------------------------
def draw_interface():
    # Create a new image for the current frame
    image = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(image)
    
    # Draw the input line area at the top (for visual reference)
    draw.rectangle([0, 0, SCREEN_WIDTH, INPUT_LINE_HEIGHT], fill=INPUT_BG_COLOR)
    draw.text((10, 10), "Touch a key...", font=font, fill=INPUT_TEXT_COLOR)
    
    # Draw the numpad keys
    for row in range(NUM_ROWS):
        for col in range(NUM_COLS):
            label = KEY_LAYOUT[row][col]
            x = col * KEY_WIDTH
            y = INPUT_LINE_HEIGHT + row * KEY_HEIGHT
            draw.rectangle([x, y, x + KEY_WIDTH, y + KEY_HEIGHT],
                           fill=KEY_FILL_COLOR, outline=KEY_OUTLINE_COLOR)
            # Use textbbox (avoids deprecation warnings)
            bbox = draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = x + (KEY_WIDTH - text_width) / 2
            text_y = y + (KEY_HEIGHT - text_height) / 2
            draw.text((text_x, text_y), label, font=font, fill=KEY_TEXT_COLOR)
    
    return image

# -------------------------
# Main routine (test program)
# -------------------------
if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    
    # Initialize display and clear screen
    disp = st7789.st7789()
    disp.clear()
    
    # Initialize touch controller
    touch = cst816d.cst816d()

    logging.info("Starting numpad key test program")
    
    while True:
        # Draw and flip the interface to correct the mirroring
        image = draw_interface()
        flipped_image = image.transpose(Image.FLIP_LEFT_RIGHT)
        disp.show_image(flipped_image)
        
        # Read touch data and get coordinates
        touch.read_touch_data()
        point, coordinates = touch.get_touch_xy()
        if point != 0 and coordinates:
            raw_x = coordinates[0]['x']
            raw_y = coordinates[0]['y']
            # Adjust the x coordinate: subtract from (SCREEN_WIDTH - 1)
            tx = (SCREEN_WIDTH - 1) - raw_x
            ty = raw_y

            # Determine which key is pressed based on adjusted coordinates
            pressed_key = None
            for row in range(NUM_ROWS):
                for col in range(NUM_COLS):
                    key_x = col * KEY_WIDTH
                    key_y = INPUT_LINE_HEIGHT + row * KEY_HEIGHT
                    if (key_x <= tx <= key_x + KEY_WIDTH) and (key_y <= ty <= key_y + KEY_HEIGHT):
                        pressed_key = KEY_LAYOUT[row][col]
                        break
                if pressed_key:
                    break

            # Print debug info to console
            print("============================================")
            print(f"Raw touch coordinates: x={raw_x}, y={raw_y}")
            print(f"Adjusted coordinates:  x={tx}, y={ty}")
            if pressed_key:
                print(f"Mapped key: {pressed_key}")
            else:
                print("No key mapped for these coordinates.")
            
            # Ask user for feedback via console input
            user_feedback = input("Please type the key you actually pressed (or press Enter if correct): ").strip()
            if user_feedback:
                print(f"User reported: {user_feedback}")
            else:
                print("User confirmed the mapped key is correct.")
            print("============================================\n")
            
            # Small pause for debouncing (and to allow time for next touch)
            time.sleep(0.5)
        time.sleep(0.02)
