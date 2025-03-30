#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

# ANSI colors for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header():
    """Print setup header"""
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}{GREEN}         Servo Controller Setup{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}\n")

def check_python_version():
    """Check if Python version is 3.6 or higher"""
    if sys.version_info < (3, 6):
        print(f"{RED}Error: Python 3.6 or higher is required.{RESET}")
        sys.exit(1)
    print(f"{GREEN}✓ Python version check passed.{RESET}")

def install_packages():
    """Install required packages"""
    print(f"{BOLD}Installing required packages...{RESET}")
    required_packages = [
        "evdev",
        "adafruit-pca9685",
        "flask",
        "mpu6050-raspberrypi"
    ]
    
    # Install system dependencies first
    try:
        print(f"{YELLOW}Checking/installing system dependencies...{RESET}")
        subprocess.check_call(["sudo", "apt-get", "update", "-qq"])
        subprocess.check_call(["sudo", "apt-get", "install", "-y", "python3-pip", "python3-dev", "i2c-tools"])
        print(f"{GREEN}✓ System dependencies installed.{RESET}")
    except subprocess.CalledProcessError:
        print(f"{YELLOW}Warning: Failed to install system dependencies. Continuing with Python packages...{RESET}")
    
    # Install Python packages
    for package in required_packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", package])
            print(f"{GREEN}✓ {package} installed successfully{RESET}")
        except subprocess.CalledProcessError:
            print(f"{YELLOW}Warning: Failed to install {package}. Some functionality may be limited.{RESET}")

def setup_systemd_service():
    """Create systemd service for auto-start on boot (Raspberry Pi)"""
    print("Setting up systemd service...")
    
    service_content = """[Unit]
Description=Servo Controller Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 {}/servo_controller.py
WorkingDirectory={}
StandardOutput=inherit
StandardError=inherit
Restart=always
User={}

[Install]
WantedBy=multi-user.target
""".format(os.getcwd(), os.getcwd(), os.getenv('USER', 'pi'))
    
    service_path = "/tmp/servo-controller.service"
    
    try:
        with open(service_path, "w") as f:
            f.write(service_content)
        
        # Copy to systemd directory and enable
        subprocess.call(["sudo", "cp", service_path, "/etc/systemd/system/"])
        subprocess.call(["sudo", "systemctl", "daemon-reload"])
        subprocess.call(["sudo", "systemctl", "enable", "servo-controller.service"])
        
        print("Systemd service installed. To start the service, run:")
        print("  sudo systemctl start servo-controller.service")
        print("To enable auto-start on boot, run:")
        print("  sudo systemctl enable servo-controller.service")
    except Exception as e:
        print(f"Failed to set up systemd service: {e}")
        print("You can manually start the application with: python3 servo_controller.py")

def enable_i2c():
    """Try to enable I2C if running on Raspberry Pi"""
    try:
        # Check if we're on a Raspberry Pi
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()
        
        if "Raspberry Pi" in cpuinfo or "BCM" in cpuinfo:
            print(f"{BOLD}Raspberry Pi detected. Enabling I2C...{RESET}")
            
            # Check if I2C is already enabled
            with open("/boot/config.txt", "r") as f:
                config = f.read()
            
            if "dtparam=i2c_arm=on" not in config:
                # Enable I2C
                try:
                    subprocess.check_call(["sudo", "raspi-config", "nonint", "do_i2c", "0"])
                    print(f"{GREEN}✓ I2C enabled successfully.{RESET}")
                    print(f"{YELLOW}Note: A reboot may be required for I2C to work.{RESET}")
                except subprocess.CalledProcessError:
                    print(f"{YELLOW}Warning: Failed to enable I2C automatically.{RESET}")
                    print("Please enable it manually using raspi-config:")
                    print("  sudo raspi-config")
                    print("  Navigate to: Interface Options > I2C > Enable")
            else:
                print(f"{GREEN}✓ I2C is already enabled.{RESET}")
            
            # Check if I2C devices are detectable
            try:
                i2c_output = subprocess.check_output(["i2cdetect", "-y", "1"]).decode()
                print("\nI2C Device Scan Results:")
                print(i2c_output)
                
                # Common I2C addresses
                if "68" in i2c_output:
                    print(f"{GREEN}✓ MPU6050 likely detected at address 0x68{RESET}")
                if "40" in i2c_output:
                    print(f"{GREEN}✓ PCA9685 likely detected at address 0x40{RESET}")
                
                if "68" not in i2c_output and "40" not in i2c_output:
                    print(f"{YELLOW}No servo controller or IMU devices detected. Check connections.{RESET}")
            except Exception as e:
                print(f"{YELLOW}Could not scan I2C bus: {e}{RESET}")
        else:
            print(f"{YELLOW}This does not appear to be a Raspberry Pi. Skipping I2C setup.{RESET}")
    except Exception as e:
        print(f"{YELLOW}Could not check/enable I2C: {e}{RESET}")
        print("If running on Raspberry Pi, please enable I2C manually using raspi-config.")

