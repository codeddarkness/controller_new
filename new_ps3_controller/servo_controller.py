#!/usr/bin/env python3
"""
Servo Controller for Raspberry Pi
Supports PS3 and Xbox controllers for manipulating servos via PCA9685
Includes testing and debugging functionality
"""

import evdev
import argparse  # noqa: F401 - Used in main()
import json
import logging
import math
import os
import signal  # noqa: F401 - Used in signal handlers
import sqlite3
import sys
import threading  # noqa: F401 - Used in update thread
import time
from datetime import datetime
from evdev import InputDevice, ecodes
from sqlite3 import Error

def main():
    """Main function"""
    print("Starting main function...")
    
    # Force using known controller
    force_controller = True  # Set to True to force controller detection
    """Main function"""
    print("Starting main function...")
    print("Arguments parsed...")
    print("Hardware detection complete...")
    print("Searching for controller...")

    print("Starting main function...")
    
    global exit_flag, controller_connected, controller_type
    # Rest of the function...
# Configure logging
def setup_logging():
    """Set up logging system with main, debug and test loggers"""
    # Create directory for logs if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Main logger for general application logs
    main_logger = logging.getLogger('main')
    main_logger.setLevel(logging.INFO)
    main_handler = logging.FileHandler('logs/servo_controller.log')
    main_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    main_logger.addHandler(main_handler)
    
    # Debug logger for detailed operation logs
    debug_logger = logging.getLogger('debug')
    debug_logger.setLevel(logging.DEBUG)
    debug_handler = logging.FileHandler('logs/debug.log')
    debug_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    debug_logger.addHandler(debug_handler)
    
    # Test logger for controller testing logs
    test_logger = logging.getLogger('test')
    test_logger.setLevel(logging.DEBUG)
    test_handler = logging.FileHandler('logs/config_debug.log')
    test_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    test_logger.addHandler(test_handler)
    
    return main_logger, debug_logger, test_logger

# Set up loggers
main_logger, debug_logger, test_logger = setup_logging()

# Try to import hardware libraries, but continue if they're not available
try:
    import Adafruit_PCA9685
    PCA9685_AVAILABLE = True
    main_logger.info("PCA9685 library available")
except ImportError:
    print("Warning: Adafruit_PCA9685 not found. Running in simulation mode.")
    main_logger.warning("Adafruit_PCA9685 not found. Running in simulation mode.")
    PCA9685_AVAILABLE = False

try:
    from mpu6050 import mpu6050
    MPU6050_AVAILABLE = True
    main_logger.info("MPU6050 library available")
except ImportError:
    print("Warning: MPU6050 library not found. Running in simulation mode.")
    main_logger.warning("MPU6050 library not found. Running in simulation mode.")
    MPU6050_AVAILABLE = False
except Exception as e:
    print(f"Warning: MPU6050 library found but cannot be used: {e}. Running in simulation mode.")
    main_logger.warning(f"MPU6050 library found but cannot be used: {e}. Running in simulation mode.")
    MPU6050_AVAILABLE = False

# Constants
# Servo Constants
SERVO_MIN = 150  # Minimum pulse length
SERVO_MAX = 600  # Maximum pulse length
SERVO_RANGE = 180  # Servo range in degrees
SERVO_CHANNELS = [0, 1, 2, 3]  # Four servo channels
SERVO_FREQ = 50  # PWM frequency for servos (50Hz standard)
I2C_BUSES = [0, 1]  # I2C buses to check

# Controller type constants
CONTROLLER_TYPE_PS3 = 'PS3'
CONTROLLER_TYPE_XBOX = 'XBOX'
CONTROLLER_TYPE_GENERIC = 'GENERIC'
CONTROLLER_TYPE_NONE = 'NONE'

