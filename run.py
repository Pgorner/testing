#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys
import time
import logging
import subprocess
import cv2
import numpy as np
from PIL import Image
import st7789
import cst816d

# Directories
VIDEO_DIR = "15fpsd"         # Folder where the original 15 FPS videos are stored.
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
    For a given video, preprocess it by extracting scaled frames,
    converting them to raw RGB NumPy arrays, and saving them as .npy files
    in a folder: processed/<video_basename_without_ext>.
    
    If the .npy files already exist, processing is skipped.
    """
    base = os.path.splitext(os.path.basename(video_path))[0]
    processed_folder = os.path.join(PROCESSED_DIR, base)
    # We check for at least one .npy file as a marker that processing is done.
    npy_marker = os.path.join(processed_folder, "frame_0001.npy")
    if os.path.exists(npy_marker):
        logging.info(f"Processed RGB frames for '{video_path}' already exist in '{processed_folder}'. Skipping preprocessing.")
        return processed_folder

    # Create the processed folder
    os.makedirs(processed_folder, exist_ok=True)
    logging.info(f"Preprocessing video '{video_path}' to folder '{processed_folder}'...")

    # Determine target dimensions.
    target_width = DISPLAY_HEIGHT if LANDSCAPE_MODE else DISPLAY_WIDTH
    target_height = DISPLAY_WIDTH if LANDSCAPE_MODE else DISPLAY_HEIGHT

    # First, extract frames as BMP images using FFmpeg.
    temp_folder = os.path.join(processed_folder, "temp_frames")
    os.makedirs(temp_folder, exist_ok=True)
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"scale={target_width}:{target_height}",
        os.path.join(temp_folder, "frame_%04d.bmp")
    ]
    logging.info("Running FFmpeg command: " + " ".join(ffmpeg_cmd))
    try:
        subprocess.run(ffmpeg_cmd, check=True)
    except subprocess.CalledProcessError as e:
        logging.error("FFmpeg preprocessing failed: " + str(e))
        sys.exit(1)

    # Now, convert each BMP to an RGB NumPy array and save as .npy.
    bmp_files = sorted([
        os.path.join(temp_folder, f)
        for f in os.listdir(temp_folder)
        if f.lower().endswith(".bmp")
    ])
    for frame_path in bmp_files:
        try:
            img = Image.open(frame_path).convert("RGB")
            # Convert to NumPy array.
            arr = np.array(img)
            # Save as .npy file.
            base_frame = os.path.splitext(os.path.basename(frame_path))[0]
            npy_path = os.path.join(processed_folder, f"{base_frame}.npy")
            np.save(npy_path, arr)
        except Exception as e:
            logging.error(f"Error processing frame '{frame_path}': {e}")

    # Optionally, remove the temporary BMP files.
    for f in bmp_files:
        os.remove(f)
    os.rmdir(temp_folder)

    logging.info(f"Preprocessing complete for '{video_path}'.")
    return processed_folder

def play_processed_video(processed_folder, original_video_path, disp, fps=15.0):
    """
    Plays a preprocessed video (frames stored as .npy RGB arrays) with synchronized audio.
    
    - Audio is played concurrently using ffplay (from the original video file).
    - Frames are loaded from the .npy files in the processed folder and displayed at the given FPS.
    - If in landscape mode, the frame is rotated and flipped as needed.
    - A print statement shows each frame's number and the elapsed time.
    """
    # Get sorted list of .npy frame file names.
    frame_files = sorted([
        os.path.join(processed_folder, f)
        for f in os.listdir(processed_folder)
        if f.lower().endswith(".npy")
    ])
    if not frame_files:
        logging.error(f"No processed frames found in folder '{processed_folder}'.")
        return

    logging.info(f"Playing processed video from '{processed_folder}' at {fps} FPS")

    # Determine display dimensions.
    screen_width = DISPLAY_HEIGHT if LANDSCAPE_MODE else DISPLAY_WIDTH
    screen_height = DISPLAY_WIDTH if LANDSCAPE_MODE else DISPLAY_HEIGHT

    # Start audio playback using ffplay (audio only).
    audio_proc = subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-vn", original_video_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    logging.info("Marker: Sound started")

    # Preload the frames into memory.
    preloaded_frames = []
    for npy_file in frame_files:
        try:
            arr = np.load(npy_file)
            preloaded_frames.append(arr)
        except Exception as e:
            logging.error(f"Error loading npy frame '{npy_file}': {e}")
    logging.info(f"Preloaded {len(preloaded_frames)} frames from '{processed_folder}'")

    start_time = time.time()
    logging.info("Marker: Images start")
    for frame_number, arr in enumerate(preloaded_frames):
        expected_time = frame_number / fps
        current_time = time.time() - start_time
        if expected_time > current_time:
            time.sleep(expected_time - current_time)

        # Convert the NumPy array back to a PIL image.
        image = Image.fromarray(arr)

        # Apply rotation/flip if needed.
        if LANDSCAPE_MODE:
            image_disp = image.rotate(ROTATION_DEGREE, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
        else:
            image_disp = image

        # Resize if necessary (should already be at target resolution).
        image_disp = image_disp.resize((screen_width, screen_height))
        disp.show_image(image_disp)

        print(f"Frame {frame_number:04d} displayed at {time.time() - start_time:.3f} sec")

    logging.info("Marker: Images stopped")
    audio_proc.wait()
    logging.info("Marker: Sound stopped")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Ensure the processed directory exists.
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # Initialize Waveshare display and touch controller.
    disp = st7789.st7789()
    disp.clear()
    touch = cst816d.cst816d()

    # Get list of video files from VIDEO_DIR.
    video_files = get_video_list(VIDEO_DIR)
    if not video_files:
        logging.error("No video files found in folder '{}'".format(VIDEO_DIR))
        sys.exit(1)
    logging.info("Found videos: " + ", ".join(video_files))

    # Preprocess each video if needed.
    processed_videos = []  # List of tuples: (processed_folder, original_video_path)
    for video_file in video_files:
        processed_folder = preprocess_video(video_file)
        processed_videos.append((processed_folder, video_file))

    # Main playback loop: cycle through videos.
    while True:
        for processed_folder, original_video_path in processed_videos:
            play_processed_video(processed_folder, original_video_path, disp, fps=15.0)
            disp.clear()
            time.sleep(1)

    # Optional: Touch input loop.
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
