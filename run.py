import RPi.GPIO as GPIO
import time
import sys, select, tty, termios

# Define the physical pins (using BOARD numbering) for the HX711 connections.
DT_PIN = 31  # Data pin from HX711
SCK_PIN = 33  # Clock pin for HX711

# Global calibration variables; adjust these via calibration
calibration_factor = 1000  # Initial calibration factor (raw units per kg)
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
    Reads 24 bits from the HX711 and returns a signed integer.
    If the HX711 does not become ready within 1 second, it resets the module.
    """
    timeout = 1.0  # seconds
    start_time = time.time()
    while GPIO.input(DT_PIN) == 1:
        if (time.time() - start_time) > timeout:
            print("Timeout waiting for HX711. Resetting module...")
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

    # One extra pulse sets gain to 128 (Channel A)
    GPIO.output(SCK_PIN, True)
    GPIO.output(SCK_PIN, False)

    # Convert to signed 24-bit integer
    if count & 0x800000:
        count |= ~0xffffff
    return count

def get_average_reading(num_readings=3, delay=0.005):
    """
    Takes a specified number of readings with a short delay between them
    and returns their average. Using a small window allows for faster updates.
    """
    readings = []
    for _ in range(num_readings):
        readings.append(read_hx711())
        time.sleep(delay)
    return sum(readings) / len(readings)

def perform_tare():
    """
    Tares the scale by averaging multiple readings with no load.
    """
    global tare_offset
    print("Taring... Ensure no load is on the scale.")
    # For tare, use 10 readings with a short delay
    tare_offset = get_average_reading(num_readings=10, delay=0.005)
    print("Tare complete. Tare offset set to:", tare_offset)

def read_weight():
    """
    Takes three weight readings (each as an average over 3 samples)
    and prints the weight in kilograms.
    """
    for i in range(3):
        avg_reading = get_average_reading(num_readings=3, delay=0.005)
        weight_kg = (avg_reading - tare_offset) / calibration_factor
        print("Reading {}: Weight (kg): {:.3f}".format(i+1, weight_kg))
        time.sleep(1)

def calibrate_scale():
    """
    Calibrates the scale by taking readings with a known weight.
    The user is prompted to tare the scale, then to place a known weight.
    The calibration factor is calculated as:
        calibration_factor = (average_with_load - tare_offset) / known_weight
    """
    global calibration_factor
    input("Remove any weight and press Enter to perform tare.")
    perform_tare()
    input("Place a known weight on the scale and press Enter when ready...")
    avg_with_load = get_average_reading(num_readings=10, delay=0.005)
    try:
        known_weight = float(input("Enter the known weight in kg: "))
    except ValueError:
        print("Invalid input. Calibration aborted.")
        return
    if known_weight <= 0:
        print("Weight must be positive. Calibration aborted.")
        return
    calibration_factor = (avg_with_load - tare_offset) / known_weight
    print("Calibration complete. New calibration factor set to:", calibration_factor)

def continuous_weight():
    """
    Continuously displays the weight using a moving average filter over a small window.
    The display updates fast, and pressing SPACE stops the continuous mode.
    """
    print("Displaying continuous weight. Press SPACE to stop.")
    # Configure terminal for nonblocking character reads.
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())
    try:
        while True:
            # Check if SPACE was pressed to stop
            if select.select([sys.stdin], [], [], 0)[0]:
                ch = sys.stdin.read(1)
                if ch == ' ':
                    print("\nStopping continuous display.")
                    break
            avg_reading = get_average_reading(num_readings=3, delay=0.005)
            weight_kg = (avg_reading - tare_offset) / calibration_factor
            sys.stdout.write("\rWeight (kg): {:.3f}".format(weight_kg))
            sys.stdout.flush()
            # A short sleep helps to prevent flooding the terminal.
            time.sleep(0.01)
        print()
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def main_menu():
    while True:
        print("\nSelect an option:")
        print("1: Tare the scale")
        print("2: Display continuous weight")
        print("3: Calibrate the scale")
        print("q: Quit")
        choice = input("Enter your choice: ").strip().lower()
        if choice == '1':
            perform_tare()
        elif choice == '2':
            continuous_weight()
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
