#!/usr/bin/python
# -*- coding: UTF-8 -*-
import time
import logging
import st7789
import cst816d
from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------
# Display and layout parameters
# ------------------------------------------------------
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240

# Final layout:
#  • Input region (final): top 40 px (y = 0 to 40)
#  • Keys region (final): bottom 200 px (y = 40 to 240)
INPUT_AREA_HEIGHT = 40
KEYS_AREA_HEIGHT = SCREEN_HEIGHT - INPUT_AREA_HEIGHT  # 200

# Keys region: 3 rows and 3 columns
NUM_KEY_ROWS = 3
NUM_KEY_COLS = 3
KEY_WIDTH = SCREEN_WIDTH / NUM_KEY_COLS            # ~106.67 px per key
KEY_HEIGHT = KEYS_AREA_HEIGHT / NUM_KEY_ROWS         # ~66.67 px per key

# Logical (final) numpad layout (rows listed in natural order)
# Final desired keys (from top of keys region to bottom):
#  Row 0: "1", "2", "3"
#  Row 1: "4", "5", "6"
#  Row 2: "clear", "0", "del"
KEY_LAYOUT = [
    ["1", "2", "3"],
    ["4", "5", "6"],
    ["clear", "0", "del"]
]

# Colors
BG_COLOR = (0, 0, 0)                # Black background
INPUT_BG_COLOR = (255, 255, 255)      # White for input region
INPUT_TEXT_COLOR = (0, 0, 0)          # Black text in input region
KEY_FILL_COLOR = (50, 50, 50)         # Dark gray for keys
KEY_OUTLINE_COLOR = (255, 255, 255)   # White outline for keys
KEY_TEXT_COLOR = (255, 255, 255)      # White key labels

# Use default PIL font (or load a TTF font if preferred)
font = ImageFont.load_default()

# ------------------------------------------------------
# Off-screen drawing for keys region (size: 320 x 200)
# ------------------------------------------------------
def create_keys_drawn_image():
    """
    Create the keys image in drawn coordinates (320 x 200).
    To obtain the final logical order after transformation (T_keys),
    we draw the keys with inverted vertical order:
      - In drawn keys image, row 0 (y: 0–KEY_HEIGHT) will become final row 2.
      - Drawn row 1 (y: KEY_HEIGHT–2*KEY_HEIGHT) becomes final row 1.
      - Drawn row 2 (y: 2*KEY_HEIGHT–KEYS_AREA_HEIGHT) becomes final row 0.
    """
    keys_img = Image.new("RGB", (SCREEN_WIDTH, int(KEYS_AREA_HEIGHT)), BG_COLOR)
    draw = ImageDraw.Draw(keys_img)
    for final_row in range(NUM_KEY_ROWS):
        # Compute drawn row: invert vertical order:
        drawn_row = (NUM_KEY_ROWS - 1) - final_row  # For final row 0, drawn_row=2; row 1 ->1; row 2 ->0.
        y_top = drawn_row * KEY_HEIGHT
        y_bottom = (drawn_row + 1) * KEY_HEIGHT
        for col in range(NUM_KEY_COLS):
            x_left = col * KEY_WIDTH
            x_right = (col + 1) * KEY_WIDTH
            label = KEY_LAYOUT[final_row][col]
            # Draw key rectangle
            draw.rectangle([x_left, y_top, x_right, y_bottom],
                           fill=KEY_FILL_COLOR, outline=KEY_OUTLINE_COLOR)
            # Center the label
            bbox = draw.textbbox((0, 0), label, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            text_x = x_left + (KEY_WIDTH - text_w) / 2
            text_y = y_top + (KEY_HEIGHT - text_h) / 2
            draw.text((text_x, text_y), label, font=font, fill=KEY_TEXT_COLOR)
    return keys_img

def transform_keys_image(keys_img):
    """
    Apply the preferred transformation to the keys image.
    For keys region (320x200), our transformation T_keys is:
         (x, y) -> (x, KEYS_AREA_HEIGHT - y)
    This is achieved by rotating 180° and then flipping horizontally.
    """
    transformed = keys_img.rotate(180, expand=False)
    transformed = transformed.transpose(Image.FLIP_LEFT_RIGHT)
    return transformed

# ------------------------------------------------------
# Create input region image (320 x 40) drawn normally.
# ------------------------------------------------------
def create_input_image(current_input):
    """
    Create an image for the input region (320 x 40) drawn in natural orientation.
    """
    input_img = Image.new("RGB", (SCREEN_WIDTH, INPUT_AREA_HEIGHT), INPUT_BG_COLOR)
    draw = ImageDraw.Draw(input_img)
    draw.text((10, 10), current_input, font=font, fill=INPUT_TEXT_COLOR)
    return input_img

# ------------------------------------------------------
# Composite final image from input region and keys region.
# ------------------------------------------------------
def compose_final_image(current_input):
    """
    Create the final composite image (320 x 240) by:
      - Generating the input image (unchanged).
      - Generating the keys image, transforming it, and pasting it below the input area.
    """
    final_img = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), BG_COLOR)
    # Create input image (final region: top 40 px)
    input_img = create_input_image(current_input)
    final_img.paste(input_img, (0, 0))
    
    # Create keys image in drawn coordinates, transform it, then paste into final image starting at y=INPUT_AREA_HEIGHT.
    keys_drawn = create_keys_drawn_image()
    keys_final = transform_keys_image(keys_drawn)
    final_img.paste(keys_final, (0, INPUT_AREA_HEIGHT))
    return final_img

