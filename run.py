#!/usr/bin/env python3
import time
from PIL import Image, ImageDraw, ImageFont

# Import your display and touch libraries.
# (Make sure these libraries are installed and that the constructors below match your wiring.)
import ST7789T3
import CST816D

# -------------------------
# Configuration parameters
# -------------------------
# Display dimensions (landscape mode; adjust if needed)
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240
INPUT_LINE_HEIGHT = 40  # Height reserved at top for input text

# Define numpad grid (4 rows x 3 columns)
NUM_ROWS = 4
NUM_COLS = 3
KEY_WIDTH = SCREEN_WIDTH // NUM_COLS
KEY_HEIGHT = (SCREEN_HEIGHT - INPUT_LINE_HEIGHT) // NUM_ROWS

# Numpad layout: change labels or add/remove buttons as desired.
# In this example, the last row has "0", "Del" (delete last character), and "Enter" (submits/clears).
KEY_LAYOUT = [
    ["7", "8", "9"],
    ["4", "5", "6"],
    ["1", "2", "3"],
    ["0", "Del", "Enter"]
]

# Colors (RGB tuples) for drawing; adjust as needed.
BG_COLOR = (0, 0, 0)
INPUT_BG_COLOR = (255, 255, 255)
INPUT_TEXT_COLOR = (0, 0, 0)
KEY_FILL_COLOR = (50, 50, 50)
KEY_OUTLINE_COLOR = (255, 255, 255)
KEY_TEXT_COLOR = (255, 255, 255)

# -------------------------
# Initialize display & touch
# -------------------------
# Initialize the Waveshare display using ST7789T3.
# (Update the parameters such as port, cs, dc, backlight, rotation, etc., per your wiring.)
disp = ST7789T3.ST7789T3(
    port=0, cs=0, dc=24, backlight=18,
    width=SCREEN_WIDTH, height=SCREEN_HEIGHT,
    rotation=90  # landscape mode; adjust rotation as needed
)
disp.begin()

# Initialize the touch controller (CST816D).
touch = CST816D.CST816D()
touch.begin()

# Create an image buffer to draw the interface.
image = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()  # You can load a TTF font if desired

# -------------------------
# Create key definitions
# -------------------------
# Each key is defined by its label and rectangle (x, y, width, height)
keys = []
for row in range(NUM_ROWS):
    for col in range(NUM_COLS):
        label = KEY_LAYOUT[row][col]
        key = {
            "label": label,
            "x": col * KEY_WIDTH,
            "y": INPUT_LINE_HEIGHT + row * KEY_HEIGHT,
            "w": KEY_WIDTH,
            "h": KEY_HEIGHT,
        }
        keys.append(key)

# -------------------------
# Function to draw the interface
# -------------------------
def draw_interface(input_str):
    # Clear entire screen
    draw.rectangle((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), fill=BG_COLOR)
    
    # Draw the input line background and text at the top.
    draw.rectangle((0, 0, SCREEN_WIDTH, INPUT_LINE_HEIGHT), fill=INPUT_BG_COLOR)
    draw.text((10, 10), input_str, font=font, fill=INPUT_TEXT_COLOR)
    
    # Draw each numpad key
    for key in keys:
        # Draw the key rectangle (filled with a dark color and white outline)
        draw.rectangle(
            (key["x"], key["y"], key["x"] + key["w"], key["y"] + key["h"]),
            fill=KEY_FILL_COLOR, outline=KEY_OUTLINE_COLOR
        )
        # Center the key label within the key rectangle.
        text_size = draw.textsize(key["label"], font=font)
        text_x = key["x"] + (key["w"] - text_size[0]) / 2
        text_y = key["y"] + (key["h"] - text_size[1]) / 2
        draw.text((text_x, text_y), key["label"], font=font, fill=KEY_TEXT_COLOR)
    
    # Update the display with the new image.
    disp.display(image)

# -------------------------
# Main loop
# -------------------------
current_input = ""

print("Starting numpad interface. Touch keys on the display...")

while True:
    # Redraw the interface with the current input string.
    draw_interface(current_input)
    
    # Small delay to let the display update and to reduce CPU usage.
    time.sleep(0.1)
    
    # Read a touch point.
    # (This example assumes a method `get_touch()` that returns a tuple (x, y)
    #  when a touch is detected, or None if no touch. Adjust based on your library.)
    touch_point = touch.get_touch()
    if touch_point:
        tx, ty = touch_point
        # Determine if the touch falls within one of the keys.
        for key in keys:
            if key["x"] <= tx <= key["x"] + key["w"] and key["y"] <= ty <= key["y"] + key["h"]:
                label = key["label"]
                if label == "Del":
                    # Remove the last character
                    current_input = current_input[:-1]
                elif label == "Enter":
                    # For this example, print the input and then clear it.
                    print("Entered:", current_input)
                    current_input = ""
                else:
                    # Append the pressed key (digit) to the current input.
                    current_input += label
                # Add a brief pause to debounce the touch input.
                time.sleep(0.3)
                break
