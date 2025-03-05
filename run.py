#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys
import time
import logging
import subprocess
import numpy as np
from PIL import Image
import st7789
import cst816d

PROCESSED_DIR = "processed"  # Base folder containing subfolders for each video

# Set this flag True if you want the display in landscape mode.
LANDSCAPE_MODE = True

# Native display dimensions (portrait)
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 320

ROTATION_DEGREE = 0

def play_processed_video(processed_folder, original_video_path, disp, fps=10.0):
    """
    Plays a video using frames from the processed_folder at a given FPS.
    If an original_video_path is provided and exists, its audio is played concurrently using ffplay.
    """
    # Get sorted list of .npy frame files.
    frame_files = sorted([
        os.path.join(processed_folder, f)
        for f in os.listdir(processed_folder)
        if f.lower().endswith(".npy")
    ])
    if not frame_files:
        logging.error(f"No processed frames found in folder '{processed_folder}'.")
        return

    logging.info(f"Playing video from '{processed_folder}' at {fps} FPS")

    # Determine display dimensions (frames are already at target dimensions).
    if LANDSCAPE_MODE:
        screen_width = DISPLAY_HEIGHT
        screen_height = DISPLAY_WIDTH
    else:
        screen_width = DISPLAY_WIDTH
        screen_height = DISPLAY_HEIGHT

    # Start audio playback using ffplay (if a valid video file is provided).
    if original_video_path and os.path.exists(original_video_path):
        audio_proc = subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-vn", original_video_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logging.info("Audio playback started.")
    else:
        audio_proc = None
        if original_video_path:
            logging.warning(f"Audio file '{original_video_path}' not found. Skipping audio playback.")

    # Preload all frames and convert them to PIL Images.
    preloaded_images = []
    for npy_file in frame_files:
        try:
            arr = np.load(npy_file)
            img = Image.fromarray(arr)
            preloaded_images.append(img)
        except Exception as e:
            logging.error(f"Error loading npy frame '{npy_file}': {e}")
    logging.info(f"Preloaded {len(preloaded_images)} frames from '{processed_folder}'")

    # Main playback loop with high resolution timing.
    start_time = time.perf_counter()
    logging.info("Starting frame display...")
    frame_interval = 1.0 / fps  # Expected time per frame (0.1 sec for 10fps)
    for frame_number, image in enumerate(preloaded_images):
        expected_time = frame_number * frame_interval
        # Calculate time to wait.
        delta = expected_time - (time.perf_counter() - start_time)
        if delta > 0.005:
            time.sleep(delta - 0.005)
        while time.perf_counter() - start_time < expected_time:
            pass

        # Display the preloaded PIL image.
        disp.show_image(image)
        print(f"Frame {frame_number:04d} displayed at {time.perf_counter() - start_time:.3f} sec")

    logging.info("Finished displaying frames.")

    if audio_proc:
        audio_proc.wait()
        logging.info("Audio playback finished.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Ensure the processed folder exists.
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # Initialize display and touch (touch is not used further here).
    disp = st7789.st7789()
    disp.clear()
    touch = cst816d.cst816d()

    # Determine the list of subfolders in the processed folder.
    processed_subfolders = [
        os.path.join(PROCESSED_DIR, d)
        for d in os.listdir(PROCESSED_DIR)
        if os.path.isdir(os.path.join(PROCESSED_DIR, d))
    ]
    if not processed_subfolders:
        logging.error(f"No subfolders found in '{PROCESSED_DIR}'.")
        sys.exit(1)

    # Optionally, you could provide an original video file for audio via command line,
    # but here we assume that each subfolder only contains frame data.
    original_video_path = None
    if len(sys.argv) > 1:
        original_video_path = sys.argv[1]

    # Loop over each subfolder and play the video.
    while True:
        for subfolder in processed_subfolders:
            logging.info(f"Now playing video from subfolder: {subfolder}")
            play_processed_video(subfolder, original_video_path, disp, fps=10.0)
            disp.clear()
            time.sleep(1)  # Short pause between videos
