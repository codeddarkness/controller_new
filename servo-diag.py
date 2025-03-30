#!/usr/bin/env python3

"""
Servo Controller Diagnostic Script
Use this to diagnose and fix issues with servo response
"""

import time
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('servo_diagnostic')

# Try to import hardware libraries
try:
    import Adafruit_PCA9685
    PCA9685_AVAILABLE = True
except ImportError:
    print("Warning: Adafruit_PCA9685 not found. Please install it with:")
    print("  pip3 install adafruit-pca9685")
    PCA9685_AVAILABLE = False

# Configuration Constants
SERVO_MIN = 150  # Min pulse length (0 degrees)
SERVO_MAX = 600  # Max pulse length (180 degrees)
SERVO_FREQ = 50  # PWM frequency for servos (50Hz standard)
SERVO_CHANNELS = [0, 1, 2, 3]  # Servo channels to control
I2C_BUSES = [0, 1]  # I2C buses to check

# Global variables
pca_connected = False
pca_bus = None
pwm = None

def detect_i2c_devices():
    """Detect available I2C devices and initialize PCA9685"""
    global pca_connected, pca_bus, pwm
    
    print("\n--- I2C Device Detection ---")
    
    # First, try to use i2cdetect to list all devices
    print("Checking I2C devices with i2cdetect (if available):")
    for bus_num in I2C_BUSES:
        try:
            os.system(f"i2cdetect -y {bus_num}")
        except:
            print(f"Could not run i2cdetect on bus {bus_num}")
    
    # Now try to initialize PCA9685 on each bus
    for bus_num in I2C_BUSES:
        print(f"\nTrying to initialize PCA9685 on I2C bus {bus_num}...")
        if PCA9685_AVAILABLE:
            try:
                test_pwm = Adafruit_PCA9685.PCA9685(busnum=bus_num)
                pca_connected = True
                pca_bus = bus_num
                pwm = test_pwm  # Save the working instance
                print(f"SUCCESS: PCA9685 found on I2C bus {bus_num}")
                break
            except Exception as e:
                print(f"FAILED: Could not initialize PCA9685 on bus {bus_num}: {e}")
        else:
            print("SKIPPED: Adafruit_PCA9685 library not available")
    
    if not pca_connected:
        print("\nERROR: Could not connect to PCA9685 on any I2C bus.")
        print("Please check:")
        print("1. Physical connections (SDA, SCL, VCC, GND)")
        print("2. I2C is enabled (run 'sudo raspi-config')")
        print("3. PCA9685 has power (3.3V or 5V depending on your board)")
        print("4. Try running 'sudo i2cdetect -y 1' to see if device is detected at address 0x40")
    else:
        print("\nSetting up PWM frequency...")
        try:
            pwm.set_pwm_freq(SERVO_FREQ)
            print(f"PWM frequency set to {SERVO_FREQ}Hz")
        except Exception as e:
            print(f"ERROR setting PWM frequency: {e}")
            pca_connected = False

def set_servo_position(channel, angle):
    """Set a servo to a specific angle (0-180)"""
    if not pca_connected or not pwm:
        print(f"Cannot set servo position: PCA9685 not connected")
        return False
    
    if channel not in SERVO_CHANNELS:
        print(f"Invalid channel: {channel}")
        return False
    
    # Constrain the angle
    angle = max(0, min(180, angle))
    
    # Calculate pulse length
    pulse = int(SERVO_MIN + (angle / 180.0) * (SERVO_MAX - SERVO_MIN))
    
    # Set the pulse
    try:
        print(f"Setting servo {channel} to {angle}° (pulse: {pulse})")
        pwm.set_pwm(channel, 0, pulse)
        return True
    except Exception as e:
        print(f"Error setting servo {channel}: {e}")
        return False

def test_servo_limits():
    """Test each servo by moving to min, center, and max positions"""
    if not pca_connected:
        print("Cannot test servos: PCA9685 not connected")
        return
    
    print("\n--- Servo Range Test ---")
    
    for channel in SERVO_CHANNELS:
        print(f"\nTesting Servo {channel}:")
        
        # Test minimum position (0°)
        print(f"  Moving to 0°...")
        set_servo_position(channel, 0)
        time.sleep(1)
        
        # Test center position (90°)
        print(f"  Moving to 90°...")
        set_servo_position(channel, 90)
        time.sleep(1)
        
        # Test maximum position (180°)
        print(f"  Moving to 180°...")
        set_servo_position(channel, 180)
        time.sleep(1)
        
        # Return to center
        print(f"  Returning to 90°...")
        set_servo_position(channel, 90)
        time.sleep(1)
    
    print("\nServo range test complete.")

def test_servo_smooth():
    """Test smooth movement of each servo"""
    if not pca_connected:
        print("Cannot test servos: PCA9685 not connected")
        return
    
    print("\n--- Servo Smooth Movement Test ---")
    
    for channel in SERVO_CHANNELS:
        print(f"\nTesting Servo {channel} with smooth movement:")
        
        # Move from center to max smoothly
        print(f"  Moving from 90° to 180° smoothly...")
        for angle in range(90, 181, 5):
            set_servo_position(channel, angle)
            time.sleep(0.05)
        
        # Move from max to min smoothly
        print(f"  Moving from 180° to 0° smoothly...")
        for angle in range(180, -1, -5):
            set_servo_position(channel, angle)
            time.sleep(0.05)
        
        # Move from min to center smoothly
        print(f"  Moving from 0° to 90° smoothly...")
        for angle in range(0, 91, 5):
            set_servo_position(channel, angle)
            time.sleep(0.05)
    
    print("\nServo smooth movement test complete.")

