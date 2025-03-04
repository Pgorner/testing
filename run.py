#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys
import time
import logging
import st7789
import cst816d
from PIL import Image
import cv2
from yt_dlp import YoutubeDL

# List your YouTube video URLs here
VIDEO_LINKS = [
    'https://www.youtube.com/watch?v=rtRl9HZGZEE',
    'https://www.youtube.com/watch?v=mLerrgININk',
    # Add more URLs as needed
]

def get_video_stream_url(link):
    """
    Extracts the direct video stream URL from a YouTube link using yt-dlp.
    """
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'skip_download': True,
        'no_warnings': True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            stream_url = info.get('url')
            return stream_url
    except Exception as e:
        logging.error(f"Error extracting URL from {link}: {e}")
        return None

def play_youtube_video(link, disp):
    """
    Plays a YouTube video on the Waveshare display by:
      1. Extracting the stream URL.
      2. Opening the stream with OpenCV.
      3. Converting each frame to a PIL image.
      4. Rotating 90 degrees, resizing and displaying it on the Waveshare.
      5. Matching the playback speed to the video FPS.
    """
    stream_url = get_video_stream_url(link)
    if not stream_url:
        logging.error("Skipping video due to extraction error.")
        return

    logging.info(f"Playing video: {link}")
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        logging.error("Failed to open video stream.")
        return

    # Use display's resolution if available; adjust these defaults as needed.
    disp_width = getattr(disp, 'width', 240)
    disp_height = getattr(disp, 'height', 240)

    # Try to get FPS from the capture; if not available, default to 30.
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or fps is None:
        fps = 30
    frame_delay = 1.0 / fps
    logging.info(f"Video FPS: {fps:.2f}, frame delay: {frame_delay:.3f} seconds")

    while True:
        start_time = time.time()
        ret, frame = cap.read()
        if not ret:
            break  # End of video stream or read error
        # OpenCV reads frames as BGR; convert to RGB.
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Convert the NumPy array to a PIL Image.
        image = Image.fromarray(frame_rgb)
        # Rotate image 90° (clockwise). 'expand=True' ensures the dimensions adjust.
        image = image.rotate(90, expand=True)
        # Resize image to match your display resolution.
        image = image.resize((disp_width, disp_height))
        disp.show_image(image)
        # Adjust delay to match the video's framerate.
        elapsed = time.time() - start_time
        sleep_time = frame_delay - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

    cap.release()
    logging.info("Finished playing video.")

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Initialize the Waveshare display.
    disp = st7789.st7789()
    disp.clear()
    
    # (Optional) Initialize touch if needed.
    touch = cst816d.cst816d()
    
    # Loop through each YouTube video continuously.
    while True:
        for link in VIDEO_LINKS:
            play_youtube_video(link, disp)
            # Pause briefly between videos if desired.
            time.sleep(2)
