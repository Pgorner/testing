import RPi.GPIO as GPIO
import time

SOLENOID_1 = 38  # GPIO 28
SOLENOID_2 = 40  # GPIO 29

GPIO.setmode(GPIO.BCM)
GPIO.setup(SOLENOID_1, GPIO.OUT)
GPIO.setup(SOLENOID_2, GPIO.OUT)

print("Turning Solenoid 1 ON...")
GPIO.output(SOLENOID_1, GPIO.HIGH)
time.sleep(5)

print("Turning Solenoid 1 OFF...")
GPIO.output(SOLENOID_1, GPIO.LOW)
time.sleep(5)

print("Turning Solenoid 2 ON...")
GPIO.output(SOLENOID_2, GPIO.HIGH)
time.sleep(5)

print("Turning Solenoid 2 OFF...")
GPIO.output(SOLENOID_2, GPIO.LOW)
time.sleep(5)

GPIO.cleanup()
print("Test complete.")
