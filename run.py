#!/usr/bin/env python3
import os
import subprocess
import logging

# --- Configuration ---
FPS = 10  # Playback framerate
# Directory that holds folders for each processed video.
PROCESSED_DIR = os.path.join(os.getcwd(), "processed")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def play_video(video_folder):
    """
    Plays the video composed of an audio file (audio.aac) and an image sequence
    (frame_%04d.png) from the given folder.
    """
    audio_path = os.path.join(video_folder, "audio.aac")
    frames_pattern = os.path.join(video_folder, "frame_%04d.png")

    if not os.path.exists(audio_path):
        logging.error(f"Audio file not found in {video_folder}")
        return

    # Check if at least one frame exists.
    frame_files = [f for f in os.listdir(video_folder)
                   if f.startswith("frame_") and f.endswith(".png")]
    if not frame_files:
        logging.error(f"No frame images found in {video_folder}")
        return

    logging.info(f"Playing video from folder: {os.path.basename(video_folder)}")

    # Build the ffmpeg command to read the image sequence at FPS and audio,
    # then mux them into a stream piped to ffplay for playback.
    ffmpeg_cmd = [
        "ffmpeg",
        "-framerate", str(FPS),
        "-i", frames_pattern,
        "-i", audio_path,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        # Re-encode audio with AAC at 128kbps instead of copying
        "-c:a", "aac",
        "-b:a", "128k",
        # End the output when the shortest input ends
        "-shortest",
        "-f", "matroska",
        "-"  # Output to stdout
    ]
    ffplay_cmd = ["ffplay", "-autoexit", "-"]

    try:
        ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE)
        ffplay_proc = subprocess.Popen(ffplay_cmd, stdin=ffmpeg_proc.stdout)
        ffmpeg_proc.stdout.close()
        ffplay_proc.wait()
    except Exception as e:
        logging.error(f"Error playing video from {video_folder}: {e}")

def main():
    if not os.path.exists(PROCESSED_DIR):
        logging.error("The 'processed' directory was not found.")
        return

    for folder in sorted(os.listdir(PROCESSED_DIR)):
        video_folder = os.path.join(PROCESSED_DIR, folder)
        if os.path.isdir(video_folder):
            play_video(video_folder)

if __name__ == '__main__':
    main()
