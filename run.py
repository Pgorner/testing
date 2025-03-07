import RPi.GPIO as GPIO
import time

# Define the physical pins (using BOARD numbering) for the HX711 connections.
DT_PIN = 31  # Data pin from HX711
SCK_PIN = 33  # Clock pin for HX711

# Global variables for calibration and tare
calibration_factor = 1000  # Initial value; will be updated by calibration
tare_offset = 0  # Tare offset

# Setup GPIO in BOARD mode
GPIO.setmode(GPIO.BOARD)
GPIO.setup(DT_PIN, GPIO.IN)
GPIO.setup(SCK_PIN, GPIO.OUT)

def reset_hx711():
    """Resets the HX711 by pulsing the clock pin."""
    GPIO.output(SCK_PIN, True)
    time.sleep(0.0001)
    GPIO.output(SCK_PIN, False)

def read_hx711():
    """
    Reads a 24-bit value from the HX711 and returns a signed integer.
    If the HX711 is not ready within 1 second, it resets the module.
    """
    timeout = 1.0  # seconds
    start_time = time.time()
    # Wait for HX711 to become ready (DT goes low)
    while GPIO.input(DT_PIN) == 1:
        if (time.time() - start_time) > timeout:
            print("Timeout waiting for HX711. Resetting the module...")
            reset_hx711()
            start_time = time.time()
        time.sleep(0.001)

    count = 0
    for _ in range(24):
        GPIO.output(SCK_PIN, True)
        count = count << 1
        GPIO.output(SCK_PIN, False)
        if GPIO.input(DT_PIN):
            count += 1

    # One extra pulse sets the gain to 128 for the next reading.
    GPIO.output(SCK_PIN, True)
    GPIO.output(SCK_PIN, False)

    # Convert to signed 24-bit value
    if count & 0x800000:
        count |= ~0xffffff
    return count

def get_average_reading(num_readings=10, delay=0.1):
    """
    Takes multiple readings and returns their average.
    """
    readings = []
    for _ in range(num_readings):
        reading = read_hx711()
        readings.append(reading)
        time.sleep(delay)
    return sum(readings) / len(readings)

def perform_tare():
    """
    Tares the scale by averaging multiple readings with no load.
    """
    global tare_offset
    print("Appearing ...")
    tare_offset = get_average_reading(num_readings=10, delay=0.1)
    print("Tare complete. New tare offset set to:", tare_offset)

def read_weight():
    """
    Reads the weight by averaging multiple readings and prints the weight in kg.
    Repeats the process 3 times with a 1-second pause between each.
    """
    for i in range(3):
        avg_reading = get_average_reading(num_readings=10, delay=0.1)
        weight_kg = (avg_reading - tare_offset) / calibration_factor
        print(f"Reading {i+1}: Weight (kg): {weight_kg:.3f}")
        time.sleep(1)

def calibrate_scale():
    """
    Calibrates the scale by taking readings with a known weight.
    The user must first perform a tare, then place a known weight on the scale.
    The calibration factor is computed as:
        (average_with_load - tare_offset) / known_weight
    """
    global calibration_factor
    input("Remove any weight and press Enter to perform tare.")
    perform_tare()
    input("Place a known weight on the scale and press Enter when ready...")
    average_with_load = get_average_reading(num_readings=10, delay=0.1)
    try:
        known_weight = float(input("Enter the known weight in kg: "))
    except ValueError:
        print("Invalid input. Calibration aborted.")
        return
    if known_weight <= 0:
        print("Weight must be positive. Calibration aborted.")
        return
    calibration_factor = (average_with_load - tare_offset) / known_weight
    print("Calibration complete.")
    print("New calibration factor set to:", calibration_factor)

def main_menu():
    while True:
        print("\nSelect an option:")
        print("1: Tare the scale")
        print("2: Read the weight 3 times")
        print("3: Calibrate the scale")
        print("q: Quit")
        choice = input("Enter your choice: ").strip().lower()
        if choice == '1':
            perform_tare()
        elif choice == '2':
            read_weight()
        elif choice == '3':
            calibrate_scale()
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
