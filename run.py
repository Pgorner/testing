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
INPUT_LINE_HEIGHT = 40  # Top area reserved for text

NUM_ROWS = 4
NUM_COLS = 3
KEY_WIDTH = SCREEN_WIDTH // NUM_COLS
KEY_HEIGHT = (SCREEN_HEIGHT - INPUT_LINE_HEIGHT) // NUM_ROWS  # e.g., 50 if (240-40)/4

# Numpad layout: rows are:
# Row0: "7", "8", "9"
# Row1: "4", "5", "6"
# Row2: "1", "2", "3"
# Row3: "0", "Del", "Enter"
KEY_LAYOUT = [
    ["7", "8", "9"],
    ["4", "5", "6"],
    ["1", "2", "3"],
    ["0", "Del", "Enter"]
]

# Colors (RGB)
BG_COLOR = (0, 0, 0)              # Black background
INPUT_BG_COLOR = (255, 255, 255)    # White input area
INPUT_TEXT_COLOR = (0, 0, 0)        # Black text for input area
KEY_FILL_COLOR = (50, 50, 50)       # Dark gray for keys
KEY_OUTLINE_COLOR = (255, 255, 255) # White outlines for keys
KEY_TEXT_COLOR = (255, 255, 255)    # White text for keys

# Use the default PIL font (or load a TTF if desired)
font = ImageFont.load_default()

# -------------------------
# Calibration values (based on your logs)
# -------------------------
# Observed raw_x values:
#   ~171 at the top (expected row0) and ~35 at the bottom (expected row3)
RAW_MAX_X = 171.0  # corresponds to the top of key area (INPUT_LINE_HEIGHT)
RAW_MIN_X = 35.0   # corresponds to the bottom (SCREEN_HEIGHT)
RAW_RANGE = RAW_MAX_X - RAW_MIN_X  # ~136

# -------------------------
# Drawing the interface
# -------------------------
def draw_interface():
    image = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(image)
    # Draw the top input area (for reference)
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
            # Use textbbox to compute text size (avoids deprecation warnings)
            bbox = draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = x + (KEY_WIDTH - text_width) / 2
            text_y = y + (KEY_HEIGHT - text_height) / 2
            draw.text((text_x, text_y), label, font=font, fill=KEY_TEXT_COLOR)
    return image

# -------------------------
# Transform raw touch coordinates to virtual display coordinates
# -------------------------
def transform_touch(raw_x, raw_y):
    """
    Map raw_x from [RAW_MAX_X, RAW_MIN_X] linearly to [INPUT_LINE_HEIGHT, SCREEN_HEIGHT].
    Use raw_y directly as the horizontal coordinate.
    """
    # Invert raw_x so that a higher raw_x (near 171) maps to the top of the key area.
    # Linear mapping: raw_x = RAW_MAX_X -> virtual_y = INPUT_LINE_HEIGHT,
    #                raw_x = RAW_MIN_X -> virtual_y = SCREEN_HEIGHT.
    virtual_y = ((RAW_MAX_X - raw_x) / RAW_RANGE) * (SCREEN_HEIGHT - INPUT_LINE_HEIGHT) + INPUT_LINE_HEIGHT
    virtual_x = raw_y
    return virtual_x, virtual_y

# -------------------------
# Main Test Program
# -------------------------
if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    disp = st7789.st7789()
    disp.clear()
    touch = cst816d.cst816d()

    logging.info("Starting numpad key test program with proper coordinate transformation")

    while True:
        # Draw the interface and show it
        image = draw_interface()
        disp.show_image(image)
        
        # Read touch data from the sensor
        touch.read_touch_data()
        point, coordinates = touch.get_touch_xy()
        if point != 0 and coordinates:
            raw_x = coordinates[0]['x']
            raw_y = coordinates[0]['y']
            # Transform the raw sensor coordinates
            virt_x, virt_y = transform_touch(raw_x, raw_y)
            
            # Determine which key is pressed
            # The keys are drawn starting at y = INPUT_LINE_HEIGHT.
            # Compute the row index from the vertical coordinate.
            row_index = int((virt_y - INPUT_LINE_HEIGHT) // KEY_HEIGHT)
            if row_index < 0:
                row_index = 0
            if row_index >= NUM_ROWS:
                row_index = NUM_ROWS - 1
            # Column index from the horizontal coordinate
            col_index = int(virt_x // KEY_WIDTH)
            if col_index < 0:
                col_index = 0
            if col_index >= NUM_COLS:
                col_index = NUM_COLS - 1

            mapped_key = KEY_LAYOUT[row_index][col_index]
            
            # Print debug information
            print("============================================")
            print("Raw touch coordinates: x={}, y={}".format(raw_x, raw_y))
            print("Transformed virtual coordinates: x={:.1f}, y={:.1f}".format(virt_x, virt_y))
            print("Computed key area: row_index={}, col_index={}".format(row_index, col_index))
            print("Mapped key: {}".format(mapped_key))
            
            # Ask for user confirmation via the console
            user_feedback = input("Please type the key you actually pressed (or press Enter if correct): ").strip()
            if user_feedback:
                print("User reported: {}".format(user_feedback))
            else:
                print("User confirmed mapping is correct.")
            print("============================================\n")
            time.sleep(0.5)
        time.sleep(0.02)
