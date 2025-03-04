#!/usr/bin/python
# -*- coding: UTF-8 -*-
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
# In the final display, we want the top 40 pixels for input text.
# In our drawn image (before transformation) we reserve the bottom 40 pixels.
INPUT_AREA_HEIGHT = 40  
KEYS_AREA_HEIGHT = SCREEN_HEIGHT - INPUT_AREA_HEIGHT  # 240 - 40 = 200

NUM_ROWS = 4
NUM_COLS = 3
KEY_WIDTH = SCREEN_WIDTH / NUM_COLS       # ≈106.67 px per key horizontally
KEY_HEIGHT = KEYS_AREA_HEIGHT / NUM_ROWS    # 200/4 = 50 px per key vertically

# Logical numpad layout (final order, top row = "7 8 9", then "4 5 6", etc.)
KEY_LAYOUT = [
    ["7", "8", "9"],     # Final row 0 (should appear at top of keys in final display)
    ["4", "5", "6"],     # Final row 1
    ["1", "2", "3"],     # Final row 2
    ["0", "Del", "Enter"]  # Final row 3 (appears at bottom)
]

# Colors (RGB)
BG_COLOR = (0, 0, 0)              # Black background
INPUT_BG_COLOR = (255, 255, 255)    # White input area
INPUT_TEXT_COLOR = (0, 0, 0)        # Black text in input area
KEY_FILL_COLOR = (50, 50, 50)       # Dark gray for keys
KEY_OUTLINE_COLOR = (255, 255, 255) # White outline for keys
KEY_TEXT_COLOR = (255, 255, 255)    # White key labels

# Use default PIL font (or load a TTF font if desired)
font = ImageFont.load_default()

# -------------------------
# Create the drawn (off‑screen) interface image
# -------------------------
def create_drawn_interface(current_input):
    """
    In the drawn coordinate system (320x240):
      - The keys area occupies y from 0 to KEYS_AREA_HEIGHT (0 to 200).
      - To get final keys in natural order after transformation, we draw them in reversed order:
            Drawn row 3 (y: 150 to 200) will be final row 0 ("7 8 9")
            Drawn row 2 (y: 100 to 150) will be final row 1 ("4 5 6")
            Drawn row 1 (y: 50  to 100) will be final row 2 ("1 2 3")
            Drawn row 0 (y: 0   to 50) will be final row 3 ("0 Del Enter")
      - The input text is drawn in the drawn area from y=KEYS_AREA_HEIGHT to SCREEN_HEIGHT (200 to 240).
    """
    image = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(image)
    
    # Draw keys:
    # Loop over final rows (0 to 3) in natural order.
    # For each final row, compute the corresponding drawn row index:
    # drawn_row = 3 - final_row.
    for final_row in range(NUM_ROWS):
        drawn_row = 3 - final_row  # reverse order for drawing
        y_top = drawn_row * KEY_HEIGHT
        y_bottom = (drawn_row + 1) * KEY_HEIGHT
        for col in range(NUM_COLS):
            x_left = col * KEY_WIDTH
            x_right = (col + 1) * KEY_WIDTH
            label = KEY_LAYOUT[final_row][col]
            # Draw the key rectangle
            draw.rectangle([x_left, y_top, x_right, y_bottom],
                           fill=KEY_FILL_COLOR, outline=KEY_OUTLINE_COLOR)
            # Center the label within the rectangle
            bbox = draw.textbbox((0, 0), label, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            text_x = x_left + (KEY_WIDTH - text_w) / 2
            text_y = y_top + (KEY_HEIGHT - text_h) / 2
            draw.text((text_x, text_y), label, font=font, fill=KEY_TEXT_COLOR)
    
    # Draw the input text area in the drawn image.
    # The input area occupies y from KEYS_AREA_HEIGHT to SCREEN_HEIGHT (200 to 240).
    draw.rectangle([0, KEYS_AREA_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT], fill=INPUT_BG_COLOR)
    draw.text((10, KEYS_AREA_HEIGHT + 10), current_input, font=font, fill=INPUT_TEXT_COLOR)
    
    return image

# -------------------------
# Preferred Transformation: 180° rotation + horizontal flip
# -------------------------
def apply_preferred_transformation(image):
    """
    Transform the drawn image to the final display orientation.
    The transformation applied is:
      1. Rotate 180°.
      2. Flip horizontally.
    Overall, a point (x, y) in the drawn image is mapped to (x, SCREEN_HEIGHT - y)
    in the final display.
    """
    transformed = image.rotate(180, expand=False)
    transformed = transformed.transpose(Image.FLIP_LEFT_RIGHT)
    return transformed

# -------------------------
# Map raw touch coordinates (from final display) to drawn coordinates
# -------------------------
def map_touch_to_drawn(tx, ty):
    """
    Given raw touch coordinates (tx, ty) in the final display coordinate system,
    compute the corresponding drawn coordinate.
    Our transformation T maps drawn (x, y) -> final (x, SCREEN_HEIGHT - y).
    Since T is its own inverse, we have:
         drawn_x = tx
         drawn_y = SCREEN_HEIGHT - ty
    """
    return tx, SCREEN_HEIGHT - ty

# -------------------------
# Main Program: Numpad Interface with Touch Input
# -------------------------
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    disp = st7789.st7789()    # Initialize the display
    disp.clear()
    touch = cst816d.cst816d()  # Initialize the touch sensor

    current_input = ""
    logging.info("Starting numpad input interface with preferred orientation.")
    
    while True:
        # Create the drawn interface with the current input.
        drawn_img = create_drawn_interface(current_input)
        # Apply the preferred transformation (180° rotation + horizontal flip)
        final_img = apply_preferred_transformation(drawn_img)
        # Show the final image on the display.
        disp.show_image(final_img)
        
        # Read touch data from the sensor.
        touch.read_touch_data()
        point, coordinates = touch.get_touch_xy()
        if point != 0 and coordinates:
            raw_x = coordinates[0]['x']
            raw_y = coordinates[0]['y']
            # Map the raw touch coordinates to the drawn coordinate system.
            d_x, d_y = map_touch_to_drawn(raw_x, raw_y)
            
            # Process only touches in the keys area (drawn y < KEYS_AREA_HEIGHT).
            if d_y < KEYS_AREA_HEIGHT:
                # Compute column index from drawn x.
                col_index = int(d_x // KEY_WIDTH)
                if col_index < 0:
                    col_index = 0
                elif col_index >= NUM_COLS:
                    col_index = NUM_COLS - 1
                
                # Compute drawn row in the keys area.
                # In the drawn image, keys were drawn in reversed order.
                # Determine drawn row dr = int(d_y // KEY_HEIGHT), then final row = 3 - dr.
                dr = int(d_y // KEY_HEIGHT)
                final_row = 3 - dr
                if final_row < 0:
                    final_row = 0
                elif final_row >= NUM_ROWS:
                    final_row = NUM_ROWS - 1
                
                pressed_key = KEY_LAYOUT[final_row][col_index]
                logging.debug("Raw touch: x=%s, y=%s | Mapped drawn: x=%.1f, y=%.1f | Row: %d, Col: %d | Key: %s",
                              raw_x, raw_y, d_x, d_y, final_row, col_index, pressed_key)
                
                # Process the key:
                if pressed_key == "Del":
                    current_input = current_input[:-1]
                elif pressed_key == "Enter":
                    print("Entered:", current_input)
                    current_input = ""
                else:
                    current_input += pressed_key
                # Debounce delay
                time.sleep(0.3)
        time.sleep(0.02)
