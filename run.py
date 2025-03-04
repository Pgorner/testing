#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os
import time
import logging
import cv2
import numpy as np
import st7789
import smbus
from PIL import Image

# Path to the SD card folder with MP4 videos
SD_CARD_PATH = "/movies"

# Initialize Display
disp = st7789.st7789()
disp.clear()

# Function to detect I2C devices (for debugging SD card connection)
def scan_i2c():
    bus = smbus.SMBus(1)
    devices = []
    for address in range(0x03, 0x78):
        try:
            bus.read_byte(address)
            devices.append(hex(address))
        except OSError:
            pass
    bus.close()
    return devices

# Function to get a list of MP4 videos from the SD card
def get_video_files():
    if not os.path.exists(SD_CARD_PATH):
        logging.error(f"⚠️ SD card path '{SD_CARD_PATH}' not found!")
        return []
    
    videos = sorted([f for f in os.listdir(SD_CARD_PATH) if f.endswith(".mp4")])
    
    if not videos:
        logging.error("⚠️ No MP4 files found in /movies!")
    
    return [os.path.join(SD_CARD_PATH, vid) for vid in videos]

# Function to play a video
def play_video(video_path):
    logging.info(f"🎬 Now playing: {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        logging.error(f"⚠️ Cannot open video: {video_path}")
        return

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_delay = 1.0 / fps if fps > 0 else 0.033  # Default to ~30 FPS if FPS is 0
    
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

# Main loop to continuously play videos from SD card
def main():
    logging.info("🔍 Scanning I2C for SD card...")
    devices = scan_i2c()
    
    if devices:
        logging.info(f"✅ I2C devices found: {devices}")
    else:
        logging.warning("⚠️ No I2C devices detected. Ensure SD card is properly connected.")

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
