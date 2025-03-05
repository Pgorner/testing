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
    while factor < 0.5:
        filters.append("atempo=0.5")
        factor /= 0.5
    while factor > 2.0:
        filters.append("atempo=2.0")
        factor /= 2.0
    filters.append(f"atempo={factor:.3f}")
    return ",".join(filters)

def calibrate_frame_time(preloaded_images, disp, sample_frames=10):
    """
    Display a small number of frames (sample_frames) and measure the average time per frame.
    This average time (which includes the overhead of disp.show_image)
    is used to estimate the full video duration.
    """
    n = min(sample_frames, len(preloaded_images))
    start = time.perf_counter()
    for i in range(n):
        disp.show_image(preloaded_images[i])
    end = time.perf_counter()
    avg_time = (end - start) / n
    logging.info(f"Calibration: Displayed {n} frames in {end-start:.3f} sec "
                 f"(avg {avg_time:.3f} sec/frame)")
    return avg_time

def play_processed_video(processed_folder, disp, fps=10.0, calibration_frames=10):
    """
    Plays a video using frames from processed_folder at a given FPS.
    First, it preloads the frames and runs a short calibration (using disp.show_image)
    to estimate the actual average frame display time.
    Then, it uses that estimated time to compute an expected video duration and an audio atempo factor.
    Finally, it plays the audio (using ffplay with the atempo filter chain) concurrently with the video.
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

    # Preload all frames (convert from npy to PIL Images).
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
    
    # --- Calibration: Measure average display time per frame using a sample ---
    avg_frame_time = calibrate_frame_time(preloaded_images, disp, sample_frames=calibration_frames)
    # Estimate expected video duration (if all frames were displayed at this rate)
    expected_video_duration = num_frames * avg_frame_time
    logging.info(f"Estimated video duration based on calibration: {expected_video_duration:.3f} sec")
    
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
            audio_duration = expected_video_duration  # Fallback

        # Compute the atempo factor so that: adjusted_audio_duration = audio_duration / factor ≈ expected_video_duration.
        factor = audio_duration / expected_video_duration if expected_video_duration > 0 else 1.0
        logging.info(f"Audio duration: {audio_duration:.3f}s, expected video duration: {expected_video_duration:.3f}s, "
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

    # Clear the display after calibration (optional)
    disp.clear()
    time.sleep(0.1)

    # --- Actual Playback ---
    logging.info("Starting frame display...")
    # We now use the calibrated average frame time to schedule frames.
    start_time = time.perf_counter()
    for frame_number, image in enumerate(preloaded_images):
        target_time = frame_number * avg_frame_time
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
            play_processed_video(subfolder, disp, fps=10.0, calibration_frames=10)
            disp.clear()
            time.sleep(1)  # Short pause between videos
