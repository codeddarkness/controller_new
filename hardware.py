#!/usr/bin/env python3
"""
Hardware interface for PCA9685 servo controller and MPU6050 sensor.
"""

import math
import time
from config import SERVO_MIN, SERVO_MAX, SERVO_FREQ, I2C_BUSES, SERVO_CHANNELS, DIRECTION_ARROWS
from logger import main_logger

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

# Global hardware state
pca_connected = False
mpu_connected = False
pca_bus = None
mpu_bus = None
pwm = None
mpu = None

# Servo state
servo_positions = {0: 90, 1: 90, 2: 90, 3: 90}
servo_directions = {0: "neutral", 1: "neutral", 2: "neutral", 3: "neutral"}
hold_state = {0: False, 1: False, 2: False, 3: False}
lock_state = False
servo_speed = 1.0

# MPU data
mpu_data = {
    'accel': {'x': 0, 'y': 0, 'z': 0},
    'gyro': {'x': 0, 'y': 0, 'z': 0},
    'temp': 0,
    'direction': {'x': "neutral", 'y': "neutral", 'z': "neutral"}
}

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
                main_logger.info(f"PCA9685 found on I2C bus {bus_num}")
            except Exception as e:
                print(f"PCA9685 not found on I2C bus {bus_num}: {e}")
                main_logger.warning(f"PCA9685 not found on I2C bus {bus_num}: {e}")
        
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
                main_logger.info(f"MPU6050 found on I2C bus {bus_num}")
            except Exception as e:
                print(f"MPU6050 not found on I2C bus {bus_num}: {e}")
                main_logger.warning(f"MPU6050 not found on I2C bus {bus_num}: {e}")
    
    # If hardware is still not connected, set up simulation
    if not pca_connected:
        print("No PCA9685 found. Running servo control in simulation mode.")
        main_logger.warning("No PCA9685 found. Running servo control in simulation mode.")
    
    if not mpu_connected:
        print("No MPU6050 found. Running MPU in simulation mode.")
        main_logger.warning("No MPU6050 found. Running MPU in simulation mode.")
    
    return pca_connected, mpu_connected

def joystick_to_angle(value):
    """Convert joystick value (-32767 to 32767) to angle (0-180)"""
    angle = int(((value + 32767) / 65534) * 180)  # Normalize to 0-180 degrees
    return angle

def angle_to_pwm(angle):
    """Convert angle (0-180) to PWM pulse length"""
    # Constrain the angle
    angle = max(0, min(180, angle))
    
    # Calculate pulse length
    pulse = int(SERVO_MIN + (angle / 180.0) * (SERVO_MAX - SERVO_MIN))
    return pulse

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
    
    # Calculate and set the pulse
    pulse = angle_to_pwm(angle)
    
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
    global servo_positions, servo_directions
    
    if lock_state or hold_state[channel]:
        return  # Don't move if locked or held
    
    # Store old position for logging
    old_position = servo_positions[channel]
    
    # Convert joystick value to servo position
    angle = joystick_to_angle(value)
    
    # Set servo position
    set_servo_position(channel, angle)
    
    # Return old and new positions for logging
    return old_position, angle

def move_all_servos(angle):
    """Move all servos to a specified angle"""
    global servo_positions
    
    if lock_state:
        return  # Don't move if locked
    
    # Store results for logging
    results = {}
    
    # Move each servo that isn't on hold
    for channel in SERVO_CHANNELS:
        if not hold_state[channel]:
            old_position = servo_positions[channel]
            set_servo_position(channel, angle)
            results[channel] = (old_position, angle)
    
    return results

def stop_all_servos():
    """Stop all servos (turn off PWM)"""
    if pca_connected and pwm:
        pwm.set_all_pwm(0, 0)
        main_logger.info("All servos stopped")

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
    
    return mpu_data

def get_hardware_status():
    """Get current hardware status"""
    return {
        'pca': {
            'connected': pca_connected,
            'bus': pca_bus
        },
        'mpu': {
            'connected': mpu_connected,
            'bus': mpu_bus,
            'data': mpu_data
        },
        'servos': {
            'positions': servo_positions,
            'directions': servo_directions,
            'hold_state': hold_state,
            'lock_state': lock_state,
            'speed': servo_speed
        }
    }
