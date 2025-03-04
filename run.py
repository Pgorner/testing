import pygame
import time
import sys
from io import BytesIO
from PIL import Image
import subprocess

# Configuration parameters (adjust paths and resolution as needed)
FPS = 30
SCREEN_WIDTH = 288
SCREEN_HEIGHT = 240
MJPEG_FILE = "/Videos/1/288_30fps.mjpeg"
AAC_FILE = "/Videos/1/44100.aac"

def mjpeg_frame_generator(mjpeg_file_path):
    """
    Generator that yields individual JPEG frames from an MJPEG file.
    (For simplicity, this implementation reads the whole file into memory.
    For very large files you may want to read in chunks.)
    """
    with open(mjpeg_file_path, "rb") as f:
        data = f.read()
    start = 0
    while True:
        # Find the start (0xFFD8) and end (0xFFD9) markers for a JPEG
        start_index = data.find(b'\xff\xd8', start)
        if start_index == -1:
            break
        end_index = data.find(b'\xff\xd9', start_index)
        if end_index == -1:
            break
        jpeg_data = data[start_index:end_index+2]
        yield jpeg_data
        start = end_index + 2

def play_audio(aac_file_path):
    """
    Start playing the AAC file using ffplay in a separate process.
    The '-nodisp' option hides video output, and '-autoexit' quits when done.
    """
    return subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", aac_file_path])

def main():
    # Initialize Pygame and set up the display
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("MJPEG Video Playback")
    clock = pygame.time.Clock()

    # Start audio playback
    audio_process = play_audio(AAC_FILE)
    
    # Create a frame generator for the MJPEG file
    frame_generator = mjpeg_frame_generator(MJPEG_FILE)
    
    start_time = time.time()
    frame_count = 0

    # Main loop: decode and display each frame at the correct FPS
    for jpeg_data in frame_generator:
        # Allow graceful exit on window close
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Decode JPEG frame using Pillow
        try:
            image = Image.open(BytesIO(jpeg_data))
        except Exception as e:
            print("Error decoding frame:", e)
            continue
        image = image.convert("RGB")
        frame_surface = pygame.image.fromstring(image.tobytes(), image.size, image.mode)
        
        # Draw the frame on the screen
        screen.blit(frame_surface, (0, 0))
        pygame.display.flip()

        frame_count += 1
        # Wait so that playback is at the target FPS
        clock.tick(FPS)
    
    # Optionally, wait for audio to finish if needed
    audio_process.wait()
    pygame.quit()

if __name__ == "__main__":
    main()
