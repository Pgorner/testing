#!/usr/bin/env python3
import subprocess
import time
from yt_dlp import YoutubeDL

# List your YouTube video URLs here
VIDEO_LINKS = [
    'https://www.youtube.com/watch?v=VIDEO_ID1',
    'https://www.youtube.com/watch?v=VIDEO_ID2',
    'https://www.youtube.com/watch?v=VIDEO_ID3',
]

def get_video_stream_url(link):
    """
    Uses yt-dlp to extract the direct stream URL for the best quality format.
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
            # The 'url' field holds the direct URL to the video stream.
            stream_url = info.get('url')
            return stream_url
    except Exception as e:
        print(f"Error extracting URL from {link}: {e}")
        return None

def play_video(stream_url):
    """
    Calls omxplayer to play the video using the direct stream URL.
    The '--no-osd' flag disables the on-screen display.
    """
    if stream_url:
        print(f"Playing video stream: {stream_url}")
        try:
            # Start omxplayer and wait until playback finishes.
            subprocess.call(['omxplayer', '--no-osd', stream_url])
        except Exception as e:
            print(f"Error during playback: {e}")

def main():
    while True:
        for link in VIDEO_LINKS:
            print(f"\nProcessing: {link}")
            stream_url = get_video_stream_url(link)
            if stream_url:
                play_video(stream_url)
            else:
                print("Skipping due to extraction error.")
            # Optional: wait a second between videos
            time.sleep(1)

if __name__ == '__main__':
    main()
