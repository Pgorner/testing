#!/usr/bin/python
# -*- coding: UTF-8 -*-
import time
import logging
import subprocess
from yt_dlp import YoutubeDL

# List your YouTube video URLs here
VIDEO_LINKS = [
    'https://www.youtube.com/watch?v=rtRl9HZGZEE',
    'https://www.youtube.com/watch?v=mLerrgININk',
    # Add more URLs as needed
]

def get_video_stream_url(link):
    """
    Extracts the direct video stream URL from a YouTube link using yt-dlp.
    """
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'skip_download': True,
        'no_warnings': True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            stream_url = info.get('url')
            return stream_url
    except Exception as e:
        logging.error(f"Error extracting URL from {link}: {e}")
        return None

def play_video_mpv(link):
    """
    Plays the video using mpv with hardware acceleration, framebuffer output,
    and a rotation filter to display the video rotated 90°.
    """
    stream_url = get_video_stream_url(link)
    if not stream_url:
        logging.error("Skipping video due to extraction error.")
        return

    logging.info(f"Playing video: {link}")
    cmd = [
        "mpv",
        "--vo=fbdev",         # Video output to framebuffer.
        "--fbdev=/dev/fb1",     # Use /dev/fb1 (Waveshare display).
        "--vf=rotate=90",       # Rotate video 90°.
        "--hwdec=auto",         # Enable hardware decoding if available.
        "--really-quiet",       # Suppress extra output.
        stream_url
    ]
    # Run mpv; this call will block until the video finishes.
    subprocess.run(cmd)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    while True:
        for link in VIDEO_LINKS:
            play_video_mpv(link)
            # Optional: pause briefly between videos.
            time.sleep(2)
