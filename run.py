import RPi.GPIO as GPIO
import time

# Define the physical pins (using BOARD numbering) for the HX711 connections.
DT_PIN = 31  # Data pin from HX711
SCK_PIN = 33  # Clock pin for HX711

# Calibration constants:
calibration_factor = 1000  # Adjust this factor to match your scale's response (raw units per kg)
tare_offset = 0  # Global tare offset (will be updated during tare)

# Setup GPIO in BOARD mode
GPIO.setmode(GPIO.BOARD)
GPIO.setup(DT_PIN, GPIO.IN)
GPIO.setup(SCK_PIN, GPIO.OUT)

def read_hx711():
    """
    Reads a 24-bit value from the HX711 and returns a signed integer.
    """
    # Wait for HX711 to become ready (DT goes low)
    while GPIO.input(DT_PIN) == 1:
        time.sleep(0.001)

    count = 0
    # Read 24 bits from HX711
    for _ in range(24):
        GPIO.output(SCK_PIN, True)
        count = count << 1
        GPIO.output(SCK_PIN, False)
        if GPIO.input(DT_PIN):
            count += 1

    # Set the gain to 128 for the next reading by pulsing SCK once more
    GPIO.output(SCK_PIN, True)
    GPIO.output(SCK_PIN, False)

    # Convert the 24-bit reading to a signed value
    if count & 0x800000:  # if sign bit is set
        count |= ~0xffffff  # sign extension
    return count

def perform_tare():
    """
    Takes 10 consecutive readings to compute an average value as the tare offset.
    Displays 'Appearing ...' while taring.
    """
    global tare_offset
    print("Appearing ...")
    readings = []
    for _ in range(10):
        reading = read_hx711()
        readings.append(reading)
        time.sleep(0.1)
    tare_offset = sum(readings) / len(readings)
    print("Tare complete. New tare offset set to:", tare_offset)

def read_weight():
    """
    Reads the weight 3 times with a 1-second delay between each reading and prints the result.
    """
    for i in range(3):
        raw_value = read_hx711()
        # Calculate weight (kg) using the tare offset and calibration factor.
        weight_kg = (raw_value - tare_offset) / calibration_factor
        print(f"Reading {i+1}: Weight (kg): {weight_kg:.3f}")
        time.sleep(1)

def main_menu():
    while True:
        print("\nSelect an option:")
        print("1: Tare the scale")
        print("2: Read the weight 3 times")
        print("q: Quit")
        choice = input("Enter your choice: ").strip().lower()
        if choice == '1':
            perform_tare()
        elif choice == '2':
            read_weight()
        elif choice == 'q':
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == '__main__':
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        GPIO.cleanup()
