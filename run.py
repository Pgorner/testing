import os
import subprocess
import logging

# Define where the SD card will be mounted
MOUNT_PATH = "/mnt/selected_sd"

def list_storage_devices():
    """List all storage devices and their mount points."""
    try:
        output = subprocess.check_output("lsblk -o NAME,MOUNTPOINT,SIZE -n", shell=True).decode()
        devices = []
        print("\n📂 Available Storage Devices:\n")
        for line in output.split("\n"):
            parts = line.split()
            if parts:
                name = parts[0]
                mountpoint = parts[1] if len(parts) > 1 else "Not Mounted"
                size = parts[-1]
                device_path = f"/dev/{name}"
                devices.append((device_path, mountpoint, size))
                print(f"[{len(devices)}] {device_path} ({size}) ➜ {mountpoint}")

        return devices
    except Exception as e:
        logging.error(f"❌ Error listing storage devices: {e}")
        return []

def choose_device(devices):
    """Prompt the user to choose a storage device."""
    while True:
        try:
            choice = int(input("\n🔍 Select a device number: "))
            if 1 <= choice <= len(devices):
                return devices[choice - 1]
        except ValueError:
            pass
        print("⚠️ Invalid choice. Try again.")

def mount_device(device):
    """Mount the selected device."""
    os.makedirs(MOUNT_PATH, exist_ok=True)

    if os.path.ismount(MOUNT_PATH):
        print(f"✅ Already mounted at {MOUNT_PATH}")
        return True

    cmd = f"sudo mount {device} {MOUNT_PATH}"
    if os.system(cmd) == 0:
        print(f"✅ Mounted {device} at {MOUNT_PATH}")
        return True
    else:
        print(f"❌ Failed to mount {device}.")
        return False

if __name__ == "__main__":
    devices = list_storage_devices()
    if not devices:
        print("❌ No storage devices found.")
        exit(1)

    device, mountpoint, size = choose_device(devices)

    if mountpoint == "Not Mounted":
        print(f"🔄 Attempting to mount {device}...")
        if not mount_device(device):
            exit(1)

    print(f"\n📂 Opening: {MOUNT_PATH}\n")
    os.system(f"cd {MOUNT_PATH} && bash")
