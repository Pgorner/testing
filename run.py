#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
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

PROCESSED_DIR = "processed"

def get_processed_video_path(link):
    """
    Extracts the video ID from the YouTube link and returns the path to the
    pre-processed video file in the PROCESSED_DIR.
    """
    ydl_opts = {'quiet': True, 'no_warnings': True}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            video_id = info.get("id")
    except Exception as e:
        logging.error(f"Error extracting video info from {link}: {e}")
        return None

    processed_path = os.path.join(PROCESSED_DIR, f"{video_id}_proc.mp4")
    if not os.path.exists(processed_path):
        logging.error(f"Processed video not found for video ID {video_id}. "
                      "Please run the processing script first.")
        return None
    return processed_path

def play_video_file(video_file, disp):
    """
    Plays a local video file on the Waveshare display by:
      1. Launching an audio process using mpv (with --no-video) so that audio plays.
      2. Opening the video file with OpenCV.
      3. Converting each frame to a PIL Image, resizing it to the display resolution,
         and displaying it.
      4. Maintaining the video's frame rate.
    """
    logging.info(f"Playing video file: {video_file}")
    
    # Start the audio process with mpv (audio-only)
    audio_proc = subprocess.Popen(["mpv", "--no-video", "--really-quiet", video_file])
    
    cap = cv2.VideoCapture(video_file)
    if not cap.isOpened():
        logging.error("Failed to open video file.")
        audio_proc.terminate()
        return

    # Use display's resolution; your display is 240x320.
    disp_width = getattr(disp, 'width', 240)
    disp_height = getattr(disp, 'height', 320)

    # Try to get FPS from the video file; default to 30 if unavailable.
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps == 0:
        fps = 30
    frame_delay = 1.0 / fps
    logging.info(f"Video FPS: {fps:.2f}, target frame delay: {frame_delay:.3f} sec")

    while True:
        start_time = time.time()
        ret, frame = cap.read()
        if not ret:
            break  # End of video file or read error

        # Convert from BGR (OpenCV) to RGB.
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Convert to a PIL Image.
        image = Image.fromarray(frame_rgb)
        # Since the video was pre-rotated and scaled, we only need to ensure it fits the display.
        image = image.resize((disp_width, disp_height))
        disp.show_image(image)

        # Maintain frame rate.
        elapsed = time.time() - start_time
        sleep_time = frame_delay - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

    cap.release()
    audio_proc.terminate()
    logging.info("Finished playing video file.")

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Initialize the Waveshare display.
    disp = st7789.st7789()
    disp.clear()
    
    # (Optional) Initialize touch if needed.
    touch = cst816d.cst816d()
    
    # Loop continuously through the list of processed YouTube videos.
    while True:
        for link in VIDEO_LINKS:
            processed_path = get_processed_video_path(link)
            if processed_path:
                play_video_file(processed_path, disp)
                # Brief pause between videos.
                time.sleep(2)
