#!/usr/bin/env python3

"""
Servo Controller - Fixed Version
This version corrects the button mappings and I2C bus configuration
to work with the PS3 controller and PCA9685 servo driver.
"""

import json
import signal
import sys
import time
import threading
import os
import argparse
import select
import evdev
from evdev import InputDevice, ecodes
from flask import Flask, render_template, jsonify, request
import logging
from datetime import datetime
import math
import sqlite3
from sqlite3 import Error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('servo_controller')

# Try to import hardware libraries, but continue if they're not available
try:
    import Adafruit_PCA9685
    PCA9685_AVAILABLE = True
except ImportError:
    print("Warning: Adafruit_PCA9685 not found. Running in simulation mode.")
    PCA9685_AVAILABLE = False

try:
    from mpu6050 import mpu6050
    MPU6050_AVAILABLE = True
except ImportError:
    print("Warning: MPU6050 library not found. Running in simulation mode.")
    MPU6050_AVAILABLE = False

# Configuration Constants
SERVO_MIN = 150  # Min pulse length (0 degrees)
SERVO_MAX = 600  # Max pulse length (180 degrees)
SERVO_FREQ = 50  # PWM frequency for servos (50Hz standard)
SERVO_CHANNELS = [0, 1, 2, 3]  # Servo channels to control
I2C_BUSES = [1]  # Use only I2C bus 1 which is confirmed working

# Global variables
hold_state = {0: False, 1: False, 2: False, 3: False}
lock_state = False  # Global lock for all servos
servo_positions = {0: 90, 1: 90, 2: 90, 3: 90}
servo_directions = {0: "neutral", 1: "neutral", 2: "neutral", 3: "neutral"}
servo_speed = 1.0
controller_type = None
controller_connected = False
pca_connected = False
mpu_connected = False
pca_bus = None
mpu_bus = None
mpu_data = {
    'accel': {'x': 0, 'y': 0, 'z': 0},
    'gyro': {'x': 0, 'y': 0, 'z': 0},
    'temp': 0,
    'direction': {'x': "neutral", 'y': "neutral", 'z': "neutral"}
}
app = Flask(__name__)
pwm = None
mpu = None
q_pressed = False
exit_flag = False
db_path = 'servo_data.db'

# FIXED PS3 controller button mappings based on config_debug.log
PS3_BUTTON_MAPPINGS = {
    # Face buttons
    304: "Cross (✕)",     # South/X button
    305: "Circle (○)",    # East/Circle button
    307: "Triangle (△)",  # North/Triangle button
    308: "Square (□)",    # West/Square button
    
    # Shoulder/trigger buttons
    294: "L1",            # Left shoulder
    295: "R1",            # Right shoulder
    298: "L2",            # Left trigger
    299: "R2",            # Right trigger
    
    # D-pad buttons
    300: "D-Pad Up",      # D-pad up
    301: "D-Pad Right",   # D-pad right
    302: "D-Pad Down",    # D-pad down
    303: "D-Pad Left",    # D-pad left
    
    # Other buttons
    288: "Select",        # Select button
    291: "Start",         # Start button
    292: "PS Button",     # PS Button
    293: "Unknown (293)", # Unknown button
    296: "L3",            # Left stick press
    297: "R3"             # Right stick press
}

# PS3 joystick axis mappings
PS3_AXIS_MAPPINGS = {
    0: "Left Stick X",        # Left stick horizontal
    1: "Left Stick Y",        # Left stick vertical
    2: "Right Stick X (PS3-Z)",  # Right stick horizontal 
    3: "Right Stick Y (PS3-RX)"  # Right stick vertical
}

# Configure debug logging
def setup_debug_logging():
    """Set up a dedicated debug logger for controller inputs"""
    debug_logger = logging.getLogger('controller_debug')
    debug_logger.setLevel(logging.DEBUG)
    
    # Create file handler for debug.log
    debug_file = logging.FileHandler('debug.log')
    debug_file.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    debug_file.setFormatter(formatter)
    
    # Add handler to logger
    debug_logger.addHandler(debug_file)
    
    return debug_logger

