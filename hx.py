#!/usr/bin/env python3
# import RPi.GPIO as GPIO
import time

# --- Hardware Imports ---
try:
    import RPi.GPIO as GPIO
    from hx711 import HX711
except ImportError:
    GPIO = None
    class HX711:
        def __init__(self, dout_pin, pd_sck_pin):
            self.dout_pin = dout_pin
            self.pd_sck_pin = pd_sck_pin
        def reset(self):
            pass
        def get_weight(self, times=5):
            return 0
        def power_down(self):
            pass
        def power_up(self):
            pass

# --- HX711 Pin Definitions (using BOARD numbering) ---
DT_PIN = 31   # Data pin from HX711
SCK_PIN = 33  # Clock (PD_SCK) pin for HX711

# --- Global Calibration Variables ---
# These variables are meant to be updated via tare and calibration procedures.
CALIBRATION_FACTOR =25921.726190476194  # Default raw units per gram (adjust via calibration)
tare_offset = -85791.3  # Tare offset

# --- GPIO Setup ---
GPIO.setmode(GPIO.BOARD)
GPIO.setup(DT_PIN, GPIO.IN)
GPIO.setup(SCK_PIN, GPIO.OUT)
GPIO.output(SCK_PIN, False)  # Ensure clock is low

def reset():
    """Resets the HX711 by pulsing the clock pin."""
    GPIO.output(SCK_PIN, True)
    time.sleep(0.0001)
    GPIO.output(SCK_PIN, False)

def read_raw():
    """
    Reads 24 bits from the HX711 and returns a signed integer.
    If the device does not become ready within one second, it resets the module.
    """
    timeout = 1.0  # seconds
    start_time = time.time()
    while GPIO.input(DT_PIN) == 1:
        if time.time() - start_time > timeout:
            reset()
            start_time = time.time()
        time.sleep(0.001)
    
    count = 0
    for _ in range(24):
        GPIO.output(SCK_PIN, True)
        count = count << 1
        GPIO.output(SCK_PIN, False)
        if GPIO.input(DT_PIN):
            count += 1

    # One extra pulse to set gain for next reading (Channel A, Gain=128)
    GPIO.output(SCK_PIN, True)
    GPIO.output(SCK_PIN, False)

    # Convert from 24-bit two's complement
    if count & 0x800000:
        count |= ~0xffffff
    return count

def get_filtered_reading(num_readings=5, delay=0.005):
    """
    Takes a number of consecutive raw readings, sorts them, and returns the median.
    This helps reduce the effect of sporadic outliers.
    """
    readings = []
    for _ in range(num_readings):
        readings.append(read_raw())
        time.sleep(delay)
    readings.sort()
    return readings[len(readings)//2]

def get_weight(num_readings=5):
    """
    Returns the current weight as a raw measurement minus the tare offset.
    The calling code should convert this value into grams (or ml) by dividing
    by CALIBRATION_FACTOR.
    """
    global tare_offset
    raw = get_filtered_reading(num_readings=num_readings)
    return raw - tare_offset

def tare(num_readings=10, delay=0.005):
    """
    Performs a tare (zero) calibration.
    Takes several readings with no load and computes the average raw value.
    This value is stored as tare_offset.
    Returns the computed tare offset.
    """
    global tare_offset
    total = 0
    for _ in range(num_readings):
        total += read_raw()
        time.sleep(delay)
    tare_offset = total / num_readings
    return tare_offset

def calibrate(known_weight, num_readings=10, delay=0.005):
    """
    Calibrates the scale using a known weight.
    The calibration factor is computed as:
       (average_with_load - tare_offset) / known_weight
    known_weight is in grams.
    Returns the new calibration factor.
    """
    global CALIBRATION_FACTOR, tare_offset
    total = 0
    for _ in range(num_readings):
        total += read_raw()
        time.sleep(delay)
    avg_with_load = total / num_readings
    # Update calibration factor based on known weight (in grams)
    CALIBRATION_FACTOR = (avg_with_load - tare_offset) / known_weight
    return CALIBRATION_FACTOR

def power_down():
    """
    Powers down the HX711.
    To do this, set PD_SCK (SCK_PIN) high for at least 60µs.
    """
    GPIO.output(SCK_PIN, True)
    time.sleep(0.0001)  # 100µs is sufficient

def power_up():
    """
    Powers up the HX711.
    Simply set PD_SCK (SCK_PIN) low and allow time for the chip to settle.
    """
    GPIO.output(SCK_PIN, False)
    time.sleep(0.1)

def cleanup():
    """
    Cleans up the GPIO. Call this when your application is exiting.
    """
    GPIO.cleanup()

# Optionally, you can add additional helper functions here (e.g. continuous display)
if __name__ == '__main__':
    # For testing: perform a tare, then print continuous weight readings.
    try:
        print("Performing tare...")
        t = tare()
        print("Tare offset =", t)
        print("Displaying continuous weight (raw units):")
        while True:
            weight = get_weight() / CALIBRATION_FACTOR
            print("Weight: {:.3f}".format(weight))
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()