# PS3 controller mappings according to requested_button_mappings.txt and debug logs
PS3_BUTTON_MAPPINGS = {
    304: "Cross (✕)",      # South 
    305: "Circle (○)",     # East
    307: "Triangle (△)",   # North
    308: "Square (□)",     # West
    294: "L1",             # Left shoulder
    295: "R1",             # Right shoulder
    298: "L2",             # Left trigger
    299: "R2",             # Right trigger
    300: "D-Pad Up",
    301: "D-Pad Right",
    302: "D-Pad Down",
    303: "D-Pad Left",
    288: "Select",
    291: "Start",
    292: "PS Button",
    296: "L3",             # Left stick press
    297: "R3",             # Right stick press
    289: "Unknown (289)",  # Additional buttons found in logs
    290: "Unknown (290)",  # Additional buttons found in logs
    293: "Unknown (293)"   # Additional buttons found in logs
}

PS3_AXIS_MAPPINGS = {
    0: "Left Stick X",      # Left stick horizontal
    1: "Left Stick Y",      # Left stick vertical
    2: "Right Stick X",     # Right stick horizontal (Z axis on PS3)
    3: "Right Stick Y",     # Right stick vertical (RX axis on PS3)
    4: "Unknown Axis 4",    # -32767 static on PS3
    5: "Unknown Axis 5",    # 32767 static on PS3
    6: "Unknown Axis 6"     # 32767 static on PS3
}

# Xbox controller mappings - using standard ecodes constants
XBOX_BUTTON_MAPPINGS = {
    ecodes.BTN_SOUTH: "A",
    ecodes.BTN_EAST: "B",
    ecodes.BTN_WEST: "X",
    ecodes.BTN_NORTH: "Y",
    ecodes.BTN_TL: "Left Shoulder",
    ecodes.BTN_TR: "Right Shoulder",
    ecodes.BTN_SELECT: "Select/Back",
    ecodes.BTN_START: "Start",
    ecodes.BTN_MODE: "Xbox Button",
    ecodes.BTN_THUMBL: "Left Thumb",
    ecodes.BTN_THUMBR: "Right Thumb",
    ecodes.BTN_DPAD_UP: "D-Pad Up",
    ecodes.BTN_DPAD_DOWN: "D-Pad Down",
    ecodes.BTN_DPAD_LEFT: "D-Pad Left",
    ecodes.BTN_DPAD_RIGHT: "D-Pad Right"
}

XBOX_AXIS_MAPPINGS = {
    0: "Left Stick X",
    1: "Left Stick Y",
    3: "Right Stick X",
    4: "Right Stick Y",
    2: "Left Trigger",
    5: "Right Trigger"
}

# Global variables
controller_type = CONTROLLER_TYPE_NONE
controller_connected = False
controller_device_path = None
exit_flag = False
q_pressed = False
pca_connected = False
pca_bus = None
mpu_connected = False
mpu_bus = None
pwm = None
mpu = None

# Hold toggle states for servos
hold_state = {0: False, 1: False, 2: False, 3: False}

# Global lock for servos
lock_state = False

# Store current servo positions (default to 90 degrees - center position)
servo_positions = {0: 90, 1: 90, 2: 90, 3: 90}

# Servo directions for display
servo_directions = {0: "neutral", 1: "neutral", 2: "neutral", 3: "neutral"}

# MPU6050 data structure
mpu_data = {
    'accel': {'x': 0, 'y': 0, 'z': 0},
    'gyro': {'x': 0, 'y': 0, 'z': 0},
    'temp': 0,
    'direction': {'x': "neutral", 'y': "neutral", 'z': "neutral"}
}

# Servo speed modifier (1.0 = normal, <1.0 = slower, >1.0 = faster)
servo_speed = 1.0

# Database setup
db_path = 'servo_data.db'

