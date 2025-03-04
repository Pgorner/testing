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
import subprocess

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
      2. Launching an audio process using mpv (with --no-video) so sound plays via aux.
      3. Opening the video stream with OpenCV.
      4. Converting each frame to a PIL image, rotating 90°, resizing it, and displaying it.
      5. Timing each frame to try to match the video FPS.
    """
    stream_url = get_video_stream_url(link)
    if not stream_url:
        logging.error("Skipping video due to extraction error.")
        return

    logging.info(f"Playing video: {link}")
    
    # Start the audio process using mpv in no-video mode.
    # Ensure mpv is installed and that your Pi is configured to output audio via aux.
    audio_proc = subprocess.Popen(["mpv", "--no-video", "--really-quiet", stream_url])
    
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        logging.error("Failed to open video stream.")
        audio_proc.terminate()
        return

    # Use display's resolution; adjust these defaults as needed.
    disp_width = getattr(disp, 'width', 240)
    disp_height = getattr(disp, 'height', 240)

    # Try to get FPS from the video stream; default to 30 if unavailable.
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps == 0:
        fps = 30
    frame_delay = 0
    logging.info(f"Video FPS: {fps:.2f}, target frame delay: {frame_delay:.3f} sec")

    while True:
        start_time = time.time()
        ret, frame = cap.read()
        if not ret:
            break  # End of video stream or read error

        # Convert from BGR (OpenCV) to RGB.
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Convert to a PIL Image.
        image = Image.fromarray(frame_rgb)
        # Rotate 90° clockwise (expand adjusts dimensions accordingly).
        image = image.rotate(90, expand=True)
        # Resize image to match the display resolution.
        image = image.resize((disp_width, disp_height))
        disp.show_image(image)

        # Calculate processing time and sleep to maintain the desired frame rate.
        elapsed = time.time() - start_time
        sleep_time = frame_delay - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

    cap.release()
    audio_proc.terminate()
    logging.info("Finished playing video.")

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Initialize the Waveshare display.
    disp = st7789.st7789()
    disp.clear()
    
    # (Optional) Initialize touch if needed.
    touch = cst816d.cst816d()
    
    # Loop continuously through the list of YouTube videos.
    while True:
        for link in VIDEO_LINKS:
            play_youtube_video(link, disp)
            # Brief pause between videos.
            time.sleep(2)
