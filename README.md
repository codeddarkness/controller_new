# Servo Controller Project

## Overview

This project provides a web-based and controller-based interface for controlling four servo motors using a Raspberry Pi with a PCA9685 servo driver and an MPU6050 accelerometer/gyroscope. It supports PlayStation 3 and Xbox controllers, as well as a browser-based interface.

## Features

- **Multi-controller support**: Works with PlayStation 3 and Xbox controllers
- **Web Interface**: Control servos from any browser on your network
- **Accelerometer data**: Monitor MPU6050 motion sensor data in real-time
- **Servo position locking**: Lock individual servos in place
- **Database logging**: Log all servo movements and sensor data
- **Debug mode**: Runs in simulation mode if hardware isn't available

## Hardware Requirements

- Raspberry Pi (3/4/Zero W recommended)
- PCA9685 16-channel servo controller
- MPU6050 accelerometer/gyroscope
- 4 servo motors
- PlayStation 3 or Xbox controller (USB or Bluetooth)

## Installation

1. **Install required packages**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-dev i2c-tools joystick
   pip3 install flask evdev adafruit-pca9685 mpu6050-raspberrypi
   ```

2. **Enable I2C on your Raspberry Pi**:
   ```bash
   sudo raspi-config
   # Navigate to Interface Options → I2C → Enable
   ```

3. **Test I2C connection**:
   ```bash
   sudo i2cdetect -y 1
   # You should see devices at address 0x40 (PCA9685) and 0x68 (MPU6050)
   ```

4. **Clone or download this repository**:
   ```bash
   git clone https://github.com/username/controller_new.git
   cd controller_new
   ```

5. **Run the fix script if needed**:
   ```bash
   python3 code-fix-script.py
   ```

## Usage

### Starting the Controller

Basic usage:
```bash
python3 servo_controller.py
```

With specific controller device:
```bash
python3 servo_controller.py --device /dev/input/event0
```

Web interface only (no controller):
```bash
python3 servo_controller.py --web-only
```

Test controller buttons and mapping:
```bash
python3 servo_controller.py --test-controller
```

### Controller Mappings

#### PlayStation 3 Controller

- **Left Stick X**: Servo 0 (Left/Right)
- **Left Stick Y**: Servo 1 (Up/Down)
- **Right Stick X**: Servo 2 (Left/Right)
- **Right Stick Y**: Servo 3 (Up/Down)
- **Cross (✕)**: Toggle Servo 0 lock
- **Circle (○)**: Toggle Servo 1 lock
- **Square (□)**: Toggle Servo 2 lock
- **Triangle (△)**: Toggle Servo 3 lock
- **L1**: Decrease servo speed
- **R1**: Increase servo speed
- **L2**: Move all servos to 0°
- **R2**: Move all servos to 180°
- **D-Pad Up**: Move all servos to 90°
- **D-Pad Down**: Toggle global lock
- **D-Pad Left**: Move all servos to 0°
- **D-Pad Right**: Move all servos to 180°
- **PS Button** (double-press): Exit program

#### Xbox Controller

- **Left Stick X**: Servo 0
- **Left Stick Y**: Servo 1
- **Right Stick Y**: Servo 2
- **Right Stick X**: Servo 3
- **A Button**: Toggle Servo 0 lock
- **B Button**: Toggle Servo 1 lock
- **X Button**: Toggle Servo 2 lock
- **Y Button**: Toggle Servo 3 lock
- **Left Shoulder**: Decrease speed
- **Right Shoulder**: Increase speed
- **D-pad Left**: Move all servos to 0°
- **D-pad Right**: Move all servos to 180°
- **D-pad Up**: Move all servos to 90°
- **D-pad Down**: Toggle global lock

### Web Interface

The web interface is available at:
```
http://[your-raspberry-pi-ip]:5000/
```

Features:
- Circular sliders for each servo
- Real-time MPU6050 data display
- Hardware status monitoring
- System logs viewer

## Troubleshooting

### Controller Issues

1. **Controller not detected**:
   - Check if the controller is powered on
   - Try a different USB port
   - List available devices: `python3 servo_controller.py --list`
   - Specify device manually: `python3 servo_controller.py --device /dev/input/event0`

2. **Wrong button mapping**:
   - Run test mode: `python3 servo_controller.py --test-controller`
   - Check debug.log and config_debug.log for button codes
   - Update PS3_BUTTON_MAPPINGS in the code if needed

### Hardware Issues

1. **PCA9685 not detected**:
   - Check I2C connections and addresses: `sudo i2cdetect -y 1`
   - Verify that I2C is enabled: `sudo raspi-config`
   - Check power supply to PCA9685

2. **MPU6050 not working**:
   - Check I2C connections
   - Verify address (usually 0x68)
   - Try different I2C bus if available

### Web Interface Issues

1. **Can't access web interface**:
   - Check that the Flask server started successfully
   - Verify your Raspberry Pi's IP address: `hostname -I`
   - Check for firewall issues: `sudo ufw status`

## File Structure

- `servo_controller.py` - Main application file
- `templates/servo_controller.html` - Web interface template
- `debug.log` - Controller input logging
- `config_debug.log` - Controller testing logs
- `servo_data.db` - SQLite database for data logging
- `backups/` - Automatic backups of the main script

## Credits & License

This project is available under the MIT License.

Created for educational and hobby purposes.
