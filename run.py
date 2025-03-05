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

def build_atempo_chain(factor):
    """
    Decompose the overall atempo factor into a chain of factors,
    each within the allowed range [0.5, 2.0].
    """
    filters = []
    # For factors lower than 0.5, chain multiples of 0.5.
    while factor < 0.5:
        filters.append("atempo=0.5")
        factor /= 0.5
    # For factors higher than 2.0, chain multiples of 2.0.
    while factor > 2.0:
        filters.append("atempo=2.0")
        factor /= 2.0
    filters.append(f"atempo={factor:.3f}")
    return ",".join(filters)

def measure_video_duration(preloaded_images, fps):
    """
    Run a dry-run of the timing loop (without displaying images)
    to measure the actual duration it takes to iterate through all frames.
    """
    num_frames = len(preloaded_images)
    frame_interval = 1.0 / fps
    start_time = time.perf_counter()
    for i in range(num_frames):
        # Target time for frame i based on the ideal timing
        target_time = i * frame_interval
        # Busy-wait until that target time is reached.
        while time.perf_counter() - start_time < target_time:
            pass
    return time.perf_counter() - start_time

def play_processed_video(processed_folder, disp, fps=10.0):
    """
    Plays a video using frames from processed_folder at a given FPS.
    First, measures the actual duration of the playback loop.
    Then, plays the corresponding audio (audio.mp3 in the same folder)
    using an atempo filter chain that adjusts audio speed to match the measured video duration.
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

    logging.info(f"Preparing to play video from '{processed_folder}' at {fps} FPS")

    # Preload all frames and convert them to PIL Images.
    preloaded_images = []
    for npy_file in frame_files:
        try:
            arr = np.load(npy_file)
            img = Image.fromarray(arr)
            preloaded_images.append(img)
        except Exception as e:
            logging.error(f"Error loading npy frame '{npy_file}': {e}")
    num_frames = len(preloaded_images)
    logging.info(f"Preloaded {num_frames} frames from '{processed_folder}'")
    
    # --- Calibration: Measure the actual playback duration ---
    measured_duration = measure_video_duration(preloaded_images, fps)
    logging.info(f"Measured video duration: {measured_duration:.3f} seconds")
    
    # --- Prepare audio playback ---
    audio_path = os.path.join(processed_folder, "audio.mp3")
    audio_proc = None
    if os.path.exists(audio_path):
        # Determine audio duration using ffprobe.
        try:
            result = subprocess.check_output([
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ])
            audio_duration = float(result.strip())
        except Exception as e:
            logging.error("Failed to get audio duration: " + str(e))
            audio_duration = measured_duration  # Fallback

        # Compute the atempo factor based on measured video duration.
        # We want: adjusted_audio_duration = audio_duration / factor == measured_duration
        # So factor = audio_duration / measured_duration.
        factor = audio_duration / measured_duration if measured_duration > 0 else 1.0
        logging.info(f"Audio duration: {audio_duration:.3f}s, measured video duration: {measured_duration:.3f}s, "
                     f"raw atempo factor: {factor:.3f}")
        atempo_chain = build_atempo_chain(factor)
        logging.info(f"Using atempo filter chain: {atempo_chain}")

        audio_cmd = [
            "ffplay", "-nodisp", "-autoexit", "-vn",
            "-af", atempo_chain,
            audio_path
        ]
        # Launch audio in a separate process.
        audio_proc = subprocess.Popen(audio_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info("Audio playback started from " + audio_path)
    else:
        logging.warning(f"Audio file '{audio_path}' not found. Skipping audio playback.")

    # --- Actual Playback: Use the measured duration for target timing ---
    start_time = time.perf_counter()
    logging.info("Starting frame display...")
    # We'll distribute frames evenly over the measured duration.
    for frame_number, image in enumerate(preloaded_images):
        target_time = (frame_number / (num_frames - 1)) * measured_duration if num_frames > 1 else 0
        while time.perf_counter() - start_time < target_time:
            pass
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

    # Loop over each subfolder and play the video with its audio.
    while True:
        for subfolder in processed_subfolders:
            logging.info(f"Now playing video from subfolder: {subfolder}")
            play_processed_video(subfolder, disp, fps=10.0)
            disp.clear()
            time.sleep(1)  # Short pause between videos
