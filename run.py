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

# Directories
VIDEO_DIR = "15fpsd"         # Folder where the original videos are stored.
PROCESSED_DIR = "processed"  # Base folder to hold processed frames.

# Set this flag True if you want the display in landscape mode.
LANDSCAPE_MODE = True

# Native display dimensions (portrait)
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 320

# In landscape mode, the effective resolution is swapped: 320x240.
# Adjust this rotation angle as needed: try 0, 90, 180, or 270.
ROTATION_DEGREE = 0

def get_video_list(directory):
    """
    Returns a sorted list of full paths to MP4 videos in the specified directory.
    """
    videos = []
    for filename in sorted(os.listdir(directory)):
        if filename.lower().endswith(".mp4"):
            videos.append(os.path.join(directory, filename))
    return videos

def preprocess_video(video_path):
    """
    For a given video, preprocess it by extracting frames, converting them to
    display-ready RGB NumPy arrays (with rotation, flip, and resizing applied),
    and saving them as .npy files in a folder:
        processed/<video_basename_without_ext>/
    If the marker file exists, the processing is skipped.
    """
    base = os.path.splitext(os.path.basename(video_path))[0]
    processed_folder = os.path.join(PROCESSED_DIR, base)
    marker_file = os.path.join(processed_folder, "frame_0001.npy")
    if os.path.exists(marker_file):
        logging.info(f"Processed RGB frames for '{video_path}' already exist in '{processed_folder}'. Skipping preprocessing.")
        return processed_folder

    os.makedirs(processed_folder, exist_ok=True)
    logging.info(f"Preprocessing video '{video_path}' to folder '{processed_folder}'...")

    # Determine target dimensions.
    if LANDSCAPE_MODE:
        target_width = DISPLAY_HEIGHT  # e.g. 320
        target_height = DISPLAY_WIDTH  # e.g. 240
    else:
        target_width = DISPLAY_WIDTH
        target_height = DISPLAY_HEIGHT

    # Extract frames as BMP images using FFmpeg with enforced 10fps.
    temp_folder = os.path.join(processed_folder, "temp_frames")
    os.makedirs(temp_folder, exist_ok=True)
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", video_path,
        "-r", "10",  # Force output to 10 fps
        "-vf", f"scale={target_width}:{target_height}",
        os.path.join(temp_folder, "frame_%04d.bmp")
    ]
    logging.info("Running FFmpeg command: " + " ".join(ffmpeg_cmd))
    try:
        subprocess.run(ffmpeg_cmd, check=True)
    except subprocess.CalledProcessError as e:
        logging.error("FFmpeg preprocessing failed: " + str(e))
        sys.exit(1)

    # Process each BMP frame to create a display-ready NumPy array.
    bmp_files = sorted([
        os.path.join(temp_folder, f)
        for f in os.listdir(temp_folder)
        if f.lower().endswith(".bmp")
    ])
    for frame_path in bmp_files:
        try:
            img = Image.open(frame_path).convert("RGB")
            # Apply rotation and flip if in landscape mode.
            if LANDSCAPE_MODE:
                img = img.rotate(ROTATION_DEGREE, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
            # The frame should already be at target dimensions from FFmpeg,
            # but we call resize() just to be safe.
            img = img.resize((target_width, target_height))
            arr = np.array(img)
            # Save the array as .npy file.
            base_frame = os.path.splitext(os.path.basename(frame_path))[0]
            npy_path = os.path.join(processed_folder, f"{base_frame}.npy")
            np.save(npy_path, arr)
        except Exception as e:
            logging.error(f"Error processing frame '{frame_path}': {e}")

    # Clean up the temporary BMP files.
    for f in bmp_files:
        os.remove(f)
    os.rmdir(temp_folder)

    logging.info(f"Preprocessing complete for '{video_path}'.")
    return processed_folder

def play_processed_video(processed_folder, original_video_path, disp, fps=10.0):
    """
    Plays a preprocessed video (frames stored as display-ready .npy RGB arrays)
    with synchronized audio.
    
    - Audio is played concurrently using ffplay (from the original video file).
    - The .npy frames are loaded once into memory and immediately converted
      to PIL Images (this conversion is done only once per frame).
    - The PIL Images are then iterated over at the given FPS.
    - Timing is managed with a high-resolution timer.
    
    This version uses a sleep-then-busy-wait approach for minimal delay.
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

    logging.info(f"Playing processed video from '{processed_folder}' at {fps} FPS")

    # --- Print conversion summary ---
    num_frames = len(frame_files)
    # Calculate the expected duration from the extracted frames
    converted_duration = num_frames / fps
    print(f"Extracted {num_frames} frames. At {fps:.2f} fps, the converted video duration is ~{converted_duration:.2f} sec (expected 10.00 fps).")
    # ---------------------------------

    # Determine display dimensions (frames are already at target dimensions).
    if LANDSCAPE_MODE:
        screen_width = DISPLAY_HEIGHT
        screen_height = DISPLAY_WIDTH
    else:
        screen_width = DISPLAY_WIDTH
        screen_height = DISPLAY_HEIGHT

    # Start audio playback using ffplay (audio only).
    audio_proc = subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-vn", original_video_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    logging.info("Marker: Sound started")

    # Preload all frames and convert them to PIL Images.
    preloaded_images = []
    for npy_file in frame_files:
        try:
            arr = np.load(npy_
