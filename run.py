#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys
import subprocess
import logging
import numpy as np
from PIL import Image

# Base folder to hold processed frame subfolders.
PROCESSED_DIR = "processed"

# Settings matching your display configuration.
LANDSCAPE_MODE = True
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 320
ROTATION_DEGREE = 0  # Options: 0, 90, 180, 270

def process_video(input_video_path, output_subfolder, fps=10):
    """
    Process the input video with ffmpeg:
      - Extract frames at the specified fps.
      - Resize frames to the target dimensions.
      - Rotate frames if needed.
      - Save frames as PNGs, then convert each to a .npy file.
    The PNG files are removed after conversion.
    """
    os.makedirs(output_subfolder, exist_ok=True)
    
    # Determine the target width and height.
    if LANDSCAPE_MODE:
        width = DISPLAY_HEIGHT  # 320
        height = DISPLAY_WIDTH  # 240
    else:
        width = DISPLAY_WIDTH   # 240
        height = DISPLAY_HEIGHT # 320

    # Build the ffmpeg video filter string.
    # Start with fps and scale.
    vf_filters = f"fps={fps},scale={width}:{height}"
    
    # Append rotation filters if necessary.
    # ffmpeg's transpose filter rotates 90 degrees clockwise (transpose=1) or counter-clockwise (transpose=2).
    if ROTATION_DEGREE == 90:
        vf_filters += ",transpose=1"
    elif ROTATION_DEGREE == 180:
        # Apply two 90-degree rotations.
        vf_filters += ",transpose=1,transpose=1"
    elif ROTATION_DEGREE == 270:
        vf_filters += ",transpose=2"
    
    # Define output pattern for PNG images.
    output_pattern = os.path.join(output_subfolder, "frame_%04d.png")
    cmd = [
        "ffmpeg",
        "-i", input_video_path,
        "-vf", vf_filters,
        output_pattern
    ]
    logging.info("Running ffmpeg command: " + " ".join(cmd))
    subprocess.run(cmd, check=True)

    # Convert extracted PNG frames to .npy files.
    frame_files = sorted([
        os.path.join(output_subfolder, f)
        for f in os.listdir(output_subfolder)
        if f.lower().endswith(".png")
    ])
    for png_file in frame_files:
        try:
            img = Image.open(png_file)
            arr = np.array(img)
            npy_file = os.path.splitext(png_file)[0] + ".npy"
            np.save(npy_file, arr)
        except Exception as e:
            logging.error(f"Error processing {png_file}: {e}")
    
    # Optionally, remove the PNG files.
    for png_file in frame_files:
        os.remove(png_file)
    
    logging.info(f"Processed {len(frame_files)} frames from video '{input_video_path}' into folder '{output_subfolder}'")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: process_video.py <input_video_file>")
        sys.exit(1)
    
    input_video_path = sys.argv[1]
    # Use the base name of the video (without extension) as the subfolder name.
    video_name = os.path.splitext(os.path.basename(input_video_path))[0]
    output_subfolder = os.path.join(PROCESSED_DIR, video_name)
    
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    process_video(input_video_path, output_subfolder, fps=10)
