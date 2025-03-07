import RPi.GPIO as GPIO
import time
import threading

# Define the physical pins (using BOARD numbering) for the HX711 connections.
DT_PIN = 31  # Data pin from HX711
SCK_PIN = 33  # Clock pin for HX711

# Calibration constants:
# Adjust these values for your specific scale.
calibration_factor = 1000  # Example: change this to match your scale's response (raw units per kg)
tare_offset = 0  # Global tare offset (will be set during tare)

# Setup GPIO in BOARD mode
GPIO.setmode(GPIO.BOARD)
GPIO.setup(DT_PIN, GPIO.IN)
GPIO.setup(SCK_PIN, GPIO.OUT)

def read_hx711():
    """
    Reads a 24-bit value from the HX711 and returns a signed integer.
    """
    # Wait for the chip to become ready by checking if DT is low.
    while GPIO.input(DT_PIN) == 1:
        time.sleep(0.001)

    count = 0
    # Read 24 bits of data from the HX711.
    for _ in range(24):
        GPIO.output(SCK_PIN, True)
        count = count << 1
        GPIO.output(SCK_PIN, False)
        if GPIO.input(DT_PIN):
            count += 1

    # Set the channel and gain factor for the next reading:
    # One additional clock pulse after the 24 bits will set the gain to 128.
    GPIO.output(SCK_PIN, True)
    GPIO.output(SCK_PIN, False)

    # Convert the 24-bit reading into a signed value
    if count & 0x800000:  # if the sign bit is set
        count |= ~0xffffff  # perform sign extension

    return count

def perform_tare():
    """
    Takes 10 consecutive readings and computes the average value as the tare offset.
    """
    global tare_offset
    readings = []
    print("Taring... please ensure no weight is on the scale.")
    for _ in range(10):
        reading = read_hx711()
        readings.append(reading)
        time.sleep(0.1)
    tare_offset = sum(readings) / len(readings)
    print("Tare complete. New tare offset set to:", tare_offset)

def input_listener():
    """
    Listen for user input in a separate thread.
    Typing 'tare' (and pressing Enter) will perform the tare function.
    """
    while True:
        command = input("Type 'tare' to tare the scale: ")
        if command.strip().lower() == "tare":
            perform_tare()

if __name__ == '__main__':
    # Start the input listener thread for tare functionality.
    listener_thread = threading.Thread(target=input_listener, daemon=True)
    listener_thread.start()

    print("Starting HX711 scale reading. Press Ctrl+C to exit.")
    try:
        while True:
            raw_value = read_hx711()
            # Apply the tare offset and calibration factor to calculate the weight.
            # weight (kg) = (raw_value - tare_offset) / calibration_factor
            weight_kg = (raw_value - tare_offset) / calibration_factor
            print("Raw reading: {:>10} | Weight (kg): {:.3f}".format(raw_value, weight_kg))
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        GPIO.cleanup()
