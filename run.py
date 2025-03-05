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

# Directories
VIDEO_DIR = "15fpsd"     # Folder where the original 15 FPS videos are stored.
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
    For a given video, preprocess it by extracting scaled frames
    into a folder processed/<video_basename_without_ext>.
    If the folder already exists, processing is skipped.
    """
    base = os.path.splitext(os.path.basename(video_path))[0]
    processed_folder = os.path.join(PROCESSED_DIR, base)
    if os.path.exists(processed_folder):
        logging.info(f"Processed frames for '{video_path}' already exist in '{processed_folder}'. Skipping preprocessing.")
        return processed_folder

    # Create the processed folder
    os.makedirs(processed_folder, exist_ok=True)
    logging.info(f"Preprocessing video '{video_path}' to folder '{processed_folder}'...")
    
    # Build FFmpeg command to extract frames:
    # Scale to the display size. For landscape mode we want 240x320 (swapped)
    target_width = DISPLAY_HEIGHT if LANDSCAPE_MODE else DISPLAY_WIDTH
    target_height = DISPLAY_WIDTH if LANDSCAPE_MODE else DISPLAY_HEIGHT

    # This command extracts each frame as a BMP image.
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"scale={target_width}:{target_height}",
        os.path.join(processed_folder, "frame_%04d.bmp")
    ]
    logging.info("Running FFmpeg command: " + " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logging.error("FFmpeg preprocessing failed: " + str(e))
        sys.exit(1)
    return processed_folder

def play_processed_video(processed_folder, original_video_path, disp, fps=15.0):
    """
    Plays a preprocessed video (as a folder of frames) with synchronized audio.
    
    - Audio is played concurrently using ffplay (from the original video file).
    - Frames are loaded from the processed folder and displayed at the given FPS.
    - If in landscape mode, the frame is rotated and flipped as needed.
    """
    # Get sorted list of frame file names.
    frame_files = sorted([
        os.path.join(processed_folder, f)
        for f in os.listdir(processed_folder)
        if f.lower().endswith(".bmp")
    ])
    if not frame_files:
        logging.error(f"No frames found in processed folder '{processed_folder}'.")
        return

    logging.info(f"Playing processed video from '{processed_folder}' at {fps} FPS")
    
    # Determine display dimensions (frames are already scaled to target)
    screen_width = DISPLAY_HEIGHT if LANDSCAPE_MODE else DISPLAY_WIDTH
    screen_height = DISPLAY_WIDTH if LANDSCAPE_MODE else DISPLAY_HEIGHT

    # Start audio playback using ffplay (audio only)
    audio_proc = subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-vn", original_video_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Synchronize display based on FPS.
    start_time = time.time()
    for frame_number, frame_path in enumerate(frame_files):
        # Calculate the expected display time.
        expected_time = frame_number / fps
        current_time = time.time() - start_time
        if expected_time > current_time:
            time.sleep(expected_time - current_time)

        try:
            image = Image.open(frame_path)
        except Exception as e:
            logging.error(f"Error opening frame '{frame_path}': {e}")
            continue

        # Apply rotation/flip if needed.
        if LANDSCAPE_MODE:
            image = image.rotate(ROTATION_DEGREE, expand=True)
            image = image.transpose(Image.FLIP_LEFT_RIGHT)

        # In this case, frames are already scaled, but you can resize if needed:
        image = image.resize((screen_width, screen_height))
        disp.show_image(image)

    audio_proc.wait()  # Wait for audio to finish

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Ensure the processed directory exists
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # Initialize Waveshare display and touch controller
    disp = st7789.st7789()
    disp.clear()
    touch = cst816d.cst816d()

    # Get list of video files from VIDEO_DIR
    video_files = get_video_list(VIDEO_DIR)
    if not video_files:
        logging.error("No video files found in folder '{}'".format(VIDEO_DIR))
        sys.exit(1)
    logging.info("Found videos: " + ", ".join(video_files))

    # Preprocess each video if needed, and then play in a loop.
    processed_videos = []  # List of tuples: (processed_folder, original_video_path)
    for video_file in video_files:
        processed_folder = preprocess_video(video_file)
        processed_videos.append((processed_folder, video_file))

    # Main playback loop: cycle through videos.
    while True:
        for processed_folder, original_video_path in processed_videos:
            play_processed_video(processed_folder, original_video_path, disp, fps=15.0)
            # Clear display between videos
            disp.clear()
            time.sleep(1)

    # Optional: Touch input loop (if needed)
    while True:
        touch.read_touch_data()
        point, coordinates = touch.get_touch_xy()
        if point != 0 and coordinates:
            disp.dre_rectangle(
                coordinates[0]['x'], coordinates[0]['y'],
                coordinates[0]['x'] + 5, coordinates[0]['y'] + 5,
                0x00ff  # rectangle color
            )
            print(f"Touch coordinates: x={coordinates[0]['x']}, y={coordinates[0]['y']}")
        time.sleep(0.02)
