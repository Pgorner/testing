#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys
import time
import logging
import subprocess
import cv2
from PIL import Image
import st7789
import cst816d

# Directory containing pre-converted videos
VIDEO_DIR = "15fpsd"

# Set this flag True if you want the display in landscape mode.
LANDSCAPE_MODE = True

# Native display dimensions (portrait)
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 320

# In landscape mode, the effective resolution is swapped: 320x240.
# Adjust this rotation angle as needed: try 0, 90, 180, or 270.
ROTATION_DEGREE = 0

def get_video_list(directory):
    """
    Returns a sorted list of full paths to MP4 videos in the specified directory.
    """
    videos = []
    for filename in sorted(os.listdir(directory)):
        if filename.lower().endswith(".mp4"):
            videos.append(os.path.join(directory, filename))
    return videos

def play_video(video_path, disp):
    """
    Play the given video file on the Waveshare display with synchronized audio.
    This function:
      - Launches FFplay in a subprocess to play the audio (with no video display).
      - Reads video frames with OpenCV and synchronizes frame display to 20 FPS.
      - Adjusts (rotates and flips) the frame for landscape mode.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logging.error(f"Failed to open video file: {video_path}")
        return

    # We are forcing playback at 20 FPS.
    fps = 20.0
    logging.info(f"Playing video: {video_path} at {fps} FPS")
    
    # Determine display dimensions
    if LANDSCAPE_MODE:
        screen_width = DISPLAY_HEIGHT  # 240
        screen_height = DISPLAY_WIDTH  # 320
    else:
        screen_width = DISPLAY_WIDTH
        screen_height = DISPLAY_HEIGHT

    # Start audio playback using ffplay (audio only)
    # '-nodisp' disables video display, '-vn' disables video decoding.
    audio_proc = subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-vn", video_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Use a timing loop to display frames at exactly 20 FPS.
    start_time = time.time()
    frame_number = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        # Calculate when this frame should be displayed
        expected_time = frame_number * (1.0 / fps)
        current_time = time.time() - start_time
        if expected_time > current_time:
            time.sleep(expected_time - current_time)

        # Convert frame from BGR (OpenCV) to RGB (PIL)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)

        # If in landscape mode, rotate and flip the image as needed.
        if LANDSCAPE_MODE:
            image = image.rotate(ROTATION_DEGREE, expand=True)
            image = image.transpose(Image.FLIP_LEFT_RIGHT)

        # Resize the image to fit the display.
        image = image.resize((screen_width, screen_height))
        disp.show_image(image)
        frame_number += 1

    cap.release()
    audio_proc.wait()  # Wait for audio playback to finish

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize Waveshare display and touch controller
    disp = st7789.st7789()
    disp.clear()
    touch = cst816d.cst816d()

    # Get the list of video files from the "vids" folder
    video_files = get_video_list(VIDEO_DIR)
    if not video_files:
        logging.error("No video files found in folder 'vids'")
        sys.exit(1)

    logging.info("Found videos: " + ", ".join(video_files))

    # Main loop: play each video in sequence and then loop back.
    while True:
        for video_file in video_files:
            play_video(video_file, disp)

        # Clear the display between loops
        disp.clear()
        time.sleep(1)

    # Optional: Touch input loop (if needed)
    while True:
        touch.read_touch_data()
        point, coordinates = touch.get_touch_xy()
        if point != 0 and coordinates:
            disp.dre_rectangle(
                coordinates[0]['x'], coordinates[0]['y'],
                coordinates[0]['x'] + 5, coordinates[0]['y'] + 5,
                0x00ff  # rectangle color
            )
            print(f"Touch coordinates: x={coordinates[0]['x']}, y={coordinates[0]['y']}")
        time.sleep(0.02)