# Configure controller test logging
def setup_test_logging():
    """Set up a dedicated logger for controller testing"""
    test_logger = logging.getLogger('controller_test')
    test_logger.setLevel(logging.DEBUG)
    
    # Create file handler for config_debug.log
    test_file = logging.FileHandler('config_debug.log')
    test_file.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    test_file.setFormatter(formatter)
    
    # Add handler to logger
    test_logger.addHandler(test_file)
    
    return test_logger

# Initialize the loggers
debug_logger = setup_debug_logging()
test_logger = setup_test_logging()

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
        
        conn.commit()
        return True
    except Error as e:
        logger.error(f"Database error: {e}")
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
        logger.error(f"Logging error: {e}")

def detect_i2c_devices():
    """Detect available I2C devices and initialize hardware"""
    global pca_connected, mpu_connected, pca_bus, mpu_bus, pwm, mpu
    
    print("\n--- I2C Device Detection ---")
    
    # Only check bus 1 which we know works
    bus_num = 1
    
    # Try to initialize PCA9685 on this bus
    if PCA9685_AVAILABLE:
        try:
            test_pwm = Adafruit_PCA9685.PCA9685(busnum=bus_num)
            pca_connected = True
            pca_bus = bus_num
            pwm = test_pwm  # Save the working instance
            pwm.set_pwm_freq(SERVO_FREQ)
            print(f"PCA9685 found on I2C bus {bus_num}")
        except Exception as e:
            print(f"PCA9685 not found on I2C bus {bus_num}: {e}")
    
    # Try to initialize MPU6050 on this bus
    if MPU6050_AVAILABLE:
        try:
            test_mpu = mpu6050(bus_num)
            # Test if it's working by reading temperature
            test_mpu.get_temp()
            mpu_connected = True
            mpu_bus = bus_num
            mpu = test_mpu  # Save the working instance
            print(f"MPU6050 found on I2C bus {bus_num}")
        except Exception as e:
            print(f"MPU6050 not found on I2C bus {bus_num}: {e}")
    
    # If hardware is still not connected, set up simulation
    if not pca_connected:
        print("No PCA9685 found. Running servo control in simulation mode.")
    
    if not mpu_connected:
        print("No MPU6050 found. Running MPU in simulation mode.")

