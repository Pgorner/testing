#!/usr/bin/python
# -*- coding: UTF-8 -*-
import time
import logging
import st7789
import cst816d
from PIL import Image, ImageDraw, ImageFont

# -------------------------
# Display and layout parameters
# -------------------------
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240

# Final layout:
#   Final Input view area: y = 0 to 40 (input text at the top)
#   Final keys area: y = 40 to 240 (height 200), divided into 3 rows.
#   Final key rows:
#       Row 0 (top keys): "1", "2", "3"
#       Row 1: "4", "5", "6"
#       Row 2 (bottom keys): "clear", "0", "del"
#
# Because our transformation T rotates 180° and then flips horizontally,
# a drawn point (x, y) maps to final (x, SCREEN_HEIGHT - y).
# Thus, to have the final layout as above, we draw in the off-screen (drawn) image:
#   - The keys area in drawn coordinates is y = 0 to 200.
#   - The input view in drawn coordinates is y = 200 to 240.
#
# And we invert the vertical order of keys:
#   Final row 0 is drawn in drawn row 2,
#   Final row 1 is drawn in drawn row 1,
#   Final row 2 is drawn in drawn row 0.

INPUT_AREA_HEIGHT = 40         # Final input view height (and drawn input area: y 200 to 240)
KEYS_AREA_HEIGHT = SCREEN_HEIGHT - INPUT_AREA_HEIGHT  # = 240 - 40 = 200

NUM_KEY_ROWS = 3
NUM_KEY_COLS = 3
KEY_WIDTH = SCREEN_WIDTH / NUM_KEY_COLS            # ≈ 106.67 px each
KEY_HEIGHT = KEYS_AREA_HEIGHT / NUM_KEY_ROWS         # 200/3 ≈ 66.67 px each

# Logical (final) numpad layout (rows in natural order)
KEY_LAYOUT = [
    ["1", "2", "3"],         # Final row 0 (should appear at top of keys)
    ["4", "5", "6"],         # Final row 1
    ["clear", "0", "del"]      # Final row 2 (appears at bottom)
]

# Colors
BG_COLOR = (0, 0, 0)              # Black background
INPUT_BG_COLOR = (255, 255, 255)  # White input view area
INPUT_TEXT_COLOR = (0, 0, 0)      # Black text for input view
KEY_FILL_COLOR = (50, 50, 50)     # Dark gray keys
KEY_OUTLINE_COLOR = (255, 255, 255)  # White key outlines
KEY_TEXT_COLOR = (255, 255, 255)  # White key labels

# Use default PIL font (or load a TTF if desired)
font = ImageFont.load_default()

