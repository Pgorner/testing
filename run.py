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
    each within the range [0.5, 2.0], which when multiplied yield the desired factor.
    """
    filters = []
    # If factor is less than 0.5, chain multiple atempo=0.5 filters.
    while factor < 0.5:
        filters.append("atempo=0.5")
        factor /= 0.5
    # If factor is greater than 2.0, chain multiple atempo=2.0 filters.
    while factor > 2.0:
        filters.append("atempo=2.0")
        factor /= 2.0
    # Append the remaining factor.
    filters.append(f"atempo={factor:.3f}")
    return ",".join(filters)

def play_processed_video(processed_folder, disp, fps=10.0):
    """
    Plays a video using frames from the processed_folder at a given FPS.
    Also plays the corresponding audio (audio.mp3 in the same folder) concurrently,
    adjusting the audio playback speed to match the video's intended duration.
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
    
    # Calculate intended video duration.
    video_duration = num_frames / fps

    # Prepare audio playback.
    audio_path = os.path.join(processed_folder, "audio.mp3")
    audio_proc = None
    if os.path.exists(audio_path):
        # Use ffprobe to determine the audio duration.
        try:
            result = subprocess.check_output([
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ])
            audio_duration = float(result.strip())
        except Exception as e:
            logging.error("Failed to get audio duration: " + str(e))
            audio_duration = video_duration  # fallback

        # Compute the overall factor so that: adjusted_duration = input_duration / factor == video_duration.
        # That is, factor = audio_duration / video_duration.
        factor = audio_duration / video_duration if video_duration > 0 else 1.0
        logging.info(f"Audio duration: {audio_duration:.3f}s, Video duration: {video_duration:.3f}s, "
                     f"raw atempo factor: {factor:.3f}")
        # Build a chain of atempo filters if necessary.
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

    # Loop over each subfolder and play the video with its audio.
    while True:
        for subfolder in processed_subfolders:
            logging.info(f"Now playing video from subfolder: {subfolder}")
            play_processed_video(subfolder, disp, fps=10.0)
            disp.clear()
            time.sleep(1)  # Short pause between videos