def find_game_controller():
    """Find and return a PlayStation or Xbox controller device"""
    global controller_type, controller_connected
    
    try:
        devices = [InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            if 'PLAYSTATION(R)3' in device.name or 'PlayStation 3' in device.name:
                controller_type = 'PS3'
                controller_connected = True
                return device
            elif 'Xbox' in device.name:
                controller_type = 'Xbox'
                controller_connected = True
                return device
    except Exception as e:
        logger.error(f"Error finding controller: {e}")
    
    print("No game controller found. Using keyboard or web interface.")
    return None

def joystick_to_pwm(value):
    """Convert joystick value (-32767 to 32767) to servo pulse and angle"""
    # Normalize to 0-180 degrees
    angle = int(((value + 32767) / 65534) * 180)
    return angle

def set_servo_position(channel, angle):
    """Set a servo to a specific angle (0-180)"""
    global servo_positions, servo_directions
    
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
            # Verbose logging for debugging
            debug_logger.info(f"SERVO MOVED - Channel {channel} - Angle: {angle}° - Pulse: {pulse}")
        except Exception as e:
            logger.error(f"Error setting servo {channel}: {e}")
    else:
        # Log in simulation mode
        debug_logger.info(f"SIMULATION - Setting servo {channel} to {angle}°")
    
    # Update position
    servo_positions[channel] = angle
    return True

def move_servo(channel, value):
    """Move a servo based on joystick input"""
    global servo_positions, servo_directions
    
    if lock_state or hold_state[channel]:
        debug_logger.info(f"Servo {channel} movement blocked (locked:{lock_state}, hold:{hold_state[channel]})")
        return  # Don't move if locked or held
    
    # Store old position for logging
    old_position = servo_positions[channel]
    
    # Convert joystick value to servo position
    angle = joystick_to_pwm(value)
    
    # Set servo position
    set_servo_position(channel, angle)
    
    # Log the movement
    debug_logger.info(f"SERVO - Channel {channel} - From {old_position}° to {angle}° - Joystick value: {value}")

def move_all_servos(angle):
    """Move all servos to a specified angle"""
    
    if lock_state:
        debug_logger.info(f"All servo movement blocked (locked)")
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
            if controller_type == 'PS3':
                btn_name = PS3_BUTTON_MAPPINGS.get(code, f"Unknown ({code})")
            else:
                # Xbox button names
                btn_names = {
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
                }
                btn_name = btn_names.get(code, f"Unknown ({code})")
            
            btn_state = "Pressed" if value == 1 else "Released" if value == 0 else "Held"
            debug_logger.info(f"BUTTON - {btn_name} - {btn_state} - Code: {code}")
            
        elif event_type == ecodes.EV_ABS:
            # Log joystick/axis events
            axis_name = "Unknown"
            
            # Axis mappings
            axis_names = {
                0: "Left Stick X",
                1: "Left Stick Y",
                2: "Right Stick X (PS3-Z)",
                3: "Right Stick Y (PS3-RX)",
                4: "Right Stick Y (Xbox)",
                5: "Right Stick X (Xbox)",
                16: "D-pad X",
                17: "D-pad Y",
            }
            
            axis_name = axis_names.get(code, f"Unknown Axis ({code})")
            debug_logger.info(f"AXIS - {axis_name} - Value: {value}")
        
        # Add additional custom description if provided
        if description:
            debug_logger.info(f"INFO - {description}")
    except Exception as e:
        logger.error(f"Error logging controller event: {e}")

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
    pca_status = "CONNECTED" if pca_connected else "DISCONNECTED"
    mpu_status = "CONNECTED" if mpu_connected else "DISCONNECTED"
    controller_status = f"{controller_type}" if controller_connected else "DISCONNECTED"
    
    # Servo status
    servo_text = ""
    for ch in SERVO_CHANNELS:
        arrow = get_direction_arrow(servo_directions[ch])
        lock = "L" if hold_state[ch] else " "
        servo_text += f"S{ch}:{arrow}{servo_positions[ch]:3}°{lock} "
    
    # MPU data (if connected)
    mpu_text = ""
    if mpu_connected or True:  # Show in simulation mode too
        ax = get_direction_arrow(mpu_data['direction']['x'])
        ay = get_direction_arrow(mpu_data['direction']['y'])
        az = get_direction_arrow(mpu_data['direction']['z'])
        mpu_text = f"Accel: X:{ax}{mpu_data['accel']['x']:5.1f} Y:{ay}{mpu_data['accel']['y']:5.1f} Z:{az}{mpu_data['accel']['z']:5.1f}"
    
    # Hardware status
    hw_text = f"PCA:{pca_status}({pca_bus}) MPU:{mpu_status}({mpu_bus}) Ctrl:{controller_status} Spd:{servo_speed:.1f}x"
    
    # Combine all text
    status_text = f"{servo_text} | {mpu_text} | {hw_text}"
    sys.stdout.write(status_text)
    sys.stdout.flush()

def update_mpu_data():
    """Update MPU6050 sensor data"""
    global mpu_data
    
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
            logger.error(f"Error reading MPU data: {e}")
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

def run_controller_test_mode(gamepad):
    """Interactive controller test mode"""
    print("\nEntering Controller Test Mode")
    print("-----------------------------")
    print("This mode will help you identify button and axis codes for your controller.")
    print("All events will be logged to config_debug.log")
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
            "Press the Face buttons (X/Square, Circle, Triangle, Cross)",
            "Press the Left Shoulder button (L1)",
            "Press the Right Shoulder button (R1)",
            "Press the Left Trigger button (L2)",
            "Press the Right Trigger button (R2)",
            "Move the Left Stick in all directions",
            "Move the Right Stick in all directions",
            "Press the Left Stick button (L3)",
            "Press the Right Stick button (R3)",
            "Press the Start button",
            "Press the Select button",
            "Press the PS/Xbox button"
        ]
        
        for test_instruction in tests:
            print(f"\n> {test_instruction}")
            test_logger.info(f"INSTRUCTION: {test_instruction}")
            
            # Wait for events for 5 seconds or until user presses Enter
            start_time = time.time()
            while time.time() - start_time < 5:
                try:
                    # Poll for events
                    event = gamepad.read_one()
                    if event:
                        if event.type == ecodes.EV_KEY and event.value == 1:  # Button down
                            btn_name = PS3_BUTTON_MAPPINGS.get(event.code, f"Unknown ({event.code})")
                            test_logger.info(f"TEST - BUTTON - {btn_name} - Pressed - Code: {event.code}")
                            print(f"  Detected: {btn_name} (Code: {event.code})")
                        elif event.type == ecodes.EV_KEY and event.value == 0:  # Button up
                            btn_name = PS3_BUTTON_MAPPINGS.get(event.code, f"Unknown ({event.code})")
                            test_logger.info(f"TEST - BUTTON - {btn_name} - Released - Code: {event.code}")
                        elif event.type == ecodes.EV_ABS and abs(event.value) > 10:  # Axis movement
                            axis_names = {
                                0: "Left Stick X",
                                1: "Left Stick Y",
                                2: "Right Stick X (PS3-Z)",
                                3: "Right Stick Y (PS3-RX)",
                                4: "Right Stick Y (Xbox)",
                                5: "Right Stick X (Xbox)",
                            }
                            axis_name = axis_names.get(event.code, f"Unknown Axis ({event.code})")
                            test_logger.info(f"TEST - AXIS - {axis_name} - Value: {event.value}")
                            if abs(event.value) > 1000:  # Only print significant movements
                                print(f"  Detected: {axis_name} (Value: {event.value})")
                    # Short sleep to avoid CPU thrashing
                    time.sleep(0.01)
                except Exception as e:
                    debug_logger.error(f"Error reading event: {e}")
                    time.sleep(0.01)
            
            # Give feedback
            print("  Moving to next test...")
        
        print("\nController test complete! Results logged to config_debug.log")
        print("Press Enter to continue to normal operation or Ctrl+C to exit...")
        input()
        
    except KeyboardInterrupt:
        print("\nTest mode interrupted by user.")
    except Exception as e:
        import traceback
        print(f"\nError in test mode: {e}")
        traceback.print_exc()
        logger.error(f"Test mode error: {e}")
    
    return

