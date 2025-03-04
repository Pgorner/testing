#!/usr/bin/python
# -*- coding: UTF-8 -*-
from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------
# In your custom coordinate system:
#   - The screen is 240 (width) x 320 (height).
#   - Top left: (0,320), top right: (240,320)
#   - Bottom left: (0,0), bottom right: (240,0)
# We define a conversion to the native PIL coordinate system
# (which has (0,0) at the top left) via:
#       pil_y = HEIGHT - custom_y
# ------------------------------------------------------------------
WIDTH = 240
HEIGHT = 320

def custom_to_pil(x, y_custom):
    """Convert from custom coordinates to PIL coordinates."""
    return (x, HEIGHT - y_custom)

# ------------------------------------------------------------------
# Layout in custom coordinates:
#
# Input view: spans full width and 1/4 of height.
#   → occupies from y = 320 (top) down to y = 320 - (320/4) = 240.
#
# Numpad: occupies below the input view,
#   → from y = 240 down to y = 0.
#
# For the numpad we use 3 rows × 3 columns.
#   Each cell width = WIDTH/3 = 80.
#   Each cell height = (240)/3 = 80.
#
# Logical numpad layout:
#   Row 0 (top row): "1", "2", "3"
#   Row 1: "4", "5", "6"
#   Row 2 (bottom row): "clear", "0", "del"
# ------------------------------------------------------------------
INPUT_TOP = 320
INPUT_BOTTOM = 240   # Input view height = 80 (1/4 of 320)
NUMPAD_TOP = INPUT_BOTTOM  # 240
NUMPAD_BOTTOM = 0
NUM_ROWS = 3
NUM_COLS = 3
CELL_WIDTH = WIDTH / NUM_COLS    # 240/3 = 80
CELL_HEIGHT = (NUMPAD_TOP - NUMPAD_BOTTOM) / NUM_ROWS  # 240/3 = 80

# Define the key layout (rows in natural order from top to bottom)
KEY_LAYOUT = [
    ["1", "2", "3"],
    ["4", "5", "6"],
    ["clear", "0", "del"]
]

# Create a new image (we use the native PIL coordinate system: 240x320)
img = Image.new("RGB", (WIDTH, HEIGHT), "black")
draw = ImageDraw.Draw(img)
font = ImageFont.load_default()

# ------------------------------------------------------------------
# Draw the Input View region
#
# In custom coordinates, input view is the rectangle with:
#    Top-left: (0,320)
#    Bottom-right: (240,240)
# Convert these points to PIL coordinates.
# ------------------------------------------------------------------
input_top_left = custom_to_pil(0, INPUT_TOP)       # (0,320) → (0, 320-320=0)
input_bottom_right = custom_to_pil(WIDTH, INPUT_BOTTOM)  # (240,240) → (240,320-240=80)
draw.rectangle([input_top_left, input_bottom_right], fill="white")
draw.text(custom_to_pil(10, INPUT_TOP - 10), "Input:", font=font, fill="black")
# (Here, custom_to_pil(10,310) → (10,320-310=10))

# ------------------------------------------------------------------
# Draw the Numpad region
#
# The numpad occupies custom y from 240 down to 0.
# For row r (0 at top of numpad, 1, 2), the cell boundaries in custom coordinates are:
#    Top = NUMPAD_TOP - (r * CELL_HEIGHT)
#    Bottom = NUMPAD_TOP - ((r+1) * CELL_HEIGHT)
# For column c, the boundaries are:
#    Left = c * CELL_WIDTH, Right = (c+1) * CELL_WIDTH.
# ------------------------------------------------------------------
for r in range(NUM_ROWS):
    for c in range(NUM_COLS):
        cell_left = c * CELL_WIDTH
        cell_right = (c + 1) * CELL_WIDTH
        cell_top = NUMPAD_TOP - (r * CELL_HEIGHT)
        cell_bottom = NUMPAD_TOP - ((r + 1) * CELL_HEIGHT)
        # Convert cell rectangle to PIL coordinates:
        pil_top_left = custom_to_pil(cell_left, cell_top)
        pil_bottom_right = custom_to_pil(cell_right, cell_bottom)
        draw.rectangle([pil_top_left, pil_bottom_right], outline="white", fill="gray")
        
        # Draw the key label centered in the cell.
        key_label = KEY_LAYOUT[r][c]
        bbox = draw.textbbox((0, 0), key_label, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        # Compute the center of the cell in custom coordinates:
        center_x = (cell_left + cell_right) / 2
        center_y = (cell_top + cell_bottom) / 2
        # Convert center to PIL coordinates:
        pil_center = custom_to_pil(center_x, center_y)
        text_x = pil_center[0] - text_width / 2
        text_y = pil_center[1] - text_height / 2
        draw.text((text_x, text_y), key_label, font=font, fill="white")

# ------------------------------------------------------------------
# Show and save the resulting image
# ------------------------------------------------------------------
img.show()
img.save("custom_numpad.png")
