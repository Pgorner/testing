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
INPUT_LINE_HEIGHT = 40  # Top area for displaying input

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
BG_COLOR = (0, 0, 0)             # Background: Black
INPUT_BG_COLOR = (255, 255, 255)   # Input line background: White
INPUT_TEXT_COLOR = (0, 0, 0)       # Input text: Black
KEY_FILL_COLOR = (50, 50, 50)      # Key background: Dark gray
KEY_OUTLINE_COLOR = (255, 255, 255)# Key outline: White
KEY_TEXT_COLOR = (255, 255, 255)   # Key text: White

# Use default font from PIL (you can load a TTF if preferred)
font = ImageFont.load_default()

# -------------------------
# Function to draw the interface
# -------------------------
def draw_interface(current_input):
    # Create a new image for the current frame
    image = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(image)
    
    # Draw the input line area at the top
    draw.rectangle([0, 0, SCREEN_WIDTH, INPUT_LINE_HEIGHT], fill=INPUT_BG_COLOR)
    draw.text((10, 10), current_input, font=font, fill=INPUT_TEXT_COLOR)
    
    # Draw the numpad keys
    for row in range(NUM_ROWS):
        for col in range(NUM_COLS):
            label = KEY_LAYOUT[row][col]
            x = col * KEY_WIDTH
            y = INPUT_LINE_HEIGHT + row * KEY_HEIGHT
            draw.rectangle([x, y, x + KEY_WIDTH, y + KEY_HEIGHT],
                           fill=KEY_FILL_COLOR, outline=KEY_OUTLINE_COLOR)
            # Center the label on the key
            text_size = draw.textsize(label, font=font)
            text_x = x + (KEY_WIDTH - text_size[0]) / 2
            text_y = y + (KEY_HEIGHT - text_size[1]) / 2
            draw.text((text_x, text_y), label, font=font, fill=KEY_TEXT_COLOR)
    
    return image

# -------------------------
# Main routine
# -------------------------
if __name__=='__main__':
    # Initialize display and clear screen
    disp = st7789.st7789()
    disp.clear()
    
    # Initialize touch controller
    touch = cst816d.cst816d()

    logging.info("Starting landscape numpad input interface")
    current_input = ""
    
    while True:
        # Draw the interface with the current input string and update the display
        image = draw_interface(current_input)
        disp.show_image(image)
        
        # Read touch data and get coordinates
        touch.read_touch_data()
        point, coordinates = touch.get_touch_xy()
        
        if point != 0 and coordinates:
            tx = coordinates[0]['x']
            ty = coordinates[0]['y']
            pressed_key = None
            
            # Determine which key is pressed based on touch coordinates
            for row in range(NUM_ROWS):
                for col in range(NUM_COLS):
                    x = col * KEY_WIDTH
                    y = INPUT_LINE_HEIGHT + row * KEY_HEIGHT
                    if (x <= tx <= x + KEY_WIDTH) and (y <= ty <= y + KEY_HEIGHT):
                        pressed_key = KEY_LAYOUT[row][col]
                        break
                if pressed_key:
                    break
            
            if pressed_key:
                if pressed_key == "Del":
                    # Remove last character from the input string
                    current_input = current_input[:-1]
                elif pressed_key == "Enter":
                    # For demonstration, print the input and then clear it
                    print("Entered:", current_input)
                    current_input = ""
                else:
                    # Append the pressed digit or character to the input string
                    current_input += pressed_key
                # Debounce delay to avoid multiple triggers
                time.sleep(0.3)
        
        time.sleep(0.02)