def setup_database():
    """Initialize the SQLite database and tables"""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table for servo logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS servo_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                servo_data TEXT,
                mpu_data TEXT,
                hardware_status TEXT
            )
        ''')
        
        # Create table for test results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                test_type TEXT,
                result TEXT,
                details TEXT
            )
        ''')
        
        conn.commit()
        main_logger.info("Database setup complete")
        return True
    except Error as e:
        main_logger.error(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def log_data():
    """Log current data to the database"""
    try:
        # Prepare data to be logged
        timestamp = datetime.now().isoformat()
        servo_data = {
            'positions': servo_positions,
            'hold_states': hold_state,
            'directions': servo_directions,
            'speed': servo_speed
        }
        
        hardware_status = {
            'controller': {
                'connected': controller_connected,
                'type': controller_type
            },
            'pca9685': {
                'connected': pca_connected,
                'bus': pca_bus
            },
            'mpu6050': {
                'connected': mpu_connected,
                'bus': mpu_bus
            }
        }
        
        # Convert to JSON
        servo_json = json.dumps(servo_data)
        mpu_json = json.dumps(mpu_data)
        status_json = json.dumps(hardware_status)
        
        # Store in database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO servo_logs (timestamp, servo_data, mpu_data, hardware_status) VALUES (?, ?, ?, ?)",
            (timestamp, servo_json, mpu_json, status_json)
        )
        conn.commit()
        conn.close()
        
    except Exception as e:
        main_logger.error(f"Logging error: {e}")

def log_test_result(test_type, result, details=""):
    """Log a test result to the database"""
    try:
        timestamp = datetime.now().isoformat()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO test_results (timestamp, test_type, result, details) VALUES (?, ?, ?, ?)",
            (timestamp, test_type, result, details)
        )
        conn.commit()
        conn.close()
        
        main_logger.info(f"Test result logged: {test_type} - {result}")
    except Exception as e:
        main_logger.error(f"Error logging test result: {e}")

def detect_i2c_devices():
    print("Hardware detection complete...")
    """Detect available I2C devices and initialize hardware"""
    global pca_connected, mpu_connected, pca_bus, mpu_bus, pwm, mpu
    
    # Check each I2C bus
    for bus_num in I2C_BUSES:
        # Try to initialize PCA9685 on this bus
        if PCA9685_AVAILABLE and not pca_connected:
            try:
                test_pwm = Adafruit_PCA9685.PCA9685(busnum=bus_num)
                pca_connected = True
                pca_bus = bus_num
                pwm = test_pwm  # Save the working instance
                pwm.set_pwm_freq(SERVO_FREQ)
                main_logger.info(f"PCA9685 found on I2C bus {bus_num}")
                print(f"PCA9685 found on I2C bus {bus_num}")
                
                # Log test result
                log_test_result("PCA9685", "PASS", f"Connected on bus {bus_num}")
            except Exception as e:
                main_logger.warning(f"PCA9685 not found on I2C bus {bus_num}: {e}")
                print(f"PCA9685 not found on I2C bus {bus_num}: {e}")
        
        # Try to initialize MPU6050 on this bus
        if MPU6050_AVAILABLE and not mpu_connected:
            try:
                # Make sure mpu6050 is properly called as a constructor
                test_mpu = mpu6050(bus_num)
                # Test if it's working by reading temperature
                _ = test_mpu.get_temp()  # Test if sensor is working
                mpu_connected = True
                mpu_bus = bus_num
                mpu = test_mpu  # Save the working instance
                main_logger.info(f"MPU6050 found on I2C bus {bus_num}")
                print(f"MPU6050 found on I2C bus {bus_num}")
                
                # Log test result
                log_test_result("MPU6050", "PASS", f"Connected on bus {bus_num}")
            except Exception as e:
                main_logger.warning(f"MPU6050 not found on I2C bus {bus_num}: {e}")
                print(f"MPU6050 not found on I2C bus {bus_num}: {e}")
    
    # If hardware is still not connected, log as failed tests
    if not pca_connected:
        log_test_result("PCA9685", "FAIL", "No connection on any I2C bus")
        main_logger.warning("No PCA9685 found. Running servo control in simulation mode.")
        print("No PCA9685 found. Running servo control in simulation mode.")
    
    if not mpu_connected:
        log_test_result("MPU6050", "FAIL", "No connection on any I2C bus")
        main_logger.warning("No MPU6050 found. Running MPU in simulation mode.")
        print("No MPU6050 found. Running MPU in simulation mode.")

