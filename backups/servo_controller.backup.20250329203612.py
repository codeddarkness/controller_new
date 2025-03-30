#!/usr/bin/env python3

import json
import signal
import sys
import time
import threading
import os
import argparse
import evdev
from evdev import InputDevice, ecodes
from flask import Flask, render_template, jsonify, request
import logging
from datetime import datetime
import math
import sqlite3
from sqlite3 import Error

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
I2C_BUSES = [0, 1]  # I2C buses to check

# Global variables
hold_state = {0: False, 1: False, 2: False, 3: False}
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
        print(f"Database error: {e}")
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
        print(f"Logging error: {e}")

def detect_i2c_devices():
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
                print(f"PCA9685 found on I2C bus {bus_num}")
            except Exception as e:
                print(f"PCA9685 not found on I2C bus {bus_num}: {e}")
        
        # Try to initialize MPU6050 on this bus
        if MPU6050_AVAILABLE and not mpu_connected:
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
        print(f"Error finding controller: {e}")
    
    print("No game controller found. Using keyboard or web interface.")
    return None

def joystick_to_pwm(value):
    """Convert joystick value (-32767 to 32767) to servo pulse and angle"""
    angle = int(((value + 32767) / 65534) * 180)  # Normalize to 0-180 degrees
    pwm_value = int(SERVO_MIN + (angle / 180.0) * (SERVO_MAX - SERVO_MIN))
    return pwm_value, angle

def set_servo_position(channel, angle):
    """Set a servo to a specific angle (0-180)"""
    global servo_positions, servo_directions
    
    if channel not in SERVO_CHANNELS:
        return False
    
    # Update direction
    if angle > servo_positions[channel]:
        servo_directions[channel] = "up" if channel in [1, 2] else "right"
    elif angle < servo_positions[channel]:
        servo_directions[channel] = "down" if channel in [1, 2] else "left"
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
            print(f"Error setting servo {channel}: {e}")
    
    # Update position
    servo_positions[channel] = angle
    return True

def move_servo(channel, value):
    """Move a servo based on joystick input"""
    if hold_state[channel]:
        return  # Don't move if hold is active
    
    _, angle = joystick_to_pwm(value)
    set_servo_position(channel, angle)

def move_all_servos(angle):
    """Move all servos to a specified angle"""
    for channel in SERVO_CHANNELS:
        if not hold_state[channel]:
            set_servo_position(channel, angle)

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
            print(f"Error reading MPU data: {e}")
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

def handle_controller_input(gamepad):
    """Process input from game controller"""
    global hold_state, servo_speed, q_pressed, exit_flag
    
    try:
        for event in gamepad.read_loop():
            # Check for exit flag
            if exit_flag:
                break
                
            # Handle joystick movements for both Xbox and PS3
            if event.type == ecodes.EV_ABS:
                # Left stick
                if event.code == 0:  # ABS_X - Left Stick X
                    move_servo(0, event.value)
                elif event.code == 1:  # ABS_Y - Left Stick Y
                    move_servo(1, event.value)
                
                # Right stick - different mapping for PS3/Xbox
                if controller_type == 'PS3':
                    if event.code == 2:  # ABS_Z - Right Stick X
                        move_servo(2, event.value)
                    elif event.code == 3:  # ABS_RX - Right Stick Y
                        move_servo(3, event.value)
                else:  # Xbox
                    if event.code == ecodes.ABS_RX:  # Right Stick X
                        move_servo(3, event.value)
                    elif event.code == ecodes.ABS_RY:  # Right Stick Y
                        move_servo(2, event.value)
                
                # Handle D-pad for PS3
                if controller_type == 'PS3':
                    if event.code == 16:  # D-pad X axis
                        if event.value == -1:  # D-pad left
                            servo_speed = max(servo_speed - 0.1, 0.1)
                        elif event.value == 1:  # D-pad right
                            servo_speed = min(servo_speed + 0.1, 2.0)
                    elif event.code == 17:  # D-pad Y axis
                        if event.value == -1:  # D-pad up
                            move_all_servos(90)
                        elif event.value == 1:  # D-pad down
                            move_all_servos(0)
            
            # Handle button presses
            elif event.type == ecodes.EV_KEY and event.value == 1:  # Button pressed
                if controller_type == 'PS3':
                    # PS3 button mappings from observed codes
                    if event.code == 304:  # Cross - A 
                        hold_state[0] = not hold_state[0]
                    elif event.code == 305:  # Circle - B
                        hold_state[1] = not hold_state[1]
                    elif event.code == 308:  # Square - X
                        hold_state[2] = not hold_state[2]
                    elif event.code == 307:  # Triangle - Y
                        hold_state[3] = not hold_state[3]
                    elif event.code == 294:  # L1
                        servo_speed = max(servo_speed - 0.1, 0.1)
                    elif event.code == 295:  # R1
                        servo_speed = min(servo_speed + 0.1, 2.0)
                    elif event.code == 298:  # L2
                        move_all_servos(0)
                    elif event.code == 299:  # R2
                        move_all_servos(180)
                else:  # Xbox controller
                    # Standard button mappings
                    if event.code == ecodes.BTN_SOUTH:  # A
                        hold_state[0] = not hold_state[0]
                    elif event.code == ecodes.BTN_EAST:  # B
                        hold_state[1] = not hold_state[1]
                    elif event.code == ecodes.BTN_WEST:  # X
                        hold_state[2] = not hold_state[2]
                    elif event.code == ecodes.BTN_NORTH:  # Y
                        hold_state[3] = not hold_state[3]
                    elif event.code == ecodes.BTN_TL:  # Left shoulder
                        servo_speed = max(servo_speed - 0.1, 0.1)
                    elif event.code == ecodes.BTN_TR:  # Right shoulder
                        servo_speed = min(servo_speed + 0.1, 2.0)
                    elif event.code == ecodes.BTN_DPAD_LEFT:
                        move_all_servos(0)
                    elif event.code == ecodes.BTN_DPAD_RIGHT:
                        move_all_servos(180)
                    elif event.code == ecodes.BTN_DPAD_UP:
                        move_all_servos(90)
                
                # Check for 'Q' key on any controller
                if event.code == ecodes.KEY_Q:
                    if q_pressed:
                        print("\nQ pressed twice. Exiting...")
                        exit_flag = True
                        break
                    else:
                        q_pressed = True
                        print("\nPress Q again to exit...")
                
    except Exception as e:
        print(f"\nController error: {e}")
        exit_flag = True

