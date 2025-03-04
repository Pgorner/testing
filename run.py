#!/usr/bin/python
# -*- coding: UTF-8 -*-
import cv2
import time
import subprocess
import logging
import requests
import numpy as np
from PIL import Image
import st7789

logging.basicConfig(level=logging.INFO)

# Use the full URL including the port where Flask is running.
STREAM_URL = "http://192.168.50.181:5000/video_feed"

def stream_video_and_audio(stream_url, disp):
    """
    Streams video (as MJPEG) and launches mpv for audio (if available).
    - Requests the MJPEG stream from the Flask endpoint.
    - Parses the multipart JPEG frames.
    - Decodes and resizes each frame before displaying on the Waveshare display.
    """
    logging.info(f"Starting stream from: {stream_url}")

    # Start audio playback using mpv (audio-only). Note: MJPEG stream typically doesn't contain audio.
    audio_proc = subprocess.Popen(["mpv", "--no-video", "--really-quiet", stream_url])
    
    try:
        r = requests.get(stream_url, stream=True, timeout=10)
    except Exception as e:
        logging.error(f"Error connecting to stream: {e}")
        audio_proc.terminate()
        return

    if r.status_code != 200:
        logging.error(f"Bad response status code: {r.status_code}")
        audio_proc.terminate()
        return

    bytes_buffer = b""
    # Use the display's resolution.
    disp_width = getattr(disp, 'width', 240)
    disp_height = getattr(disp, 'height', 320)

    try:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                bytes_buffer += chunk
                a = bytes_buffer.find(b'\xff\xd8')  # JPEG start
                b = bytes_buffer.find(b'\xff\xd9')  # JPEG end
                if a != -1 and b != -1 and b > a:
                    jpg = bytes_buffer[a:b+2]
                    bytes_buffer = bytes_buffer[b+2:]
                    # Decode the JPEG image to a numpy array.
                    np_arr = np.frombuffer(jpg, dtype=np.uint8)
                    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        # Convert BGR to RGB.
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        image = Image.fromarray(frame_rgb)
                        image = image.resize((disp_width, disp_height))
                        disp.show_image(image)
                    # Small sleep to prevent overloading the display.
                    time.sleep(0.01)
    except Exception as e:
        logging.error(f"Streaming error: {e}")
    finally:
        audio_proc.terminate()
        logging.info("Stream ended.")

if __name__ == '__main__':
    # Initialize the Waveshare display.
    disp = st7789.st7789()
    disp.clear()

    # Start streaming from the specified URL.
    stream_video_and_audio(STREAM_URL, disp)
