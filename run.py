#!/usr/bin/env python3
import os

# Update this path if your TF card is mounted elsewhere
MOUNT_POINT = '/mnt/sdcard'

def list_sd_files(mount_point):
    try:
        # List all items in the mount directory
        items = os.listdir(mount_point)
        if not items:
            print("The SD card is empty.")
        else:
            print("Files and directories on the SD card:")
            for item in items:
                print(item)
    except FileNotFoundError:
        print(f"Error: The mount point '{mount_point}' does not exist.")
    except PermissionError:
        print(f"Error: Permission denied accessing '{mount_point}'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    list_sd_files(MOUNT_POINT)