def handle_controller_input(gamepad):
    """Process input from game controller"""
    global hold_state, servo_speed, q_pressed, exit_flag, lock_state
    
    debug_logger.info(f"Controller connected: {gamepad.name} ({controller_type})")
    
    try:
        for event in gamepad.read_loop():
            # Log all controller events for debugging purposes
            log_controller_event(event.type, event.code, event.value)
            
            # Check for exit flag
            if exit_flag:
                break
                
            try:
                # Handle joystick movements
                if event.type == ecodes.EV_ABS:
                    # Left stick
                    if event.code == 0:  # Left Stick X
                        move_servo(0, event.value)
                    elif event.code == 1:  # Left Stick Y
                        move_servo(1, event.value)
                    
                    # Right stick for PS3 controllers
                    if controller_type == 'PS3':
                        if event.code == 2:  # Right Stick X (Z)
                            move_servo(2, event.value)
                        elif event.code == 3:  # Right Stick Y (RX)
                            move_servo(3, event.value)
                    else:  # Xbox
                        if event.code == 5:  # Right Stick X
                            move_servo(3, event.value)
                        elif event.code == 4:  # Right Stick Y
                            move_servo(2, event.value)
                
                # Handle button presses
                elif event.type == ecodes.EV_KEY and event.value == 1:  # Button pressed
                    # Handle PS3 controller buttons
                    if controller_type == 'PS3':
                        if event.code == 304:  # Cross (✕)
                            hold_state[0] = not hold_state[0]
                            print(f"\nServo 0 {'LOCKED' if hold_state[0] else 'UNLOCKED'}")
                        elif event.code == 305:  # Circle (○)
                            hold_state[1] = not hold_state[1]
                            print(f"\nServo 1 {'LOCKED' if hold_state[1] else 'UNLOCKED'}")
                        elif event.code == 308:  # Square (□)
                            hold_state[2] = not hold_state[2]
                            print(f"\nServo 2 {'LOCKED' if hold_state[2] else 'UNLOCKED'}")
                        elif event.code == 307:  # Triangle (△)
                            hold_state[3] = not hold_state[3]
                            print(f"\nServo 3 {'LOCKED' if hold_state[3] else 'UNLOCKED'}")
                        elif event.code == 294:  # L1
                            servo_speed = max(servo_speed - 0.1, 0.1)
                            print(f"\nSpeed decreased to {servo_speed:.1f}x")
                        elif event.code == 295:  # R1
                            servo_speed = min(servo_speed + 0.1, 2.0)
                            print(f"\nSpeed increased to {servo_speed:.1f}x")
                        elif event.code == 298:  # L2
                            move_all_servos(0)
                            print("\nAll servos moved to 0°")
                        elif event.code == 299:  # R2
                            move_all_servos(180)
                            print("\nAll servos moved to 180°")
                        elif event.code == 288:  # Select
                            # Additional function if needed
                            pass
                        elif event.code == 291:  # Start
                            move_all_servos(90)
                            print("\nAll servos moved to 90°")
                        elif event.code == 300:  # D-pad Up
                            move_all_servos(90)
                            print("\nAll servos moved to 90°")
                        elif event.code == 302:  # D-pad Down
                            lock_state = not lock_state
                            status = "LOCKED" if lock_state else "UNLOCKED"
                            print(f"\nServos now {status}")
                        elif event.code == 303:  # D-pad Left
                            move_all_servos(0)
                            print("\nAll servos moved to 0°")
                        elif event.code == 301:  # D-pad Right
                            move_all_servos(180)
                            print("\nAll servos moved to 180°")
                        elif event.code == 292:  # PS Button
                            if q_pressed:
                                print("\nPS button pressed twice. Exiting...")
                                exit_flag = True
                            else:
                                q_pressed = True
                                print("\nPress PS button again to exit...")
                                # Reset q_pressed after 3 seconds
                                threading.Timer(3.0, lambda: setattr(sys.modules[__name__], 'q_pressed', False)).start()
                    else:
                        # Xbox controller buttons
                        if event.code == ecodes.BTN_SOUTH:  # A
                            hold_state[0] = not hold_state[0]
                        elif event.code == ecodes.BTN_EAST:  # B
                            hold_state[1] = not hold_state[1]
                        elif event.code == ecodes.BTN_WEST:  # X
                            hold_state[2] = not hold_state[2]
                        elif event.code == ecodes.BTN_NORTH:  # Y
                            hold_state[3] = not hold_state[3]
                        elif event.code == ecodes.BTN_TL:  # Left Shoulder
                            servo_speed = max(servo_speed - 0.1, 0.1)
                            print(f"\nSpeed decreased to {servo_speed:.1f}x")
                        elif event.code == ecodes.BTN_TR:  # Right Shoulder
                            servo_speed = min(servo_speed + 0.1, 2.0)
                            print(f"\nSpeed increased to {servo_speed:.1f}x")
                        elif event.code == ecodes.BTN_DPAD_UP:  # Up D-pad
                            move_all_servos(90)
                        elif event.code == ecodes.BTN_DPAD_DOWN:  # Down D-pad
                            lock_state = not lock_state
                            status = "LOCKED" if lock_state else "UNLOCKED"
                            print(f"\nServos now {status}")
                        elif event.code == ecodes.BTN_DPAD_LEFT:  # Left D-pad
                            move_all_servos(0)
                        elif event.code == ecodes.BTN_DPAD_RIGHT:  # Right D-pad
                            move_all_servos(180)
                
                # Update display to reflect changes
                display_status()
                
            except Exception as e:
                # Log the error but continue processing events
                logger.error(f"Error processing controller event: {e}")
                debug_logger.error(f"ERROR - {e} - Event: {event}")
    
    except Exception as e:
        logger.error(f"Controller error: {e}")
        print(f"\nController error: {e}")
        exit_flag = True