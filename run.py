#!/usr/bin/python
# -*- coding: UTF-8 -*-
import cv2
import time
import subprocess
import logging
from PIL import Image
import st7789

# Configure logging.
logging.basicConfig(level=logging.INFO)

# Stream URL
STREAM_URL = "http://192.168.50.181/video_feed"

def stream_video_and_audio(stream_url, disp):
    """
    Streams video and audio from the provided URL.
    - Launches mpv to handle audio playback (with no video).
    - Uses OpenCV to capture video frames and displays them on the Waveshare display.
    """
    logging.info(f"Starting stream from: {stream_url}")

    # Start audio playback using mpv (audio-only).
    audio_proc = subprocess.Popen(["mpv", "--no-video", "--really-quiet", stream_url])

    # Open the video stream using OpenCV.
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        logging.error("Failed to open video stream.")
        audio_proc.terminate()
        return

    # Use the display's resolution (update if your display differs).
    disp_width = getattr(disp, 'width', 240)
    disp_height = getattr(disp, 'height', 320)

    # Attempt to get the FPS of the stream; default to 30 if unavailable.
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps == 0:
        fps = 30
    frame_delay = 1.0 / fps
    logging.info(f"Stream FPS: {fps:.2f}, frame delay: {frame_delay:.3f} sec")

    # Stream loop: read, process, and display frames.
    while True:
        start_time = time.time()
        ret, frame = cap.read()
        if not ret:
            logging.error("No frame received. Stream might have ended.")
            break

        # Convert frame from BGR (OpenCV default) to RGB.
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Create a PIL Image from the frame.
        image = Image.fromarray(frame_rgb)
        # Resize to the display resolution.
        image = image.resize((disp_width, disp_height))
        # Display the image.
        disp.show_image(image)

        # Wait to maintain the stream's FPS.
        elapsed = time.time() - start_time
        sleep_time = frame_delay - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

    cap.release()
    audio_proc.terminate()
    logging.info("Stream ended.")

if __name__ == '__main__':
    # Initialize the Waveshare display.
    disp = st7789.st7789()
    disp.clear()

    # Start streaming from the specified URL.
    stream_video_and_audio(STREAM_URL, disp)
