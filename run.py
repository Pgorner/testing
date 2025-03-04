
#!/usr/bin/env python3
import subprocess
import time
import shutil
from yt_dlp import YoutubeDL

# List your YouTube video URLs here
VIDEO_LINKS = [
    'https://www.youtube.com/watch?v=rtRl9HZGZEE',
    'https://www.youtube.com/watch?v=mLerrgININk',
    'https://www.youtube.com/watch?v=EuaA_Efu_3U',
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

def select_player():
    """
    Check for omxplayer; if not found, check for mpv.
    Returns the command (list) to call the player.
    """
    # Check if omxplayer is available
    omx = shutil.which("omxplayer")
    if omx:
        print("Using omxplayer for playback.")
        return [omx, "--no-osd"]
    
    # Fallback to mpv if available
    mpv = shutil.which("mpv")
    if mpv:
        print("omxplayer not found; using mpv for playback.")
        return [mpv, "--osd-level=0", "--really-quiet"]
    
    print("No supported media player found. Please install omxplayer or mpv.")
    exit(1)

def play_video(stream_url, player_cmd):
    """
    Calls the selected player to play the video using the direct stream URL.
    """
    if stream_url:
        print(f"Playing video stream: {stream_url}")
        try:
            # Start the media player and wait until playback finishes.
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
            # Optional: wait a second between videos
            time.sleep(1)

if __name__ == '__main__':
    main()

