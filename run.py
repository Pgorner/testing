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

# Folder containing processed videos (copy this folder to your Pi)
PROCESSED_DIR = "/home/patrick/processed"  # Adjust path if needed

# Display resolution (adjust if different)
DISP_WIDTH = 320
DISP_HEIGHT = 240

def play_video_file(video_file, disp):
    """
    Plays a video file on the Waveshare display:
      - Launches an audio process (mpv in no-video mode) for sound.
      - Uses OpenCV to display video frames.
      - Uses cv2.rotate for efficient 90° rotation.
      - Attempts to synchronize playback by delaying frame display based on measured processing time.
    """
    logging.info(f"Playing video file: {video_file}")
    
    # Start audio playback via mpv (ensure mpv is installed)
    audio_proc = subprocess.Popen(["mpv", "--no-video", "--really-quiet", video_file])
    # Allow audio to initialize
    time.sleep(0.1)
    
    cap = cv2.VideoCapture(video_file)
    if not cap.isOpened():
        logging.error(f"Failed to open video file: {video_file}")
        audio_proc.terminate()
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps == 0:
        fps = 30
    frame_delay = 1.0 / fps
    logging.info(f"Video FPS: {fps:.2f}, target frame delay: {frame_delay:.3f} sec")
    
    while True:
        start_time = time.perf_counter()
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert from BGR to RGB.
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        disp.show_image(image)
        
        elapsed = time.perf_counter() - start_time
        sleep_time = frame_delay - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
            
    cap.release()
    audio_proc.terminate()
    logging.info("Finished playing video file.")

def main():
    logging.basicConfig(level=logging.INFO)
    
    # Initialize the Waveshare display.
    disp = st7789.st7789()
    disp.clear()
    
    # (Optional) Initialize touch if needed.
    touch = cst816d.cst816d()
    
    # List all processed video files.
    video_files = [os.path.join(PROCESSED_DIR, f) for f in os.listdir(PROCESSED_DIR)
                   if f.endswith("_proc.mp4")]
    
    if not video_files:
        logging.error("No processed video files found in the directory.")
        sys.exit(1)
    
    # Loop continuously through the video files.
    while True:
        for video_file in video_files:
            play_video_file(video_file, disp)
            time.sleep(2)  # Brief pause between videos

if __name__=='__main__':
    main()
