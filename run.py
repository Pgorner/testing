#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys
import time
import logging
import subprocess
import cv2
from yt_dlp import YoutubeDL
from PIL import Image
import st7789
import cst816d

# List your YouTube video URLs here
VIDEO_LINKS = [
    'https://www.youtube.com/watch?v=rtRl9HZGZEE',
    'https://www.youtube.com/watch?v=mLerrgININk',
    # Add more URLs as needed
]

# Set display resolution (adjust these if your display resolution is different)
DISP_WIDTH = 240
DISP_HEIGHT = 240

# Directories for downloaded and processed videos.
DOWNLOAD_DIR = "downloads"
PROCESSED_DIR = "processed"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def download_video(link):
    """
    Download the video using yt-dlp if not already downloaded.
    Returns a tuple: (video_id, downloaded_file_path)
    """
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            video_id = info.get("id")
            ext = info.get("ext", "mp4")
            downloaded_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")
            logging.info(f"Downloaded video {video_id} to {downloaded_path}")
            return video_id, downloaded_path
    except Exception as e:
        logging.error(f"Error downloading video from {link}: {e}")
        return None, None

def process_video(video_id, input_path):
    """
    Process the video with ffmpeg:
      - Rotate 90° clockwise.
      - Scale to (DISP_WIDTH x DISP_HEIGHT).
      - Copy audio.
    The processed video is saved in the PROCESSED_DIR.
    Returns the processed file path.
    """
    output_path = os.path.join(PROCESSED_DIR, f"{video_id}_proc.mp4")
    if os.path.exists(output_path):
        logging.info(f"Processed video already exists: {output_path}")
        return output_path

    # Build ffmpeg command.
    # The filter "transpose=1" rotates 90° clockwise.
    # "scale=DISP_WIDTH:DISP_HEIGHT" resizes the video.
    cmd = [
        "ffmpeg",
        "-y",  # overwrite output if exists
        "-i", input_path,
        "-vf", f"transpose=1,scale={DISP_WIDTH}:{DISP_HEIGHT}",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-c:a", "copy",
        output_path
    ]
    logging.info(f"Processing video {video_id} with ffmpeg...")
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info(f"Processed video saved to {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logging.error(f"ffmpeg processing failed for {video_id}: {e}")
        return None

def prepare_video(link):
    """
    For a given YouTube link, download (if necessary) and process the video.
    Returns the processed file path.
    """
    # Use yt-dlp in 'download' mode to get the video ID and download if needed.
    # We attempt to extract the video ID without downloading first.
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            video_id = info.get("id")
    except Exception as e:
        logging.error(f"Error extracting video info from {link}: {e}")
        return None

    processed_path = os.path.join(PROCESSED_DIR, f"{video_id}_proc.mp4")
    if os.path.exists(processed_path):
        logging.info(f"Using existing processed video for {video_id}")
        return processed_path

    # Download if necessary.
    downloaded_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
    if not os.path.exists(downloaded_path):
        logging.info(f"Video {video_id} not found in downloads. Downloading...")
        video_id, downloaded_path = download_video(link)
        if not downloaded_path:
            return None
    else:
        logging.info(f"Found downloaded video for {video_id}: {downloaded_path}")

    # Process the video.
    processed_path = process_video(video_id, downloaded_path)
    return processed_path

def play_video_file(video_file, disp):
    """
    Plays the video file on the Waveshare display:
      - Launches an audio process via mpv for audio.
      - Opens the video file with OpenCV for frame-by-frame display.
      - Uses cv2.rotate to rotate frames 90° (more efficient than PIL rotation).
      - Displays each frame via disp.show_image.
    """
    logging.info(f"Playing video file: {video_file}")
    
    # Launch audio playback using mpv in no-video mode.
    audio_proc = subprocess.Popen(["mpv", "--no-video", "--really-quiet", video_file])
    
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
        start_time = time.time()
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert from BGR to RGB.
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Rotate using OpenCV (90° clockwise)
        rotated = cv2.rotate(frame_rgb, cv2.ROTATE_90_CLOCKWISE)
        # Convert to PIL Image.
        image = Image.fromarray(rotated)
        disp.show_image(image)

        elapsed = time.time() - start_time
        sleep_time = frame_delay - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
            
    cap.release()
    audio_proc.terminate()
    logging.info("Finished playing video file.")

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Initialize the Waveshare display.
    disp = st7789.st7789()
    disp.clear()
    
    # (Optional) Initialize touch if needed.
    touch = cst816d.cst816d()
    
    # For each video link, prepare the video (download & process if needed)
    prepared_videos = []
    for link in VIDEO_LINKS:
        logging.info(f"Preparing video from: {link}")
        processed_file = prepare_video(link)
        if processed_file:
            prepared_videos.append(processed_file)
    
    if not prepared_videos:
        logging.error("No videos are available for playback. Exiting.")
        sys.exit(1)
    
    # Loop continuously through the prepared videos.
    while True:
        for video_file in prepared_videos:
            play_video_file(video_file, disp)
            # Brief pause between videos.
            time.sleep(2)
