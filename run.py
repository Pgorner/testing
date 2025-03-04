import os
import subprocess
import time

MOUNT_POINT = "/mnt/waveshare_sd"

def list_storage_devices():
    """List all storage devices except the Raspberry Pi's internal SD card."""
    try:
        output = subprocess.check_output("lsblk -o NAME,MOUNTPOINT,SIZE,TYPE -n", shell=True).decode()
        devices = []
        print("\n📂 Available External Storage Devices:\n")
        
        for line in output.split("\n"):
            parts = line.split()
            if len(parts) >= 4 and parts[-1] == "disk":  # Only raw storage disks
                device_path = f"/dev/{parts[0]}"
                mountpoint = parts[1] if parts[1] != "─" else "Not Mounted"
                size = parts[2]

                if "mmcblk0" not in device_path:  # Ignore Pi's internal SD
                    devices.append((device_path, mountpoint, size))
                    print(f"[{len(devices)}] {device_path} ({size}) ➜ {mountpoint}")

        return devices
    except Exception as e:
        print(f"❌ Error listing storage devices: {e}")
        return []

def choose_device(devices):
    """Prompt user to choose an external storage device."""
    while True:
        try:
            choice = int(input("\n🔍 Select a device number: "))
            if 1 <= choice <= len(devices):
                return devices[choice - 1]
        except ValueError:
            pass
        print("⚠️ Invalid choice. Try again.")

def mount_sd_card(device):
    """Mounts the SD card from the Waveshare screen to /mnt/waveshare_sd."""
    os.makedirs(MOUNT_POINT, exist_ok=True)

    if os.path.ismount(MOUNT_POINT):
        print(f"✅ Already mounted at {MOUNT_POINT}")
        return True

    print(f"🔄 Mounting {device} to {MOUNT_POINT}...")
    if os.system(f"sudo mount {device} {MOUNT_POINT}") == 0:
        print(f"✅ Mounted {device} at {MOUNT_POINT}")
        return True
    else:
        print(f"❌ Failed to mount {device}.")
        return False

def get_sd_card_info():
    """Print SD card details (size, type)."""
    try:
        output = subprocess.check_output(f"df -h {MOUNT_POINT}", shell=True).decode().split("\n")[1]
        parts = output.split()
        if len(parts) > 1:
            print(f"\n📏 SD Card Size: {parts[1]}")
            print(f"📂 Used Space: {parts[2]}, Free Space: {parts[3]}")
    except Exception:
        print("❌ Could not retrieve SD card info.")

if __name__ == "__main__":
    devices = list_storage_devices()
    if not devices:
        print("❌ No external storage devices found.")
        exit(1)

    device, mountpoint, size = choose_device(devices)

    if mountpoint == "Not Mounted":
        if not mount_sd_card(device):
            exit(1)

    get_sd_card_info()

    # Check if /movies folder exists
    movies_path = os.path.join(MOUNT_POINT, "movies")
    if os.path.exists(movies_path):
        print(f"🎬 Found /movies directory on SD card: {movies_path}")
    else:
        print("⚠️ No '/movies' folder found on SD card.")
    
    os.system(f"ls -lh {movies_path}")  # List files in /movies
