#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os
import time
import logging
import cv2
import numpy as np
import psutil
import spidev
import st7789
from PIL import Image

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Initialize Display ---
disp = st7789.st7789()
disp.clear()

# --- SPI Configuration for SD Card (Waveshare screen) ---
SPI_BUS = 0  # Default SPI bus
SPI_DEVICE = 1  # The SD card slot is on SPI device 1
SD_MOUNT_PATH = "/mnt/waveshare_sd"

# Function to initialize SPI SD Card
def init_spi_sd():
    try:
        spi = spidev.SpiDev()
        spi.open(SPI_BUS, SPI_DEVICE)
        spi.max_speed_hz = 8000000  # Set SPI speed
        spi.mode = 0b00
        logging.info("✅ SPI initialized for Waveshare SD card.")
        return spi
    except Exception as e:
        logging.error(f"❌ SPI SD init failed: {e}")
        return None

# Function to mount the SD card
def mount_sd():
    os.makedirs(SD_MOUNT_PATH, exist_ok=True)
    cmd = f"sudo mount -o uid=pi,gid=pi -t vfat /dev/mmcblk0 {SD_MOUNT_PATH}"
    if os.system(cmd) == 0:
        logging.info(f"✅ SD card mounted at {SD_MOUNT_PATH}")
        return True
    else:
        logging.error("❌ Failed to mount SD card.")
        return False

# Function to list MP4 videos in /movies on the SD card
def get_video_files():
    movies_path = os.path.join(SD_MOUNT_PATH, "movies")

    if not os.path.exists(movies_path):
        logging.error(f"⚠️ No '/movies' folder found on SD card ({SD_MOUNT_PATH})!")
        return []

    videos = sorted([f for f in os.listdir(movies_path) if f.endswith(".mp4")])

    if not videos:
        logging.error("⚠️ No MP4 files found in '/movies/' on SD card!")
    
    return [os.path.join(movies_path, vid) for vid in videos]

# Function to play a video
def play_video(video_path):
    logging.info(f"🎬 Now playing: {video_path}")
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        logging.error(f"⚠️ Cannot open video: {video_path}")
        return

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_delay = 1.0 / fps if fps > 0 else 0.033  # Default ~30 FPS if FPS is 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            logging.info(f"🔁 Finished playing {video_path}, moving to next video...")
            break

        frame = cv2.resize(frame, (320, 240))  # Resize to match ST7789 resolution
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        image = Image.fromarray(frame)  # Convert to PIL Image
        disp.show_image(image)  # Display frame

        time.sleep(frame_delay)  # Maintain video FPS

    cap.release()

# Main function to play videos in loop
def main():
    logging.info("🔍 Initializing SPI SD card interface...")
    spi = init_spi_sd()
    
    if not spi:
        logging.error("❌ SPI SD card initialization failed! Exiting...")
        return
    
    if not mount_sd():
        logging.error("❌ SD card mount failed! Retrying in 10 seconds...")
        time.sleep(10)
        return

    while True:
        video_files = get_video_files()
        if not video_files:
            logging.error("❌ No valid MP4 files found. Retrying in 10 seconds...")
            time.sleep(10)
            continue  # Try again after 10 seconds

        for video in video_files:
            play_video(video)  # Play each video in sequence
            time.sleep(2)  # Short delay before switching videos

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("🛑 Stopping playback.")
        disp.clear()