def find_game_controller(device_path=None):
    """Find and return a PlayStation or Xbox controller device"""
    global controller_type, controller_connected, controller_device_path
    
    try:
        if device_path:
            # Use specified device path
            try:
                device = InputDevice(device_path)
                controller_device_path = device_path
                
                if 'PLAYSTATION' in device.name.upper() or 'PlayStation' in device.name:
                    controller_type = CONTROLLER_TYPE_PS3 if '3' in device.name else CONTROLLER_TYPE_PS3
                    controller_connected = True
                    main_logger.info(f"PS3 controller found: {device.name}")
                    print(f"PS3 controller found: {device.name}")
                    log_test_result("Controller", "PASS", f"PS3 controller found: {device.name}")
                    return device
                    
                elif 'Xbox' in device.name or 'XBOX' in device.name.upper():
                    controller_type = CONTROLLER_TYPE_XBOX
                    controller_connected = True
                    main_logger.info(f"Xbox controller found: {device.name}")
                    print(f"Xbox controller found: {device.name}")
                    log_test_result("Controller", "PASS", f"Xbox controller found: {device.name}")
                    return device
                    
                else:
                    controller_type = CONTROLLER_TYPE_GENERIC
                    controller_connected = True
                    main_logger.info(f"Generic controller found: {device.name}")
                    print(f"Generic controller found: {device.name}")
                    log_test_result("Controller", "PASS", f"Generic controller found: {device.name}")
                    return device
                    
            except Exception as e:
                main_logger.error(f"Error using specified device: {e}")
                print(f"Could not open specified device {device_path}: {e}")
        
        # Auto-detect controller
        devices = [InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            controller_device_path = device.path
            
            if 'PLAYSTATION(R)3' in device.name or 'PlayStation 3' in device.name:
                controller_type = CONTROLLER_TYPE_PS3
                controller_connected = True
                main_logger.info(f"Controller connected: {device.name} ({controller_type})")
                print(f"PS3 controller found: {device.name}")
                log_test_result("Controller", "PASS", f"PS3 controller found: {device.name}")
                return device
                
            elif 'PLAYSTATION' in device.name or 'PlayStation' in device.name:
                controller_type = CONTROLLER_TYPE_PS3
                controller_connected = True
                main_logger.info(f"PlayStation controller found: {device.name}")
                print(f"PlayStation controller found: {device.name}")
                log_test_result("Controller", "PASS", f"PlayStation controller found: {device.name}")
                return device
                
            elif 'Xbox' in device.name or 'XBOX' in device.name.upper():
                controller_type = CONTROLLER_TYPE_XBOX
                controller_connected = True
                main_logger.info(f"Xbox controller found: {device.name}")
                print(f"Xbox controller found: {device.name}")
                log_test_result("Controller", "PASS", f"Xbox controller found: {device.name}")
                return device
    except Exception as e:
        main_logger.error(f"Error finding controller: {e}")
        log_test_result("Controller", "FAIL", f"Error: {e}")
    
    main_logger.warning("No game controller found")
    print("No game controller found. Using keyboard interface.")
    controller_type = CONTROLLER_TYPE_NONE
    log_test_result("Controller", "FAIL", "No controller found")
    return None

def list_available_controllers():
    """List all available input devices"""
    print("Available input devices:")
    for i, path in enumerate(evdev.list_devices()):
        try:
            device = evdev.InputDevice(path)
            print(f"  {i+1}. {path}: {device.name}")
        except:
            print(f"  {i+1}. {path}: [Error accessing device]")
    print("")

def joystick_to_pwm(value):
    """Convert joystick value (-32767 to 32767) to servo pulse and angle"""
    # Normalize joystick value to 0-180 degrees
    angle = int(((value + 32767) / 65534) * SERVO_RANGE)
    # Apply speed modifier
    # (this doesn't actually change the speed, just reduces the range of motion for finer control)
    if servo_speed < 1.0:
        # Center value and reduce range
        center = SERVO_RANGE / 2
        angle = center + (angle - center) * servo_speed
    
    # Calculate PWM pulse value
    pwm_value = int(SERVO_MIN + (angle / SERVO_RANGE) * (SERVO_MAX - SERVO_MIN))
    
    return pwm_value, angle

def set_servo_position(channel, angle):
    """Set a servo to a specific angle (0-180)"""
    # These globals are modified in this function
    
    if channel not in SERVO_CHANNELS:
        return False
    
    # Update direction
    if angle > servo_positions[channel]:
        servo_directions[channel] = "up" if channel in [1, 3] else "right"
    elif angle < servo_positions[channel]:
        servo_directions[channel] = "down" if channel in [1, 3] else "left"
    else:
        servo_directions[channel] = "neutral"
    
    # Constrain the angle
    angle = max(0, min(180, angle))
    
    # Calculate pulse length
    pulse = int(SERVO_MIN + (angle / 180.0) * (SERVO_MAX - SERVO_MIN))
    
    # Set the pulse
    if pca_connected and pwm:
        try:
            pwm.set_pwm(channel, 0, pulse)
        except Exception as e:
            main_logger.error(f"Error setting servo {channel}: {e}")
    
    # Update position
    servo_positions[channel] = angle
    return True

def move_servo(channel, value):
    """Move a servo based on joystick input"""
    # These globals are modified in this function
    
    if lock_state or hold_state[channel]:
        debug_logger.info(f"Servo {channel} movement blocked (locked:{lock_state}, hold:{hold_state[channel]})")
        return  # Don't move if locked or held
    
    # Store old position for logging
    old_position = servo_positions[channel]
    
    # For channels 0 and 2, we reverse the direction based on requested_button_mappings.txt
    if channel == 0 or channel == 2:
        value = -value
    
    # Convert joystick value to servo position
    pwm_value, angle = joystick_to_pwm(value)
    
    # Set servo position
    set_servo_position(channel, angle)
    
    # Log the movement
    debug_logger.info(f"SERVO - Channel {channel} - From {old_position}° to {angle}° - Joystick value: {value}")

def move_all_servos(angle):
    """Move all servos to a specified angle"""
    # These globals are modified in this function
    
    if lock_state:
        debug_logger.info("All servo movement blocked (locked)")
        return  # Don't move if locked
    
    # Move each servo that isn't on hold
    for channel in SERVO_CHANNELS:
        if not hold_state[channel]:
            old_position = servo_positions[channel]
            set_servo_position(channel, angle)
            debug_logger.info(f"SERVO - Channel {channel} - From {old_position}° to {angle}° - Global command")

def log_controller_event(event_type, code, value, description=""):
    """Log controller events to debug.log"""
    try:
        if event_type == ecodes.EV_KEY:
            # Log button events
            btn_name = "Unknown"
            if controller_type == CONTROLLER_TYPE_PS3:
                btn_name = PS3_BUTTON_MAPPINGS.get(code, f"Unknown ({code})")
            elif controller_type == CONTROLLER_TYPE_XBOX:
                btn_name = XBOX_BUTTON_MAPPINGS.get(code, f"Unknown ({code})")
            
            btn_state = "Pressed" if value == 1 else "Released" if value == 0 else "Held"
            debug_logger.info(f"BUTTON - {btn_name} - {btn_state} - Code: {code}")
            
        elif event_type == ecodes.EV_ABS:
            # Log joystick/axis events
            axis_name = "Unknown"
            
            if controller_type == CONTROLLER_TYPE_PS3:
                axis_name = PS3_AXIS_MAPPINGS.get(code, f"Unknown Axis ({code})")
            elif controller_type == CONTROLLER_TYPE_XBOX:
                axis_name = XBOX_AXIS_MAPPINGS.get(code, f"Unknown Axis ({code})")
            
            debug_logger.info(f"AXIS - {axis_name} - Value: {value}")
        
        # Add additional custom description if provided
        if description:
            debug_logger.info(f"INFO - {description}")
    except Exception as e:
        main_logger.error(f"Error logging controller event: {e}")

def update_mpu_data():
    """Update MPU6050 sensor data"""
    # - using function param instead
    
    if mpu_connected and mpu:
        try:
            # Read accelerometer data
            accel_data = mpu.get_accel_data()
            mpu_data['accel']['x'] = accel_data['x']
            mpu_data['accel']['y'] = accel_data['y']
            mpu_data['accel']['z'] = accel_data['z']
            
            # Read gyroscope data
            gyro_data = mpu.get_gyro_data()
            mpu_data['gyro']['x'] = gyro_data['x']
            mpu_data['gyro']['y'] = gyro_data['y']
            mpu_data['gyro']['z'] = gyro_data['z']
            
            # Read temperature
            mpu_data['temp'] = mpu.get_temp()
            
            # Determine direction for visualization
            threshold = 0.5  # Threshold for considering movement
            mpu_data['direction']['x'] = "right" if accel_data['x'] > threshold else "left" if accel_data['x'] < -threshold else "neutral"
            mpu_data['direction']['y'] = "up" if accel_data['y'] > threshold else "down" if accel_data['y'] < -threshold else "neutral"
            mpu_data['direction']['z'] = "up" if accel_data['z'] > 9.8 + threshold else "down" if accel_data['z'] < 9.8 - threshold else "neutral"
            
        except Exception as e:
            main_logger.error(f"Error reading MPU data: {e}")
    else:
        # Simulation mode - generate some fake data
        mpu_data['accel']['x'] = math.sin(time.time() * 0.5) * 0.5
        mpu_data['accel']['y'] = math.cos(time.time() * 0.7) * 0.5
        mpu_data['accel']['z'] = 9.8 + math.sin(time.time() * 0.3) * 0.2
        
        mpu_data['gyro']['x'] = math.sin(time.time() * 0.2) * 2
        mpu_data['gyro']['y'] = math.cos(time.time() * 0.4) * 2
        mpu_data['gyro']['z'] = math.sin(time.time() * 0.6) * 2
        
        mpu_data['temp'] = 25 + math.sin(time.time() * 0.1) * 0.5
        
        # Determine direction for visualization
        threshold = 0.3
        mpu_data['direction']['x'] = "right" if mpu_data['accel']['x'] > threshold else "left" if mpu_data['accel']['x'] < -threshold else "neutral"
        mpu_data['direction']['y'] = "up" if mpu_data['accel']['y'] > threshold else "down" if mpu_data['accel']['y'] < -threshold else "neutral"
        mpu_data['direction']['z'] = "up" if mpu_data['accel']['z'] > 9.8 + threshold else "down" if mpu_data['accel']['z'] < 9.8 - threshold else "neutral"

def get_direction_arrow(direction):
    """Get arrow character based on direction"""
    arrows = {
        "up": "↑", "down": "↓",
        "left": "←", "right": "→",
        "neutral": "○"
    }
    return arrows.get(direction, "○")

def display_status():
    """Display current status in console"""
    # Clear the line (carriage return without newline)
    sys.stdout.write("\r" + " " * 120 + "\r")
    
    # Hardware status
    pca_status = "ON" if pca_connected else "OFF"
    mpu_status = "ON" if mpu_connected else "OFF"
    ctrl_status = controller_type if controller_connected else "NONE"
    
    # Servo status
    servo_text = ""
    for ch in SERVO_CHANNELS:
        arrow = get_direction_arrow(servo_directions[ch])
        lock = "L" if hold_state[ch] else " "
        servo_text += f"S{ch}:{arrow}{servo_positions[ch]:3}°{lock} "
    
    # MPU data (condensed display)
    mpu_text = ""
    if mpu_connected or True:  # Show even in simulation mode
        ax = get_direction_arrow(mpu_data['direction']['x'])
        ay = get_direction_arrow(mpu_data['direction']['y'])
        az = get_direction_arrow(mpu_data['direction']['z'])
        mpu_text = f"MPU:X:{ax}{mpu_data['accel']['x']:4.1f} Y:{ay}{mpu_data['accel']['y']:4.1f} Z:{az}{mpu_data['accel']['z']:4.1f}"
    
    # Status line (single line)
    status_line = f"{servo_text}| {mpu_text} | PCA:{pca_status} MPU:{mpu_status} Ctrl:{ctrl_status} Spd:{servo_speed:.1f}x"
    sys.stdout.write(status_line)
    sys.stdout.flush()

def run_controller_test_mode(gamepad):
    """Interactive controller test mode"""
    print("\nEntering Controller Test Mode")
    print("-----------------------------")
    print("This mode will help you identify button and axis codes for your controller.")
    print("All events will be logged to logs/config_debug.log")
    print("\nPress buttons or move joysticks when prompted. Press Ctrl+C to exit.")
    
    # First log controller information
    test_logger.info(f"CONTROLLER TEST - Device: {gamepad.name}")
    test_logger.info(f"CONTROLLER TEST - Path: {gamepad.path}")
    test_logger.info(f"CONTROLLER TEST - Type detected: {controller_type}")
    
    try:
        # Interactive test sequence
        tests = [
            "Press the D-pad Up button",
            "Press the D-pad Down button",
            "Press the D-pad Left button",
            "Press the D-pad Right button",
            "Press the Face buttons (X/Square, Circle, Triangle, Cross/A/B/Y)",
            "Press the Left Shoulder button (L1/LB)",
            "Press the Right Shoulder button (R1/RB)",
            "Press the Left Trigger button (L2/LT)",
            "Press the Right Trigger button (R2/RT)",
            "Move the Left Stick in all directions",
            "Move the Right Stick in all directions",
            "Press the Left Stick button (L3)",
            "Press the Right Stick button (R3)",
            "Press the Start button",
            "Press the Select/Back button",
            "Press the PS/Xbox button"
        ]
        
        for test_instruction in tests:
            print(f"\n> {test_instruction}")
            test_logger.info(f"INSTRUCTION: {test_instruction}")
            
            # Wait for events for 3 seconds
            start_time = time.time()
            while time.time() - start_time < 3:
                event = gamepad.read_one()
                if event:
                    if event.type == ecodes.EV_KEY:
                        btn_name = "Unknown"
                        if controller_type == CONTROLLER_TYPE_PS3:
                            btn_name = PS3_BUTTON_MAPPINGS.get(event.code, f"Unknown ({event.code})")
                        else:
                            btn_name = XBOX_BUTTON_MAPPINGS.get(event.code, f"Unknown ({event.code})")

                        btn_state = "Pressed" if event.value == 1 else "Released" if event.value == 0 else "Held"
                        test_logger.info(f"TEST - BUTTON - {btn_name} - {btn_state} - Code: {event.code}")
                        print(f"  Detected: {btn_name} ({event.code}) - {btn_state}")

                    elif event.type == ecodes.EV_ABS and abs(event.value) > 1000:  # Significant axis movement
                        axis_name = "Unknown Axis"
                        if controller_type == CONTROLLER_TYPE_PS3:
                            axis_name = PS3_AXIS_MAPPINGS.get(event.code, f"Unknown Axis ({event.code})")
                        else:
                            axis_name = XBOX_AXIS_MAPPINGS.get(event.code, f"Unknown Axis ({event.code})")

                        test_logger.info(f"TEST - AXIS - {axis_name} - Value: {event.value}")
                        print(f"  Detected: {axis_name} ({event.code}) - Value: {event.value}")

                # Short delay to prevent CPU overload
                time.sleep(0.01)

            # Give user a short break between instructions
            time.sleep(0.5)

        print("\nController test complete.")
        print("Results have been logged to logs/config_debug.log")
        print("Press Ctrl+C to exit or any key to continue to normal operation.")

        # Wait for a keypress or timeout
        try:
            input("Press Enter to continue...")
        except:
            pass

    except KeyboardInterrupt:
        print("\nTest mode interrupted.")
    except Exception as e:
        print(f"\nError in test mode: {e}")
        main_logger.error(f"Test mode error: {e}")

    return


if __name__ == "__main__":
    main()

