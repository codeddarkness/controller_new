#!/usr/bin/env python3

"""
PS3 Controller Servo Diagnostic Tool
This script tests servo functionality with a PCA9685 controller and PS3 gamepad,
providing step-by-step diagnostics to identify common issues.
"""

import time
import sys
import os
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("servo_diagnostic.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("servo_diagnostic")

# Try to import required libraries
try:
    import Adafruit_PCA9685
    PCA9685_AVAILABLE = True
    logger.info("PCA9685 library loaded successfully")
except ImportError:
    logger.error("Adafruit_PCA9685 library not found. Please install it with: pip install adafruit-pca9685")
    PCA9685_AVAILABLE = False

try:
    import evdev
    from evdev import InputDevice, ecodes
    EVDEV_AVAILABLE = True
    logger.info("Evdev library loaded successfully")
except ImportError:
    logger.error("Evdev library not found. Please install it with: pip install evdev")
    EVDEV_AVAILABLE = False

# Configuration Constants
SERVO_MIN = 150  # Min pulse length (0 degrees)
SERVO_MAX = 600  # Max pulse length (180 degrees)
SERVO_FREQ = 50  # PWM frequency for servos (50Hz standard)
SERVO_CHANNELS = [0, 1, 2, 3]  # Servo channels to control
I2C_BUS = 1  # I2C bus to use (based on your logs showing bus 1 works)

# Global variables
pwm = None
pca_connected = False
gamepad = None
controller_connected = False
exit_flag = False

# PS3 controller button mappings from your debug log
PS3_BUTTON_MAPPINGS = {
    # D-pad buttons
    300: "D-Pad Up",
    301: "D-Pad Right",
    302: "D-Pad Down",
    303: "D-Pad Left",
    
    # Face buttons
    304: "Cross (✕)",
    305: "Circle (○)",
    307: "Triangle (△)",
    308: "Square (□)",
    
    # Shoulder buttons
    294: "L1",
    295: "R1",
    298: "L2",
    299: "R2",
    
    # Other buttons
    288: "Select",
    291: "Start",
    292: "PS Button",
    293: "Unknown (293)",
    296: "L3",
    297: "R3"
}

def detect_pca9685():
    """Detect and initialize PCA9685 servo controller"""
    global pca_connected, pwm
    
    logger.info("Checking for PCA9685 on I2C bus %d", I2C_BUS)
    
    if not PCA9685_AVAILABLE:
        logger.error("PCA9685 library not available. Cannot detect hardware.")
        return False
    
    try:
        # Try to initialize the device
        pwm = Adafruit_PCA9685.PCA9685(busnum=I2C_BUS)
        pwm.set_pwm_freq(SERVO_FREQ)
        
        # Test by sending a reset signal to all channels
        for channel in SERVO_CHANNELS:
            pwm.set_pwm(channel, 0, 0)
        
        logger.info("PCA9685 successfully detected and initialized on bus %d", I2C_BUS)
        pca_connected = True
        return True
    except Exception as e:
        logger.error("Failed to initialize PCA9685: %s", str(e))
        pca_connected = False
        return False

def find_controller():
    """Find and initialize PS3 controller"""
    global controller_connected, gamepad
    
    if not EVDEV_AVAILABLE:
        logger.error("Evdev library not available. Cannot detect controller.")
        return None
    
    logger.info("Searching for PS3 controller...")
    
    try:
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            logger.info("Found device: %s at %s", device.name, device.path)
            
            if 'PLAYSTATION(R)3' in device.name or 'Playstation' in device.name.lower() or 'PS3' in device.name:
                logger.info("PS3 controller found: %s", device.name)
                gamepad = device
                controller_connected = True
                return device
        
        logger.warning("No PS3 controller found. Available devices:")
        for i, device in enumerate(devices):
            logger.warning("  %d. %s", i+1, device.name)
        
        if devices:
            # Ask if user wants to use another device
            device_num = input("\nNo PS3 controller found. Enter device number to use or 0 to exit: ")
            try:
                device_idx = int(device_num) - 1
                if 0 <= device_idx < len(devices):
                    gamepad = devices[device_idx]
                    controller_connected = True
                    logger.info("Using device: %s", gamepad.name)
                    return gamepad
            except ValueError:
                pass
        
        logger.error("No suitable controller found.")
        return None
    except Exception as e:
        logger.error("Error finding controller: %s", str(e))
        return None

def set_servo_position(channel, angle):
    """Set servo to a specific angle (0-180 degrees)"""
    if not pca_connected or pwm is None:
        logger.error("Cannot set servo position: PCA9685 not connected")
        return False
    
    if channel not in SERVO_CHANNELS:
        logger.error("Invalid servo channel: %d", channel)
        return False
    
    # Constrain angle to 0-180 degrees
    angle = max(0, min(180, angle))
    
    # Calculate pulse length
    pulse = int(SERVO_MIN + (angle / 180.0) * (SERVO_MAX - SERVO_MIN))
    
    try:
        logger.info("Setting servo %d to %d° (pulse: %d)", channel, angle, pulse)
        pwm.set_pwm(channel, 0, pulse)
        return True
    except Exception as e:
        logger.error("Error setting servo %d: %s", channel, str(e))
        return False

def test_all_servos():
    """Test all servos with a standard movement pattern"""
    if not pca_connected:
        logger.error("Cannot test servos: PCA9685 not connected")
        return

    logger.info("\n--- Testing All Servos ---")
    
    # First, center all servos
    logger.info("Moving all servos to center position (90°)")
    for channel in SERVO_CHANNELS:
        set_servo_position(channel, 90)
    time.sleep(1)
    
    # Test each servo individually
    for channel in SERVO_CHANNELS:
        logger.info("Testing servo %d...", channel)
        
        # Move to minimum position
        logger.info("  Moving to 0°...")
        set_servo_position(channel, 0)
        time.sleep(1)
        
        # Move to maximum position
        logger.info("  Moving to 180°...")
        set_servo_position(channel, 180)
        time.sleep(1)
        
        # Return to center
        logger.info("  Returning to 90°...")
        set_servo_position(channel, 90)
        time.sleep(1)
    
    logger.info("Servo test complete.")

def test_servo_range(channel, min_angle=0, max_angle=180):
    """Test a specific servo's range of motion"""
    if not pca_connected:
        logger.error("Cannot test servo: PCA9685 not connected")
        return

    if channel not in SERVO_CHANNELS:
        logger.error("Invalid servo channel: %d", channel)
        return
    
    logger.info("Testing range of motion for servo %d", channel)
    
    # First center the servo
    set_servo_position(channel, 90)
    time.sleep(1)
    
    # Test minimum position
    set_servo_position(channel, min_angle)
    time.sleep(1)
    
    # Test maximum position
    set_servo_position(channel, max_angle)
    time.sleep(1)
    
    # Return to center
    set_servo_position(channel, 90)
    time.sleep(1)
    
    logger.info("Range test complete for servo %d", channel)

def test_servo_sweep(channel, delay=0.01):
    """Perform a smooth sweep test on a specific servo"""
    if not pca_connected:
        logger.error("Cannot test servo: PCA9685 not connected")
        return

    if channel not in SERVO_CHANNELS:
        logger.error("Invalid servo channel: %d", channel)
        return
    
    logger.info("Performing smooth sweep test for servo %d", channel)
    
    # Sweep from 0 to 180 degrees
    logger.info("  Sweeping from 0° to 180°...")
    for angle in range(0, 181, 5):
        set_servo_position(channel, angle)
        time.sleep(delay)
    
    # Sweep from 180 to 0 degrees
    logger.info("  Sweeping from 180° to 0°...")
    for angle in range(180, -1, -5):
        set_servo_position(channel, angle)
        time.sleep(delay)
    
    # Return to center
    set_servo_position(channel, 90)
    logger.info("Sweep test complete for servo %d", channel)

def run_controller_servo_test(gamepad):
    """Test servo control using the PS3 controller"""
    if not pca_connected or not controller_connected:
        logger.error("Both PCA9685 and controller must be connected for this test.")
        return
    
    logger.info("\n--- Controller-Servo Test ---")
    logger.info("Press buttons to control servos:")
    logger.info("  D-pad Up:    All servos to 90°")
    logger.info("  D-pad Left:  All servos to 0°")
    logger.info("  D-pad Right: All servos to 180°")
    logger.info("  X (Cross):   Toggle lock state for servo 0")
    logger.info("  Circle:      Toggle lock state for servo 1")
    logger.info("  Square:      Toggle lock state for servo 2")
    logger.info("  Triangle:    Toggle lock state for servo 3")
    logger.info("  L1/R1:       Decrease/Increase speed")
    logger.info("  L2/R2:       All servos to 0°/180°")
    logger.info("Use left/right stick to control servos.")
    logger.info("Press PS button to exit test.")
    
    # Track lock states for servos
    lock_states = {0: False, 1: False, 2: False, 3: False}
    global_lock = False
    
    # Initial center position
    for channel in SERVO_CHANNELS:
        set_servo_position(channel, 90)
    
    try:
        # Enter event loop
        for event in gamepad.read_loop():
            if event.type == ecodes.EV_KEY and event.value == 1:  # Button pressed
                button_name = PS3_BUTTON_MAPPINGS.get(event.code, f"Unknown ({event.code})")
                logger.info("Button pressed: %s (Code: %d)", button_name, event.code)
                
                # Process button press
                if event.code == 300:  # D-pad Up
                    logger.info("Moving all servos to 90°")
                    for ch in SERVO_CHANNELS:
                        if not lock_states[ch] and not global_lock:
                            set_servo_position(ch, 90)
                
                elif event.code == 303:  # D-pad Left
                    logger.info("Moving all servos to 0°")
                    for ch in SERVO_CHANNELS:
                        if not lock_states[ch] and not global_lock:
                            set_servo_position(ch, 0)
                
                elif event.code == 301:  # D-pad Right
                    logger.info("Moving all servos to 180°")
                    for ch in SERVO_CHANNELS:
                        if not lock_states[ch] and not global_lock:
                            set_servo_position(ch, 180)
                
                elif event.code == 302:  # D-pad Down
                    global_lock = not global_lock
                    logger.info("Global lock %s", "enabled" if global_lock else "disabled")
                
                elif event.code == 304:  # Cross (✕)
                    lock_states[0] = not lock_states[0]
                    logger.info("Servo 0 lock %s", "enabled" if lock_states[0] else "disabled")
                
                elif event.code == 305:  # Circle (○)
                    lock_states[1] = not lock_states[1]
                    logger.info("Servo 1 lock %s", "enabled" if lock_states[1] else "disabled")
                
                elif event.code == 308:  # Square (□)
                    lock_states[2] = not lock_states[2]
                    logger.info("Servo 2 lock %s", "enabled" if lock_states[2] else "disabled")
                
                elif event.code == 307:  # Triangle (△)
                    lock_states[3] = not lock_states[3]
                    logger.info("Servo 3 lock %s", "enabled" if lock_states[3] else "disabled")
                
                elif event.code == 298:  # L2
                    logger.info("Moving all servos to 0°")
                    for ch in SERVO_CHANNELS:
                        if not lock_states[ch] and not global_lock:
                            set_servo_position(ch, 0)
                
                elif event.code == 299:  # R2
                    logger.info("Moving all servos to 180°")
                    for ch in SERVO_CHANNELS:
                        if not lock_states[ch] and not global_lock:
                            set_servo_position(ch, 180)
                
                elif event.code == 292:  # PS Button
                    logger.info("Exiting controller test.")
                    break
            
            # Handle joystick movements
            elif event.type == ecodes.EV_ABS:
                # Map joystick values to servo positions
                if event.code == 0:  # Left Stick X
                    if not lock_states[0] and not global_lock and abs(event.value) > 5000:
                        angle = int(((event.value + 32767) / 65534) * 180)
                        set_servo_position(0, angle)
                        logger.debug("Servo 0: %d° (Left Stick X: %d)", angle, event.value)
                
                elif event.code == 1:  # Left Stick Y
                    if not lock_states[1] and not global_lock and abs(event.value) > 5000:
                        angle = int(((event.value + 32767) / 65534) * 180)
                        set_servo_position(1, angle)
                        logger.debug("Servo 1: %d° (Left Stick Y: %d)", angle, event.value)
                
                elif event.code == 2:  # Right Stick X (PS3-Z)
                    if not lock_states[2] and not global_lock and abs(event.value) > 5000:
                        angle = int(((event.value + 32767) / 65534) * 180)
                        set_servo_position(2, angle)
                        logger.debug("Servo 2: %d° (Right Stick X: %d)", angle, event.value)
                
                elif event.code == 3:  # Right Stick Y (PS3-RX)
                    if not lock_states[3] and not global_lock and abs(event.value) > 5000:
                        angle = int(((event.value + 32767) / 65534) * 180)
                        set_servo_position(3, angle)
                        logger.debug("Servo 3: %d° (Right Stick Y: %d)", angle, event.value)
    
    except KeyboardInterrupt:
        logger.info("Controller test interrupted.")
    except Exception as e:
        logger.error("Error in controller test: %s", str(e))
    
    # Reset servos to center position
    for channel in SERVO_CHANNELS:
        set_servo_position(channel, 90)

def test_servo_direct():
    """Manually test servos by entering angles directly"""
    if not pca_connected:
        logger.error("Cannot test servos: PCA9685 not connected")
        return

    logger.info("\n--- Direct Servo Control Test ---")
    logger.info("Enter servo channel (0-3) and angle (0-180), or 'q' to quit.")
    logger.info("Examples: '0 90' for servo 0 at 90°, '1 0' for servo 1 at 0°")
    
    while True:
        command = input("\nEnter command: ")
        
        if command.lower() == 'q':
            break
        
        try:
            parts = command.split()
            if len(parts) != 2:
                logger.warning("Invalid command format. Use 'channel angle', e.g., '0 90'")
                continue
            
            channel = int(parts[0])
            angle = int(parts[1])
            
            if channel not in SERVO_CHANNELS:
                logger.warning("Invalid channel. Use 0-3.")
                continue
            
            if angle < 0 or angle > 180:
                logger.warning("Invalid angle. Use 0-180.")
                continue
            
            set_servo_position(channel, angle)
            logger.info("Servo %d set to %d°", channel, angle)
            
        except ValueError:
            logger.warning("Invalid input. Use numbers for channel and angle.")
        except Exception as e:
            logger.error("Error: %s", str(e))

def check_i2c_permissions():
    """Check I2C bus permissions"""
    logger.info("\n--- I2C Permission Check ---")
    
    bus_path = f"/dev/i2c-{I2C_BUS}"
    if not os.path.exists(bus_path):
        logger.error("I2C bus %d does not exist (%s)", I2C_BUS, bus_path)
        return False
    
    # Check if the current user has read/write access
    if os.access(bus_path, os.R_OK | os.W_OK):
        logger.info("I2C bus %d (%s) is accessible", I2C_BUS, bus_path)
        
        # Try to get more detailed permission info
        try:
            import stat
            st = os.stat(bus_path)
            mode = st.st_mode
            perms = stat.filemode(mode)
            logger.info("Permissions: %s", perms)
            logger.info("Owner: %d, Group: %d", st.st_uid, st.st_gid)
        except Exception as e:
            logger.warning("Could not get detailed permission info: %s", str(e))
        
        return True
    else:
        logger.error("No permission to access I2C bus %d (%s)", I2C_BUS, bus_path)
        logger.error("Try running with sudo or add your user to the i2c group:")
        logger.error("  sudo usermod -a -G i2c $USER")
        logger.error("Then log out and log back in.")
        return False

def check_servo_power():
    """Check servo power by monitoring pulses"""
    if not pca_connected:
        logger.error("Cannot check servo power: PCA9685 not connected")
        return
    
    logger.info("\n--- Servo Power Check ---")
    logger.info("Testing if servos are receiving power...")
    
    # Test each servo with a small movement to see if it responds
    for channel in SERVO_CHANNELS:
        logger.info("Testing power to servo %d", channel)
        
        # Try setting the servo to 90 degrees
        set_servo_position(channel, 90)
        time.sleep(0.5)
        
        # Try setting it to 100 degrees to see if there's movement
        set_servo_position(channel, 100)
        time.sleep(0.5)
        
        # Return to 90
        set_servo_position(channel, 90)
        
        # Ask user if servo moved
        response = input(f"Did servo {channel} move? (y/n): ")
        if response.lower() == 'y':
            logger.info("Servo %d appears to be powered and responsive", channel)
        else:
            logger.warning("Servo %d did not move. Check power and connections!", channel)
            print("\nPossible issues:")
            print("1. Servo not properly connected to channel")
            print("2. Insufficient power to the PCA9685 or servos")
            print("3. Servo might be damaged")

def reset_pca9685():
    """Reset the PCA9685 controller"""
    if not pca_connected or pwm is None:
        logger.error("Cannot reset: PCA9685 not connected")
        return False
    
    logger.info("Resetting PCA9685...")
    
    try:
        # Reset all channels
        for i in range(16):  # PCA9685 has 16 channels
            pwm.set_pwm(i, 0, 0)
        
        # Reinitialize frequency
        pwm.set_pwm_freq(SERVO_FREQ)
        
        logger.info("PCA9685 reset successfully")
        return True
    except Exception as e:
        logger.error("Error resetting PCA9685: %s", str(e))
        return False

def main():
    """Main function with diagnostic menu"""
    parser = argparse.ArgumentParser(description="PS3 Controller Servo Diagnostic Tool")
    parser.add_argument("--reset", action="store_true", help="Reset the PCA9685 and servos to default position")
    parser.add_argument("--test-all", action="store_true", help="Run all tests automatically")
    parser.add_argument("--check-permissions", action="store_true", help="Check I2C bus permissions")
    args = parser.parse_args()
    
    logger.info("=== PS3 Controller Servo Diagnostic Tool ===")
    logger.info("Starting diagnostic sequence...")
    
    # Check permissions if requested
    if args.check_permissions:
        check_i2c_permissions()
        return
    
    # Detect hardware
    pca_success = detect_pca9685()
    controller = find_controller()
    
    # Reset if requested
    if args.reset and pca_success:
        reset_pca9685()
        for channel in SERVO_CHANNELS:
            set_servo_position(channel, 90)
        logger.info("Reset complete. All servos centered.")
        return
    
    # Run all tests if requested
    if args.test_all and pca_success:
        reset_pca9685()
        check_i2c_permissions()
        test_all_servos()
        check_servo_power()
        if controller:
            run_controller_servo_test(controller)
        return
    
    # If not auto-testing, show menu
    while True:
        print("\n=== Diagnostic Menu ===")
        print("1. Check I2C Permissions")
        print("2. Reset PCA9685")
        print("3. Test All Servos")
        print("4. Test Specific Servo")
        print("5. Check Servo Power")
        print("6. Test Controller with Servos")
        print("7. Direct Servo Control")
        print("8. Exit")
        
        choice = input("\nEnter choice (1-8): ")
        
        if choice == '1':
            check_i2c_permissions()
        elif choice == '2':
            reset_pca9685()
        elif choice == '3':
            test_all_servos()
        elif choice == '4':
            channel = int(input("Enter servo channel (0-3): "))
            test_servo_range(channel)
            test_servo_sweep(channel)
        elif choice == '5':
            check_servo_power()
        elif choice == '6':
            if controller:
                run_controller_servo_test(controller)
            else:
                logger.error("No controller connected.")
        elif choice == '7':
            test_servo_direct()
        elif choice == '8':
            break
        else:
            logger.warning("Invalid choice. Please enter 1-8.")
    
    # Clean up
    if pca_connected:
        reset_pca9685()
    
    logger.info("Diagnostic session complete.")

if __name__ == "__main__":
    main()
