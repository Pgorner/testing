#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import cv2
import time
from PIL import Image
import st7789  # Waveshare display library
import cst816d  # Touch library

# Initialize display and touch
disp = st7789.st7789()
disp.clear()
touch = cst816d.cst816d()

# Directory containing video files
video_dir = "/home/patrick/processed"

# Get list of video files; adjust extensions as needed
video_files = [os.path.join(video_dir, f) for f in os.listdir(video_dir)
               if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
video_files.sort()  # Optional: sort list

# Loop through each video file
for video_path in video_files:
    print(f"Playing video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        continue

    # Retrieve video frame rate for correct timing
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 24  # Fallback to a default value if FPS info is unavailable
    delay = 1.0 / fps

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        # Convert frame from BGR (OpenCV default) to RGB (PIL default)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Convert NumPy array to PIL Image
        image = Image.fromarray(frame_rgb)

        # Resize the image if needed to match your display's resolution
        # For example, if your display is 240x240 pixels:
        # image = image.resize((240, 240))
        
        # Display the image on the Waveshare display
        disp.show_image(image)

        # Optionally handle touch input
        touch.read_touch_data()
        point, coordinates = touch.get_touch_xy()
        if point != 0 and coordinates:
            # Example: Draw a small rectangle at the touch point
            disp.draw_rectangle(
                coordinates[0]['x'], coordinates[0]['y'],
                coordinates[0]['x'] + 5, coordinates[0]['y'] + 5,
                0x00ff  # Rectangle color
            )
            print(f"Touch at: x={coordinates[0]['x']}, y={coordinates[0]['y']}")

        # Wait for the appropriate time before showing the next frame
        time.sleep(delay)
    
    cap.release()
    # Optional: clear the display between videos
    disp.clear()

print("All videos played.")
