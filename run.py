import RPi.GPIO as GPIO
import time

# Define GPIO pins
SOLENOID_1 = 28  # GPIO 28 for Solenoid 1
SOLENOID_2 = 29  # GPIO 29 for Solenoid 2

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(SOLENOID_1, GPIO.OUT)
GPIO.setup(SOLENOID_2, GPIO.OUT)

# Function to control solenoids
def control_solenoid(solenoid, action):
    if solenoid == "1":
        pin = SOLENOID_1
    elif solenoid == "2":
        pin = SOLENOID_2
    else:
        print("Invalid solenoid number! Choose 1 or 2.")
        return

    if action == "on":
        GPIO.output(pin, GPIO.HIGH)
        print(f"Solenoid {solenoid} is ON")
    elif action == "off":
        GPIO.output(pin, GPIO.LOW)
        print(f"Solenoid {solenoid} is OFF")
    else:
        print("Invalid action! Use 'on' or 'off'.")

# Main control loop
try:
    while True:
        print("\n--- Solenoid Control ---")
        print("1. Turn Solenoid 1 ON")
        print("2. Turn Solenoid 1 OFF")
        print("3. Turn Solenoid 2 ON")
        print("4. Turn Solenoid 2 OFF")
        print("5. Exit")
        
        choice = input("Enter your choice: ")

        if choice == "1":
            control_solenoid("1", "on")
        elif choice == "2":
            control_solenoid("1", "off")
        elif choice == "3":
            control_solenoid("2", "on")
        elif choice == "4":
            control_solenoid("2", "off")
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice! Please select a valid option.")

except KeyboardInterrupt:
    print("\nProgram interrupted. Cleaning up GPIO...")
finally:
    GPIO.cleanup()
    print("GPIO cleaned up. Program exited.")