def update_thread():
    """Thread for updating sensor data and display"""
    global exit_flag
    
    while not exit_flag:
        # Update MPU data
        update_mpu_data()
        
        # Display status
        display_status()
        
        # Log data to the database (lower frequency to avoid overwhelming the DB)
        if int(time.time()) % 5 == 0:  # Log every 5 seconds
            log_data()
        
        # Sleep to control update rate
        time.sleep(0.1)

def exit_handler(signal_received=None, frame=None):
    """Handle program exit gracefully"""
    global exit_flag
    
    print("\nExiting program.")
    exit_flag = True
    
    # Turn off all servos
    if pca_connected and pwm:
        pwm.set_all_pwm(0, 0)
    
    # Exit after a short delay to allow threads to close
    time.sleep(0.5)
    sys.exit(0)

# Flask routes for web interface
@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('servo_controller.html')

@app.route('/api/status')
def get_status():
    """API endpoint to get current status"""
    status = {
        'servos': {
            'positions': servo_positions,
            'hold_states': hold_state,
            'directions': servo_directions,
            'speed': servo_speed
        },
        'mpu': mpu_data,
        'hardware': {
            'pca_connected': pca_connected,
            'pca_bus': pca_bus,
            'mpu_connected': mpu_connected,
            'mpu_bus': mpu_bus,
            'controller_connected': controller_connected,
            'controller_type': controller_type
        }
    }
    return jsonify(status)

@app.route('/api/servo/<int:channel>', methods=['POST'])
def control_servo(channel):
    """API endpoint to control a servo"""
    if channel not in SERVO_CHANNELS:
        return jsonify({'error': 'Invalid channel'}), 400
    
    data = request.get_json()
    if not data or 'angle' not in data:
        return jsonify({'error': 'Missing angle parameter'}), 400
    
    try:
        angle = int(data['angle'])
        set_servo_position(channel, angle)
        return jsonify({'success': True, 'channel': channel, 'angle': angle})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servo/all', methods=['POST'])
def control_all_servos():
    """API endpoint to control all servos"""
    data = request.get_json()
    if not data or 'angle' not in data:
        return jsonify({'error': 'Missing angle parameter'}), 400
    
    try:
        angle = int(data['angle'])
        move_all_servos(angle)
        return jsonify({'success': True, 'angle': angle})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servo/hold/<int:channel>', methods=['POST'])
def toggle_hold(channel):
    """API endpoint to toggle servo hold state"""
    if channel not in SERVO_CHANNELS:
        return jsonify({'error': 'Invalid channel'}), 400
    
    try:
        data = request.get_json()
        if data and 'hold' in data:
            hold_state[channel] = bool(data['hold'])
        else:
            hold_state[channel] = not hold_state[channel]
        
        return jsonify({'success': True, 'channel': channel, 'hold': hold_state[channel]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def get_logs():
    """API endpoint to get log data"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the most recent 100 log entries
        cursor.execute("SELECT * FROM servo_logs ORDER BY id DESC LIMIT 100")
        rows = cursor.fetchall()
        
        logs = []
        for row in rows:
            log_entry = {
                'id': row[0],
                'timestamp': row[1],
                'servo_data': json.loads(row[2]),
                'mpu_data': json.loads(row[3]),
                'hardware_status': json.loads(row[4])
            }
            logs.append(log_entry)
        
        conn.close()
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def start_web_server():
    """Start the Flask web server"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def main():
    """Main function"""
    global exit_flag
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Servo Controller with MPU6050')
    parser.add_argument('--web-only', action='store_true', help='Run in web interface mode only')
    args = parser.parse_args()
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, exit_handler)
    
    # Set up database
    setup_database()
    
    # Detect I2C devices
    detect_i2c_devices()
    
    print("Servo Controller")
    print("---------------")
    print(f"PCA9685: {'Connected on bus ' + str(pca_bus) if pca_connected else 'Not connected'}")
    print(f"MPU6050: {'Connected on bus ' + str(mpu_bus) if mpu_connected else 'Not connected'}")
    
    # Find game controller if not in web-only mode
    gamepad = None
    if not args.web_only:
        gamepad = find_game_controller()
    
    # Start update thread for sensors and display
    update_thread_handle = threading.Thread(target=update_thread)
    update_thread_handle.daemon = True
    update_thread_handle.start()
    
    # Start web server in a separate thread
    web_thread = threading.Thread(target=start_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    print("Web interface available at http://localhost:5000/")
    print("Press Ctrl+C to exit or press 'q' twice")
    
    # Start controller input handling if available and not in web-only mode
    if gamepad and not args.web_only:
        handle_controller_input(gamepad)
    else:
        # Just keep the main thread alive
        while not exit_flag:
            time.sleep(0.1)
    
    # Clean exit
    exit_handler()

if __name__ == "__main__":
    main()
