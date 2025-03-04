#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys
import time
import logging
import cv2
import yt_dlp
from PIL import Image
import st7789
import cst816d

# List of YouTube video URLs to loop
VIDEO_URLS = [
    "https://www.youtube.com/watch?v=VIDEO_ID1",
    "https://www.youtube.com/watch?v=VIDEO_ID2",
    "https://www.youtube.com/watch?v=VIDEO_ID3",
]

def download_video(url, output_path):
    """
    Download a YouTube video using yt_dlp.
    If the file already exists, skip downloading.
    """
    if os.path.exists(output_path):
        logging.info(f"{output_path} already exists. Skipping download.")
        return output_path

    ydl_opts = {
        'format': 'mp4[height<=480]',  # limit resolution for faster processing
        'outtmpl': output_path,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        logging.info(f"Downloading {url} to {output_path}")
        ydl.download([url])
    return output_path

def play_video(video_path, disp):
    """
    Play the given video file on the Waveshare display.
    Uses OpenCV to decode frames, converts them to PIL images, resizes,
    and then displays them using disp.show_image.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logging.error(f"Failed to open video file: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 25  # default fallback
    delay = 1.0 / fps

    # Determine display dimensions
    screen_width = disp.width if hasattr(disp, 'width') else 240
    screen_height = disp.height if hasattr(disp, 'height') else 240

    while True:
        ret, frame = cap.read()
        if not ret:
            break  # End of video
        # Convert BGR to RGB format for PIL
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)
        # Resize the image to fit the display
        image = image.resize((screen_width, screen_height))
        disp.show_image(image)
        time.sleep(delay)

    cap.release()

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize Waveshare display and touch controller
    disp = st7789.st7789()
    disp.clear()
    touch = cst816d.cst816d()

    # Prepare local filenames for downloaded videos
    downloaded_videos = []
    for index, url in enumerate(VIDEO_URLS):
        video_filename = f"video_{index+1}.mp4"
        download_video(url, video_filename)
        downloaded_videos.append(video_filename)

    # Main loop: play each video in sequence and then loop back
    while True:
        for video_file in downloaded_videos:
            logging.info(f"Playing video: {video_file}")
            play_video(video_file, disp)

        # Optional: after one loop of videos, you can add any extra actions
        # For example, clear the display between loops:
        disp.clear()
        time.sleep(1)

    # Optional: Touch input loop (if needed, similar to your sample code)
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