# ------------------------------------------------------
# Touch mapping for keys region
# ------------------------------------------------------
def map_touch_to_key(final_touch_x, final_touch_y):
    """
    Given a touch at (final_touch_x, final_touch_y) in the final composite image,
    determine the pressed key (if any) in the keys region.
    
    The keys region in the final image occupies y from INPUT_AREA_HEIGHT to SCREEN_HEIGHT.
    For a touch in that region, we first compute the relative coordinates:
         rel_x = final_touch_x
         rel_y = final_touch_y - INPUT_AREA_HEIGHT
    Our keys transformation T_keys was: (x, y) -> (x, KEYS_AREA_HEIGHT - y)
    To invert that for the touch mapping, we do:
         drawn_y = KEYS_AREA_HEIGHT - rel_y
         drawn_x = rel_x
    Then compute:
         drawn_row = int(drawn_y / KEY_HEIGHT)
         final_row = (NUM_KEY_ROWS - 1) - drawn_row
         col_index = int(drawn_x / KEY_WIDTH)
    """
    # Ensure the touch is in the keys region.
    if final_touch_y < INPUT_AREA_HEIGHT or final_touch_y >= SCREEN_HEIGHT:
        return None  # Outside keys area
    rel_x = final_touch_x
    rel_y = final_touch_y - INPUT_AREA_HEIGHT
    # Invert vertical coordinate (T_keys inverse is same as T_keys)
    drawn_y = KEYS_AREA_HEIGHT - rel_y
    drawn_x = rel_x
    # Clamp drawn_y
    if drawn_y < 0:
        drawn_y = 0
    elif drawn_y >= KEYS_AREA_HEIGHT:
        drawn_y = KEYS_AREA_HEIGHT - 1
    drawn_row = int(drawn_y // KEY_HEIGHT)
    # Final row is inverted: final_row = (NUM_KEY_ROWS - 1) - drawn_row
    final_row = (NUM_KEY_ROWS - 1) - drawn_row
    col_index = int(drawn_x // KEY_WIDTH)
    if col_index < 0:
        col_index = 0
    elif col_index >= NUM_KEY_COLS:
        col_index = NUM_KEY_COLS - 1
    return KEY_LAYOUT[final_row][col_index]

# ------------------------------------------------------
# Main Program: Numpad Input Interface with Touch
# ------------------------------------------------------
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    disp = st7789.st7789()    # Initialize the display
    disp.clear()
    touch = cst816d.cst816d()  # Initialize the touch sensor

    current_input = ""
    logging.info("Starting numpad input interface (preferred orientation).")
    
    while True:
        # Compose the final composite image from the untransformed input and transformed keys.
        final_img = compose_final_image(current_input)
        disp.show_image(final_img)
        
        # Read touch data from sensor.
        touch.read_touch_data()
        point, coordinates = touch.get_touch_xy()
        if point != 0 and coordinates:
            # Get raw final coordinates from touch sensor.
            tx = coordinates[0]['x']
            ty = coordinates[0]['y']
            # For debugging:
            logging.debug("Raw touch: x=%s, y=%s", tx, ty)
            
            # Process only touches in the keys region.
            key = map_touch_to_key(tx, ty)
            if key is not None:
                logging.debug("Mapped key: %s", key)
                # Process key actions.
                if key.lower() == "clear":
                    current_input = ""
                elif key.lower() in ["del", "delete"]:
                    current_input = current_input[:-1]
                else:
                    current_input += key
                time.sleep(0.3)  # Debounce delay.
        time.sleep(0.02)
