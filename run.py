#!/usr/bin/python
# -*- coding: UTF-8 -*-
import cv2
import time
from PIL import Image
import st7789  # your Waveshare display library
import cst816d  # your touch library (if you want to handle touch events)

# Initialize display and touch (if needed)
disp = st7789.st7789()
disp.clear()
touch = cst816d.cst816d()

# Open the video file
video_path = "./video/sample_video.mp4"
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

# Get video frame rate for proper timing
fps = cap.get(cv2.CAP_PROP_FPS)
delay = 1.0 / fps

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break  # end of video

    # Convert frame from BGR (OpenCV default) to RGB (PIL default)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Convert NumPy array to PIL Image
    image = Image.fromarray(frame_rgb)
    
    # Resize image if necessary to fit the display dimensions
    # For example, if your display is 240x240:
    # image = image.resize((240, 240))
    
    # Display the image frame
    disp.show_image(image)

    # Optionally, handle touch events concurrently:
    touch.read_touch_data()
    point, coordinates = touch.get_touch_xy()
    if point != 0 and coordinates:
        # Example: draw a small rectangle at the touch point
        disp.draw_rectangle(
            coordinates[0]['x'], coordinates[0]['y'],
            coordinates[0]['x'] + 5, coordinates[0]['y'] + 5,
            0x00ff  # rectangle color
        )
        print(f"Touch at: x={coordinates[0]['x']}, y={coordinates[0]['y']}")
    
    # Wait for the next frame
    time.sleep(delay)

cap.release()
disp.clear()
