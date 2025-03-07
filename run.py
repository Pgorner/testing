import RPi.GPIO as GPIO
import time

# Define the physical pins (using BOARD numbering) for the HX711 connections.
DT_PIN = 31  # Data pin from HX711
SCK_PIN = 33  # Clock pin for HX711

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
    for i in range(24):
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

if __name__ == '__main__':
    try:
        print("Starting HX711 scale reading. Press Ctrl+C to exit.")
        while True:
            raw_value = read_hx711()
            # Here you can apply a calibration factor to convert raw_value to kg.
            # For example: weight_kg = (raw_value - offset) / calibration_factor
            print("Raw HX711 reading:", raw_value)
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        GPIO.cleanup()