def setup_database():
    """Create an empty database file"""
    print("Setting up database...")
    
    # Import sqlite3 to create the initial database
    import sqlite3
    
    db_path = 'servo_data.db'
    
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
            )''')
        
        conn.commit()
        print(f"Database created at {db_path}")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def create_application_files():
    """Create application files"""
    print(f"{BOLD}Creating application files...{RESET}")
    
    # Create a basic HTML file - this will be replaced by the full implementation
    print("Creating templates directory...")
    os.makedirs("templates", exist_ok=True)
    print(f"{GREEN}✓ Templates directory created{RESET}")
    
    # Check if the files already exist and ask before overwriting
    servo_controller_exists = os.path.exists("servo_controller.py")
    template_exists = os.path.exists("templates/servo_controller.html")
    
    if servo_controller_exists or template_exists:
        print(f"{YELLOW}Warning: Some application files already exist.{RESET}")
        overwrite = input("Do you want to overwrite existing files? (y/n): ").lower()
        if overwrite != 'y':
            print("Skipping file creation.")
            return
    
    # Create placeholder files
    print("Creating servo_controller.py placeholder...")
    with open("servo_controller.py", "w") as f:
        f.write('''#!/usr/bin/env python3

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

# This is a placeholder file. Please copy the full implementation.
def main():
    print("This is a placeholder file. Please replace with the full implementation.")
    print("See the README for instructions.")

if __name__ == "__main__":
    main()
''')
    os.chmod("servo_controller.py", 0o755)  # Make executable
    print(f"{GREEN}✓ servo_controller.py placeholder created{RESET}")
    
    print("Creating templates/servo_controller.html placeholder...")
    with open("templates/servo_controller.html", "w") as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Servo Controller</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            text-align: center;
        }
        .warning {
            color: red;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>Servo Controller</h1>
    <p class="warning">This is a placeholder page.</p>
    <p>Please deploy the full application for the complete interface.</p>
    <p>See the README for instructions.</p>
</body>
</html>
''')
    print(f"{GREEN}✓ HTML template placeholder created{RESET}")
    
    # Create README
    print("Creating README.md...")
    with open("README.md", "w") as f:
        f.write('''# Servo Controller

A web-based interface for controlling servos with PlayStation or Xbox controllers.

## Features

- Control 4 servos using a PlayStation 3 or Xbox controller
- Web interface with circular sliders for manual control
- MPU6050 accelerometer/gyroscope integration
- Real-time status display in both console and web interface
- JSON-formatted logging of all data

## Hardware Requirements

- Raspberry Pi (or similar Linux computer)
- PCA9685 16-channel servo controller
- MPU6050 gyroscope/accelerometer
- 4 servo motors (MG996R recommended)
- PlayStation 3 or Xbox controller (wired or wireless)

## Installation

1. Run the setup script:
   ```
   python3 setup.py
   ```

2. Copy the full implementation files:
   - Replace `servo_controller.py` with the full implementation
   - Replace `templates/servo_controller.html` with the full implementation

3. Start the application:
   ```
   python3 servo_controller.py
   ```

4. Access the web interface at:
   ```
   http://localhost:5000/
   ```

## Usage

- **Console Interface**: Shows real-time status in a single line
- **Web Interface**: Provides circular sliders and status displays
- **Controller**: Use PlayStation 3 or Xbox controller for servo control

## Controller Mappings

### PlayStation 3 Controller
- Left Stick X-axis: Servo 0 (Left/Right)
- Left Stick Y-axis: Servo 1 (Up/Down)
- Right Stick X-axis: Servo 2 (Up/Down)
- Right Stick Y-axis: Servo 3 (Left/Right)
- Cross Button: Toggle Servo 0 lock
- Circle Button: Toggle Servo 1 lock
- Square Button: Toggle Servo 2 lock
- Triangle Button: Toggle Servo 3 lock
- L1: Decrease speed
- R1: Increase speed
- L2: Move all servos to 0°
- R2: Move all servos to 180°

### Xbox Controller
- Left Stick X-axis: Servo 0 (Left/Right)
- Left Stick Y-axis: Servo 1 (Up/Down)
- Right Stick Y-axis: Servo 2 (Up/Down)
- Right Stick X-axis: Servo 3 (Left/Right)
- A Button: Toggle Servo 0 lock
- X Button: Toggle Servo 1 lock
- B Button: Toggle Servo 2 lock
- Y Button: Toggle Servo 3 lock
- Left Shoulder: Decrease speed
- Right Shoulder: Increase speed
- D-pad Left: Move all servos to 0°
- D-pad Right: Move all servos to 180°
- D-pad Up: Move all servos to 90°

## License

This software is provided as-is, without any warranties.
''')
    print(f"{GREEN}✓ README.md created{RESET}")
    
    print(f"{BOLD}Application files created.{RESET}")
    print("Please copy the full implementation files to complete the setup.")