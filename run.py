#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys
import time
import logging
import cv2
import yt_dlp
from PIL import Image
import st7789
import cst816d

# List of YouTube video URLs to loop
VIDEO_URLS = [
    "https://www.youtube.com/watch?v=rtRl9HZGZEE",
    "https://www.youtube.com/watch?v=4oi-TgKBvd4"
]

# Set this flag True if you want the display in landscape mode.
LANDSCAPE_MODE = True

# Native display dimensions (portrait)
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 320

# In landscape mode, the effective resolution is swapped: 320x240.
# Adjust this rotation angle as needed: try 0, 90, 180, or 270.
ROTATION_DEGREE = 0

def download_video(url, output_path):
    """
    Download a YouTube video using yt_dlp and re-encode it to 20 FPS.
    If the file already exists, skip downloading.
    """
    if os.path.exists(output_path):
        logging.info(f"{output_path} already exists. Skipping download.")
        return output_path

    ydl_opts = {
        'format': 'mp4[height<=480]',  # limit resolution for faster processing
        'outtmpl': output_path,
        'quiet': True,
        'http_headers': {
            'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/108.0.0.0 Safari/537.36')
        },
        # Add a postprocessor to re-encode the video to 20 FPS
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4'
        }],
        'postprocessor_args': ['-r', '20'],  # Force 20 FPS
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        logging.info(f"Downloading {url} to {output_path} with 20 FPS conversion")
        try:
            ydl.download([url])
        except Exception as e:
            logging.error(f"Error downloading {url}: {e}")
    return output_path

def play_video(video_path, disp):
    """
    Play the given video file on the Waveshare display.
    Uses OpenCV to decode frames, converts them to PIL images, rotates if needed,
    resizes, and then displays them using disp.show_image.
    
    To cope with the display's 20 FPS limit, if the video is encoded at a higher
    framerate, we skip frames so that only an effective 20 frames per second are shown.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logging.error(f"Failed to open video file: {video_path}")
        return

    # Check the video's original FPS (expected to be close to 20 if re-encoded, 
    # but if it's higher, we'll drop some frames)
    orig_fps = cap.get(cv2.CAP_PROP_FPS)
    logging.info(f"Playing video at {orig_fps} FPS")
    
    # For landscape mode, swap dimensions (effective resolution: 320x240)
    if LANDSCAPE_MODE:
        screen_width = DISPLAY_HEIGHT  # 240
        screen_height = DISPLAY_WIDTH  # 320
    else:
        screen_width = DISPLAY_WIDTH
        screen_height = DISPLAY_HEIGHT

    # Calculate frame interval ratio:
    # If the video has a higher frame rate than 20, we only display every (orig_fps/20)th frame.
    frame_interval = orig_fps / 20.0 if orig_fps > 20 else 1.0
    frame_counter = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        # Increase the frame counter; only display a frame when we cross the interval.
        frame_counter += 1.0
        if frame_counter < frame_interval:
            continue
        # Reset counter by subtracting the interval (in case of non-integer ratio)
        frame_counter -= frame_interval

        # Convert frame from BGR (OpenCV) to RGB (PIL)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)

        # Rotate the image if in landscape mode. Adjust ROTATION_DEGREE as needed.
        if LANDSCAPE_MODE:
            image = image.rotate(ROTATION_DEGREE, expand=True)
            # Correct mirror effect if needed
            image = image.transpose(Image.FLIP_LEFT_RIGHT)

        # Resize the image to fit the display
        image = image.resize((screen_width, screen_height))
        disp.show_image(image)

    cap.release()


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize Waveshare display and touch controller
    disp = st7789.st7789()
    disp.clear()
    touch = cst816d.cst816d()

    # Prepare local filenames for downloaded videos
    downloaded_videos = []
    for index, url in enumerate(VIDEO_URLS):
        video_filename = f"video_{index+1}.mp4"
        download_video(url, video_filename)
        downloaded_videos.append(video_filename)

    # Main loop: play each video in sequence and then loop back
    while True:
        for video_file in downloaded_videos:
            logging.info(f"Playing video: {video_file}")
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
