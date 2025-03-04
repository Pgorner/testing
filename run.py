import os
import subprocess
import logging

SD_MOUNT_PATH = "/mnt/waveshare_sd"

def find_sd_card():
    """Find the correct SD card device."""
    try:
        output = subprocess.check_output("lsblk -o NAME,MOUNTPOINT | grep -v '/boot' | grep -v '/ '", shell=True).decode()
        for line in output.split("\n"):
            parts = line.split()
            if len(parts) == 2 and "/mnt" not in parts[1]:  # Not already mounted
                return f"/dev/{parts[0]}"
    except Exception as e:
        logging.error(f"❌ Error detecting SD card: {e}")
    return None

def mount_sd():
    """Mount the SD card if not already mounted."""
    os.makedirs(SD_MOUNT_PATH, exist_ok=True)
    
    # Check if already mounted
    if os.path.ismount(SD_MOUNT_PATH):
        logging.info(f"✅ SD card already mounted at {SD_MOUNT_PATH}")
        return True

    # Find the correct SD card device
    sd_device = find_sd_card()
    if sd_device:
        if os.system(f"sudo mount -o uid=pi,gid=pi -t vfat {sd_device} {SD_MOUNT_PATH}") == 0:
            logging.info(f"✅ SD card mounted at {SD_MOUNT_PATH}")
            return True
        else:
            logging.error("❌ Failed to mount SD card.")
    else:
        logging.error("❌ No SD card found.")
    return False

if __name__ == "__main__":
    if mount_sd():
        logging.info("🎬 Checking for movies...")
        movies = [f for f in os.listdir(SD_MOUNT_PATH + "/movies") if f.endswith(".mp4")]
        if movies:
            logging.info(f"📂 Found {len(movies)} videos: {movies}")
        else:
            logging.error("⚠️ No MP4 files found in /movies/")
