#!/usr/bin/env python3
import os
import psutil

def find_sd_card_mount():
    """
    Find a mount point that is not the boot drive. This example assumes that
    the main system drive is mounted on '/' and that the SD card is mounted elsewhere.
    """
    boot_mount = '/'
    for part in psutil.disk_partitions():
        # Skip the boot partition
        if part.mountpoint == boot_mount:
            continue
        # We assume that an SD card will be a removable device with a FAT or similar filesystem.
        # You may need to adjust this logic based on your system.
        if 'mmcblk' in part.device or part.fstype in ['vfat', 'exfat', 'ntfs', 'ext4']:
            return part.mountpoint
    return None

def list_files(mount_point):
    try:
        items = os.listdir(mount_point)
        if not items:
            print(f"The SD card mounted at {mount_point} is empty.")
        else:
            print(f"Files and directories on the SD card at {mount_point}:")
            for item in items:
                print(item)
    except Exception as e:
        print(f"Error accessing {mount_point}: {e}")

if __name__ == '__main__':
    sd_mount = find_sd_card_mount()
    if sd_mount:
        print(f"SD card detected at: {sd_mount}")
        list_files(sd_mount)
    else:
        print("No SD card mount found. Make sure the TF card is inserted and auto-mounted.")
