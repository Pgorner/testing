#!/usr/bin/env python3
import subprocess
import time
import os
from yt_dlp import YoutubeDL

# List your YouTube video URLs here
VIDEO_LINKS = [
    'https://www.youtube.com/watch?v=rtRl9HZGZEE',
    'https://www.youtube.com/watch?v=mLerrgININk',
    # Add more URLs as needed.
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
            stream_url = info.get('url')
            return stream_url
    except Exception as e:
        print(f"Error extracting URL from {link}: {e}")
        return None

def select_player():
    """
    For output on the Waveshare screen, we use mpv with framebuffer output.
    This requires that your Waveshare display is mapped to /dev/fb1.
    """
    fb_device = "/dev/fb1"
    if os.path.exists(fb_device):
        # Build the mpv command for framebuffer output:
        # --vo=fbdev selects the framebuffer video output.
        # --fbdev sets the framebuffer device to use.
        mpv_path = "mpv"
        # Check that mpv is installed
        if subprocess.call(["which", mpv_path], stdout=subprocess.DEVNULL) != 0:
            print("mpv not found. Please install mpv.")
            exit(1)
        cmd = [mpv_path, "--osd-level=0", "--really-quiet", "--vo=fbdev", f"--fbdev={fb_device}"]
        print(f"Using mpv with framebuffer device {fb_device} for playback.")
        return cmd
    else:
        print(f"{fb_device} not found. Please ensure your Waveshare display is configured and the framebuffer device exists.")
        exit(1)

def play_video(stream_url, player_cmd):
    """
    Calls mpv to play the video using the direct stream URL.
    """
    if stream_url:
        print(f"Playing video stream: {stream_url}")
        try:
            subprocess.call(player_cmd + [stream_url])
        except Exception as e:
            print(f"Error during playback: {e}")

def main():
    player_cmd = select_player()
    while True:
        for link in VIDEO_LINKS:
            print(f"\nProcessing: {link}")
            stream_url = get_video_stream_url(link)
            if stream_url:
                play_video(stream_url, player_cmd)
            else:
                print("Skipping due to extraction error.")
            # Wait a short moment between videos
            time.sleep(1)

if __name__ == '__main__':
    main()
