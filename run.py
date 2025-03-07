import RPi.GPIO as GPIO
import time
import sys, select, tty, termios

# Define the physical pins (using BOARD numbering) for the HX711 connections.
DT_PIN = 31  # Data pin from HX711
SCK_PIN = 33  # Clock pin for HX711

# Global calibration variables; adjust these via calibration
calibration_factor = 25921.726190476194  # Initial calibration factor (raw units per kg)
tare_offset = 0  # Tare offset

# Setup GPIO in BOARD mode
GPIO.setmode(GPIO.BOARD)
GPIO.setup(DT_PIN, GPIO.IN)
GPIO.setup(SCK_PIN, GPIO.OUT)

#########################################
#  Simple 1D Kalman Filter Implementation
#########################################
class KalmanFilter:
    def __init__(self, initial_value=0.0, process_variance=1e-2, measurement_variance=1e-3):
        self.x = initial_value  # state estimate
        self.P = 1.0            # estimation error covariance
        self.Q = process_variance  # process variance (increased for faster response)
        self.R = measurement_variance  # measurement variance (decreased to trust measurements more)

    def update(self, measurement):
        # Prediction update
        self.P += self.Q
        # Measurement update
        K = self.P / (self.P + self.R)
        self.x = self.x + K * (measurement - self.x)
        self.P = (1 - K) * self.P
        return self.x

#########################################
#  HX711 Reading Functions
#########################################
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
    and returns their average.
    """
    readings = []
    for _ in range(num_readings):
        readings.append(read_hx711())
        time.sleep(delay)
    return sum(readings) / len(readings)

def get_filtered_reading(num_readings=5, delay=0.005):
    """
    Takes multiple readings, sorts them, and returns the median.
    This helps mitigate outlier effects.
    """
    readings = []
    for _ in range(num_readings):
        readings.append(read_hx711())
        time.sleep(delay)
    readings.sort()
    median = readings[len(readings)//2]
    return median

#########################################
#  Scale Functions: Tare, Calibration, and Readings
#########################################
def perform_tare():
    """
    Tares the scale by averaging multiple readings with no load.
    """
    global tare_offset
    print("Taring... Ensure no load is on the scale.")
    tare_offset = get_average_reading(num_readings=10, delay=0.005)
    print("Tare complete. Tare offset set to:", tare_offset)

def read_weight():
    """
    Takes three weight readings (each as a median over a set of samples)
    and prints the weight in kilograms.
    """
    for i in range(3):
        filtered_reading = get_filtered_reading(num_readings=5, delay=0.005)
        weight_kg = (filtered_reading - tare_offset) / calibration_factor
        print("Reading {}: Weight (kg): {:.3f}".format(i+1, weight_kg))
        time.sleep(1)

def calibrate_scale():
    """
    Calibrates the scale by taking readings with a known weight.
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

#########################################
#  Continuous Display with Kalman Filter
#########################################
def continuous_weight():
    """
    Continuously displays the weight using a median filter followed by a Kalman filter
    to improve accuracy over time. Press SPACE to stop the display.
    """
    print("Displaying continuous weight with Kalman filter. Press SPACE to stop.")
    # Set up the Kalman filter with new parameters for faster adaptation.
    kalman = KalmanFilter(initial_value=0.0, process_variance=1e-2, measurement_variance=1e-3)
    
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
            # Use the median of 5 readings for filtering out outliers.
            filtered_reading = get_filtered_reading(num_readings=5, delay=0.005)
            # Convert raw reading to weight in kg
            weight_measurement = (filtered_reading - tare_offset) / calibration_factor
            # Update the Kalman filter with the new measurement for a faster response.
            weight_estimate = kalman.update(weight_measurement)
            sys.stdout.write("\rWeight (kg): {:.3f}".format(weight_estimate))
            sys.stdout.flush()
            time.sleep(0.01)
        print()
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

#########################################
#  Main Menu
#########################################
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