def test_all_servos_together():
    """Test moving all servos together"""
    if not pca_connected:
        print("Cannot test servos: PCA9685 not connected")
        return
    
    print("\n--- All Servos Test ---")
    
    # Move all to center
    print("Moving all servos to 90°...")
    for channel in SERVO_CHANNELS:
        set_servo_position(channel, 90)
    time.sleep(1)
    
    # Move all to minimum
    print("Moving all servos to 0°...")
    for channel in SERVO_CHANNELS:
        set_servo_position(channel, 0)
    time.sleep(1)
    
    # Move all to maximum
    print("Moving all servos to 180°...")
    for channel in SERVO_CHANNELS:
        set_servo_position(channel, 180)
    time.sleep(1)
    
    # Return all to center
    print("Returning all servos to 90°...")
    for channel in SERVO_CHANNELS:
        set_servo_position(channel, 90)
    
    print("\nAll servos test complete.")

def adjust_servo_range():
    """Adjust the servo pulse range if needed"""
    global SERVO_MIN, SERVO_MAX
    
    print("\n--- Servo Range Adjustment ---")
    print("Current servo pulse settings:")
    print(f"  SERVO_MIN: {SERVO_MIN} (0°)")
    print(f"  SERVO_MAX: {SERVO_MAX} (180°)")
    
    choice = input("\nDo you want to adjust these values? (y/n): ")
    if choice.lower() != 'y':
        return
    
    try:
        new_min = int(input("Enter new SERVO_MIN value (default: 150): ") or SERVO_MIN)
        new_max = int(input("Enter new SERVO_MAX value (default: 600): ") or SERVO_MAX)
        
        if new_min >= new_max:
            print("ERROR: SERVO_MIN must be less than SERVO_MAX")
            return
        
        SERVO_MIN = new_min
        SERVO_MAX = new_max
        
        print(f"\nServo range adjusted to:")
        print(f"  SERVO_MIN: {SERVO_MIN} (0°)")
        print(f"  SERVO_MAX: {SERVO_MAX} (180°)")
        
        # Test the new range
        print("\nTesting new range on Servo 0...")
        set_servo_position(0, 0)
        time.sleep(1)
        set_servo_position(0, 90)
        time.sleep(1)
        set_servo_position(0, 180)
        time.sleep(1)
        set_servo_position(0, 90)
        
        print(f"\nTo make these changes permanent, update SERVO_MIN and SERVO_MAX in your servo_controller.py file.")
        
    except ValueError:
        print("Invalid input. Using default values.")

def fix_permissions():
    """Check and fix permissions for /dev/i2c devices"""
    print("\n--- I2C Permissions Check ---")
    
    for bus_num in I2C_BUSES:
        bus_path = f"/dev/i2c-{bus_num}"
        
        if os.path.exists(bus_path):
            # Check current permissions
            try:
                perms = os.stat(bus_path)
                print(f"Bus {bus_num} ({bus_path}):")
                print(f"  Owner: {perms.st_uid}")
                print(f"  Group: {perms.st_gid}")
                print(f"  Permissions: {oct(perms.st_mode)[-3:]}")
                
                # Check if current user has access
                if os.access(bus_path, os.R_OK | os.W_OK):
                    print(f"  Status: Current user has read/write access")
                else:
                    print(f"  Status: Current user DOES NOT have read/write access")
                    print(f"  Fix: Run 'sudo usermod -aG i2c $USER' and then log out and back in")
                    
                    # Offer to fix
                    if os.geteuid() == 0:  # Check if running as root
                        fix = input("\nFix permissions now? (y/n): ")
                        if fix.lower() == 'y':
                            os.system(f"chmod 666 {bus_path}")
                            print(f"  Applied permissions fix for {bus_path}")
                    else:
                        print(f"  To fix immediately, run 'sudo chmod 666 {bus_path}'")
            
            except Exception as e:
                print(f"Error checking bus {bus_num}: {e}")
        else:
            print(f"Bus {bus_num} ({bus_path}) does not exist")

def restart_i2c():
    """Restart I2C service"""
    print("\n--- I2C Restart ---")
    
    if os.geteuid() != 0:  # Not running as root
        print("This operation requires sudo privileges.")
        print("To restart I2C, run the following commands:")
        print("  sudo rmmod i2c_bcm2708")
        print("  sudo modprobe i2c_bcm2708")
        return
    
    try:
        print("Unloading I2C module...")
        os.system("rmmod i2c_bcm2708")
        time.sleep(1)
        print("Loading I2C module...")
        os.system("modprobe i2c_bcm2708")
        print("I2C service restarted.")
    except Exception as e:
        print(f"Error restarting I2C: {e}")

def main_menu():
    """Display main menu and handle user selection"""
    while True:
        print("\n======================================")
        print("     Servo Controller Diagnostic     ")
        print("======================================")
        print("1. Detect I2C Devices")
        print("2. Test Servo Range (0° - 90° - 180°)")
        print("3. Test Servo Smooth Movement")
        print("4. Test All Servos Together")
        print("5. Adjust Servo Pulse Range")
        print("6. Check I2C Permissions")
        print("7. Restart I2C Service (requires sudo)")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-7): ")
        
        if choice == '1':
            detect_i2c_devices()
        elif choice == '2':
            test_servo_limits()
        elif choice == '3':
            test_servo_smooth()
        elif choice == '4':
            test_all_servos_together()
        elif choice == '5':
            adjust_servo_range()
        elif choice == '6':
            fix_permissions()
        elif choice == '7':
            restart_i2c()
        elif choice == '0':
            print("\nExiting diagnostic tool. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    print("Welcome to the Servo Controller Diagnostic Tool")
    print("This tool will help diagnose and fix issues with servo response")
    
    # Initial device detection
    detect_i2c_devices()
    
    # Show menu
    main_menu()

