#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys
import time
import logging
import st7789
import cst816d
from PIL import Image
import cv2
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

def play_youtube_video(link, disp):
    """
    Plays a YouTube video on the Waveshare display by:
      1. Extracting the stream URL.
      2. Opening the stream with OpenCV.
      3. Converting each frame to a PIL image.
      4. Resizing and displaying it on the Waveshare.
    """
    stream_url = get_video_stream_url(link)
    if not stream_url:
        logging.error("Skipping video due to extraction error.")
        return

    logging.info(f"Playing video: {link}")
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        logging.error("Failed to open video stream.")
        return

    # Use display's resolution if available; adjust these defaults as needed.
    disp_width = getattr(disp, 'width', 240)
    disp_height = getattr(disp, 'height', 240)

    fps = 30  # target framerate
    frame_delay = 1.0 / fps

    while True:
        ret, frame = cap.read()
        if not ret:
            break  # End of video stream or read error
        # OpenCV reads frames as BGR; convert to RGB.
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Convert the NumPy array to a PIL Image.
        image = Image.fromarray(frame_rgb)
        # Resize image to match your display resolution.
        image = image.resize((disp_width, disp_height))
        disp.show_image(image)
        time.sleep(frame_delay)

    cap.release()
    logging.info("Finished playing video.")

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Initialize the Waveshare display
    disp = st7789.st7789()
    disp.clear()
    
    # (Optional) Initialize touch if needed.
    touch = cst816d.cst816d()
    
    # Loop through each YouTube video continuously.
    while True:
        for link in VIDEO_LINKS:
            play_youtube_video(link, disp)
            # Pause briefly between videos if desired.
            time.sleep(2)
#!/usr/bin/python
# -*- coding: UTF-8 -*-
#import chardet
import os
import sys 
import time
import logging
import st7789
import cst816d
from PIL import Image,ImageDraw,ImageFont

if __name__=='__main__':
    
    disp = st7789.st7789()
    disp.clear()
    touch = cst816d.cst816d()
    

    logging.info("show image")
    ImagePath = ["./pic/img_1.jpg", "./pic/img_2.jpg", "./pic/img_3.jpg",]
    for i in range(0, 3):
        image = Image.open(ImagePath[i])	
        # image = image.rotate(0)
        disp.show_image(image)
        time.sleep(4)
    
    disp.clear()

    while True:
        touch.read_touch_data()
        point, coordinates = touch.get_touch_xy()
        if point != 0 and coordinates:
            disp.dre_rectangle(
                coordinates[0]['x'], coordinates[0]['y'],
                coordinates[0]['x'] + 5, coordinates[0]['y'] + 5,
                0x00ff  # 矩形的颜色
            )
            print(f"point 1 coordinates: x={coordinates[0]['x']}, y={coordinates[0]['y']}")
        time.sleep(0.02)
