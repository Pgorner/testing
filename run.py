#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys
import time
import logging
import subprocess
from PIL import Image
import st7789
import cst816d

# Directory where the processed videos (subfolders) are stored.
PROCESSED_DIR = "processed"

# Set this flag True if you want the display in landscape mode.
LANDSCAPE_MODE = True

# Native display dimensions (portrait)
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 320

# In landscape mode, the effective resolution is swapped (320x240) and may require a rotation.
ROTATION_DEGREE = 0

def get_processed_videos(directory):
    """
    Returns a sorted list of full paths to subdirectories in 'directory'.
    Each subdirectory represents one processed video.
    """
    videos = []
    for name in sorted(os.listdir(directory)):
        full_path = os.path.join(directory, name)
        if os.path.isdir(full_path):
            videos.append(full_path)
    return videos

def play_processed_video(processed_folder, disp, fps=10.0):
    """
    Plays a processed video from 'processed_folder' using PNG frames and an AAC audio file.
    
    The folder is expected to contain:
      - PNG frames named like "frame_0001.png", "frame_0002.png", etc.
      - An audio file named "audio.aac".
    
    Frames are displayed at the specified fps while audio plays concurrently.
    """
    # Get sorted list of PNG frames.
    frame_files = sorted([
        os.path.join(processed_folder, f)
        for f in os.listdir(processed_folder)
        if f.lower().endswith(".png") and f.startswith("frame_")
    ])
    if not frame_files:
        logging.error(f"No processed PNG frames found in folder '{processed_folder}'.")
        return

    logging.info(f"Playing processed video from '{processed_folder}' at {fps} FPS")
    
    num_frames = len(frame_files)
    converted_duration = num_frames / fps
    print(f"Extracted {num_frames} frames. At {fps:.2f} fps, video duration is ~{converted_duration:.2f} sec (expected 10.00 fps).")
    
    # Determine display dimensions.
    if LANDSCAPE_MODE:
        screen_width = DISPLAY_HEIGHT
        screen_height = DISPLAY_WIDTH
    else:
        screen_width = DISPLAY_WIDTH
        screen_height = DISPLAY_HEIGHT

    # Get the audio file (expected to be "audio.aac" in the folder).
    audio_file = os.path.join(processed_folder, "audio.aac")
    if not os.path.exists(audio_file):
        logging.error(f"Audio file 'audio.aac' not found in folder '{processed_folder}'.")
        return

    # Start audio playback using ffplay (audio only).
    audio_proc = subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-vn", audio_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    logging.info("Marker: Sound started")

    # Preload all PNG frames into PIL Images.
    preloaded_images = []
    for frame_path in frame_files:
        try:
            img = Image.open(frame_path).convert("RGB")
            if LANDSCAPE_MODE:
                img = img.rotate(ROTATION_DEGREE, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
            preloaded_images.append(img)
        except Exception as e:
            logging.error(f"Error loading PNG frame '{frame_path}': {e}")
    logging.info(f"Preloaded {len(preloaded_images)} frames from '{processed_folder}'")
    
    # Display frames at the target fps using a high-resolution timer.
    start_time = time.perf_counter()
    logging.info("Marker: Images start")
    frame_interval = 1.0 / fps  # 0.1 sec per frame for 10 fps
    for frame_number, image in enumerate(preloaded_images):
        expected_time = frame_number * frame_interval
        # Sleep most of the remaining time, then busy-wait for precision.
        delta = expected_time - (time.perf_counter() - start_time)
        if delta > 0.005:
            time.sleep(delta - 0.005)
        while time.perf_counter() - start_time < expected_time:
            pass
        
        disp.show_image(image)
        print(f"Frame {frame_number:04d} displayed at {time.perf_counter() - start_time:.3f} sec")
    
    logging.info("Marker: Images stopped")
    audio_proc.wait()
    logging.info("Marker: Sound stopped")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Initialize display and touch (if needed).
    disp = st7789.st7789()
    disp.clear()
    touch = cst816d.cst816d()

    # Get all processed video folders.
    processed_videos = get_processed_videos(PROCESSED_DIR)
    if not processed_videos:
        logging.error(f"No processed video folders found in '{PROCESSED_DIR}'.")
        sys.exit(1)
    logging.info("Found processed videos: " + ", ".join(processed_videos))
    
    # Main loop: cycle through each processed video.
    while True:
        for video_folder in processed_videos:
            play_processed_video(video_folder, disp, fps=10.0)
            disp.clear()
            time.sleep(1)

