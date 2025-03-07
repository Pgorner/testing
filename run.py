import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)  # Disable warnings

# Define GPIO pins
SOLENOID_1 = 22  # GPIO 22 (Pin 15)
SOLENOID_2 = 23  # GPIO 23 (Pin 16)

# Ensure correct GPIO mode
GPIO.setmode(GPIO.BCM)

# Set as outputs
GPIO.setup(SOLENOID_1, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(SOLENOID_2, GPIO.OUT, initial=GPIO.LOW)

# Test solenoids
print("Turning Solenoid 1 ON...")
GPIO.output(SOLENOID_1, GPIO.HIGH)
time.sleep(2)

print("Turning Solenoid 1 OFF...")
GPIO.output(SOLENOID_1, GPIO.LOW)
time.sleep(2)

print("Turning Solenoid 2 ON...")
GPIO.output(SOLENOID_2, GPIO.HIGH)
time.sleep(2)

print("Turning Solenoid 2 OFF...")
GPIO.output(SOLENOID_2, GPIO.LOW)
time.sleep(2)

GPIO.cleanup()
print("Test complete. GPIO cleaned up.")