# -------------------------
# Off-screen drawing functions
# -------------------------
def create_drawn_interface(current_input):
    """
    Create the off-screen (drawn) interface.
    Drawn coordinate system (320x240):
      - Keys area: y in [0, KEYS_AREA_HEIGHT] = [0, 200]
      - Input view: y in [200, 240]
    To get the final keys in natural order after transformation, we draw the keys
    in reverse vertical order:
        For a given final row index (0=top, 1, 2=bottom), use:
           drawn_row = 2 - final_row.
    """
    image = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(image)
    
    # Draw the keys area:
    # Loop over final rows 0 to 2.
    for final_row in range(NUM_KEY_ROWS):
        drawn_row = (NUM_KEY_ROWS - 1) - final_row  # 2 - final_row
        y_top = drawn_row * KEY_HEIGHT
        y_bottom = (drawn_row + 1) * KEY_HEIGHT
        for col in range(NUM_KEY_COLS):
            x_left = col * KEY_WIDTH
            x_right = (col + 1) * KEY_WIDTH
            label = KEY_LAYOUT[final_row][col]
            # Draw the key rectangle
            draw.rectangle([x_left, y_top, x_right, y_bottom],
                           fill=KEY_FILL_COLOR, outline=KEY_OUTLINE_COLOR)
            # Center the label in the rectangle
            bbox = draw.textbbox((0, 0), label, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            text_x = x_left + (KEY_WIDTH - text_w) / 2
            text_y = y_top + (KEY_HEIGHT - text_h) / 2
            draw.text((text_x, text_y), label, font=font, fill=KEY_TEXT_COLOR)
    
    # Draw the input view area in drawn coordinates:
    # Drawn input view occupies y from KEYS_AREA_HEIGHT to SCREEN_HEIGHT ([200,240]).
    draw.rectangle([0, KEYS_AREA_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT], fill=INPUT_BG_COLOR)
    draw.text((10, KEYS_AREA_HEIGHT + 10), current_input, font=font, fill=INPUT_TEXT_COLOR)
    
    return image

def apply_preferred_transformation(image):
    """
    Apply the preferred transformation to the drawn image.
    The transformation is:
       1. Rotate 180°,
       2. Then flip horizontally.
    Overall, a drawn point (x, y) maps to final (x, SCREEN_HEIGHT - y).
    """
    transformed = image.rotate(180, expand=False)
    transformed = transformed.transpose(Image.FLIP_LEFT_RIGHT)
    return transformed

# -------------------------
# Touch coordinate mapping
# -------------------------
def map_touch_to_drawn(tx, ty):
    """
    Map raw touch coordinates (tx, ty) from the final display back to drawn coordinates.
    Given our transformation, we have:
         drawn_x = tx
         drawn_y = SCREEN_HEIGHT - ty
    """
    return tx, SCREEN_HEIGHT - ty

# -------------------------
# Main Program: Numpad with Touch Input
# -------------------------
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    disp = st7789.st7789()    # Initialize display
    disp.clear()
    touch = cst816d.cst816d()  # Initialize touch sensor

    current_input = ""
    logging.info("Starting numpad input interface (preferred orientation: 180° + horizontal flip).")
    
    while True:
        # Create the off-screen (drawn) interface image with current input text.
        drawn_img = create_drawn_interface(current_input)
        # Transform the drawn image to get the final display image.
        final_img = apply_preferred_transformation(drawn_img)
        # Show the final image on the display.
        disp.show_image(final_img)
        
        # Read touch data
        touch.read_touch_data()
        point, coordinates = touch.get_touch_xy()
        if point != 0 and coordinates:
            raw_x = coordinates[0]['x']
            raw_y = coordinates[0]['y']
            # Map touch coordinates from final display to drawn coordinates.
            d_x, d_y = map_touch_to_drawn(raw_x, raw_y)
            
            # Only process touches in the keys area (drawn y in [0, KEYS_AREA_HEIGHT])
            if 0 <= d_y < KEYS_AREA_HEIGHT:
                # Compute the drawn row index (in the keys area)
                # Each drawn row height = KEY_HEIGHT = KEYS_AREA_HEIGHT / 3.
                drawn_row = int(d_y // KEY_HEIGHT)
                # Final row is inverted: final_row = 2 - drawn_row
                final_row = (NUM_KEY_ROWS - 1) - drawn_row
                # Compute column index
                col_index = int(d_x // KEY_WIDTH)
                if col_index < 0:
                    col_index = 0
                elif col_index >= NUM_KEY_COLS:
                    col_index = NUM_KEY_COLS - 1
                # Get the key label from the final layout.
                pressed_key = KEY_LAYOUT[final_row][col_index]
                logging.debug("Raw touch: x=%s, y=%s | Mapped drawn: x=%.1f, y=%.1f | drawn_row=%d, final_row=%d, col=%d | Key: %s",
                              raw_x, raw_y, d_x, d_y, drawn_row, final_row, col_index, pressed_key)
                
                # Process key actions:
                if pressed_key.lower() == "clear":
                    current_input = ""
                elif pressed_key.lower() in ["del", "delete"]:
                    current_input = current_input[:-1]
                else:
                    current_input += pressed_key
                time.sleep(0.3)  # debounce delay
        time.sleep(0.02)
