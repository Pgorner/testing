import RPi.GPIO as GPIO
import time
import os

# Disable warnings
GPIO.setwarnings(False)

# Define GPIO pins for solenoids
SOLENOID_1 = 22  # GPIO 22 (Pin 15)
SOLENOID_2 = 23  # GPIO 23 (Pin 16)

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(SOLENOID_1, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(SOLENOID_2, GPIO.OUT, initial=GPIO.LOW)

# Track solenoid states
solenoid_state = {
    "1": False,  # Solenoid 1 (False = OFF, True = ON)
    "2": False   # Solenoid 2 (False = OFF, True = ON)
}

def display_status():
    """Clear screen and display the current solenoid states."""
    os.system('clear')  # Clear terminal screen (use 'cls' for Windows)
    print("\n=== Solenoid Control ===")
    print(f"1. Solenoid 1: {'ON' if solenoid_state['1'] else 'OFF'}")
    print(f"2. Solenoid 2: {'ON' if solenoid_state['2'] else 'OFF'}")
    print("Press '1' to toggle Solenoid 1")
    print("Press '2' to toggle Solenoid 2")
    print("Press 'q' to Quit\n")

try:
    while True:
        display_status()
        choice = input("Enter choice: ").strip()

        if choice == "1":
            solenoid_state["1"] = not solenoid_state["1"]
            GPIO.output(SOLENOID_1, GPIO.HIGH if solenoid_state["1"] else GPIO.LOW)
        
        elif choice == "2":
            solenoid_state["2"] = not solenoid_state["2"]
            GPIO.output(SOLENOID_2, GPIO.HIGH if solenoid_state["2"] else GPIO.LOW)

        elif choice.lower() == "q":
            print("\nExiting... Cleaning up GPIO.")
            break

        else:
            print("Invalid input! Press '1', '2', or 'q'.")

        time.sleep(0.5)  # Small delay for smooth operation

except KeyboardInterrupt:
    print("\nProgram interrupted. Cleaning up GPIO...")

finally:
    GPIO.cleanup()
    print("GPIO cleaned up. Program exited.")
