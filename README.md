# Servo Controller for Raspberry Pi

A comprehensive servo control system for Raspberry Pi, supporting PlayStation 3 and Xbox controllers.

## Features

- Support for both PS3 and Xbox controllers
- Control up to 4 servos using the PCA9685 PWM controller
- Motion sensing with MPU6050 (optional)
- Hardware testing and diagnostics
- Controller button mapping testing
- Automatic device detection
- Data logging to SQLite database
- Simple status display in console

## Hardware Requirements

- Raspberry Pi (any model with I2C support)
- PCA9685 PWM controller board
- Servo motors (up to 4)
- PlayStation 3 or Xbox controller (wired or bluetooth)
- MPU6050 accelerometer/gyroscope (optional)

## Software Dependencies

Install the required Python libraries:

```bash
# Update system packages
sudo apt update
sudo apt upgrade

# Install required system dependencies
sudo apt install -y python3-pip python3-dev i2c-tools joystick

# Enable I2C if not already enabled
sudo raspi-config nonint do_i2c 0

# Install Python libraries
sudo pip3 install evdev
sudo pip3 install Adafruit_PCA9685
sudo pip3 install mpu6050-raspberrypi
```

## Controller Setup

For PS3 controllers, you can use the included `ps3_controller_setup.sh` script to set up your controller:

```bash
chmod +x ps3_controller_setup.sh
sudo ./ps3_controller_setup.sh
```

## Usage

### Basic Usage

```bash
# Run the controller with auto-detection
sudo python3 servo_controller.py

# Specify a controller device
sudo python3 servo_controller.py --device /dev/input/event3
```

### Command Line Options

- `--help`, `-h`: Show help message
- `--test-hardware`: Run hardware diagnostic tests
- `--test-controller`: Run controller button mapping test
- `--device PATH`: Specify a controller device path
- `--list-devices`: List available input devices
- `--web-only`: Run in web interface mode only

### Control Mappings

#### Joysticks

| Joystick      | Function                            |
|---------------|-------------------------------------|
| Left Stick X  | Control Servo Channel 0             |
| Left Stick Y  | Control Servo Channel 1             |
| Right Stick X | Control Servo Channel 2             |
| Right Stick Y | Control Servo Channel 3             |

#### PS3 Controller Buttons

| Button          | Function                        |
|-----------------|----------------------------------|
| Cross (✕)       | Toggle hold for Servo 0         |
| Circle (○)      | Toggle hold for Servo 1         |
| Square (□)      | Toggle hold for Servo 2         |
| Triangle (△)    | Toggle hold for Servo 3         |
| L1              | Decrease servo speed            |
| R1              | Increase servo speed            |
| L2              | Move all servos to 0°           |
| R2              | Move all servos to 180°         |
| D-pad Up        | Move all servos to 90°          |
| D-pad Down      | Toggle lock for all servos      |
| D-pad Left      | Move all servos to 0°           |
| D-pad Right     | Move all servos to 180°         |
| Select          | Function available for custom use|
| Start           | Move all servos to 90°          |
| PS Button (2x)  | Exit program                    |

#### Xbox Controller Buttons

| Button              | Function                        |
|---------------------|----------------------------------|
| A                   | Toggle hold for Servo 0         |
| X                   | Toggle hold for Servo 1         |
| B                   | Toggle hold for Servo 2         |
| Y                   | Toggle hold for Servo 3         |
| Left Shoulder (LB)  | Decrease servo speed            |
| Right Shoulder (RB) | Increase servo speed            |
| Left Trigger (LT)   | Move all servos to 0°           |
| Right Trigger (RT)  | Move all servos to 180°         |
| D-pad Up            | Move all servos to 90°          |
| D-pad Down          | Toggle lock for all servos      |
| D-pad Left          | Move all servos to 0°           |
| D-pad Right         | Move all servos to 180°         |
| Select/Back         | Function available for custom use|
| Start               | Move all servos to 90°          |
| Xbox Button (2x)    | Exit program                    |

## Console Display

The console display shows a compact, single-line status of all system components:

- Servo positions with direction indicators (→,←,↑,↓,○)
- Servo lock status
- MPU6050 accelerometer data with direction indicators
- Hardware connection status
- Controller type
- Servo speed setting

Example:
```
S0:→45°  S1:↑90°  S2:○180°L S3:↓30°  | MPU:X:→0.5 Y:↑0.3 Z:○9.8 | PCA:ON MPU:ON Ctrl:PS3 Spd:1.0x
```

## Testing Features

### Controller Testing

Run the controller test mode to identify and verify button/axis mappings:

```bash
sudo python3 servo_controller.py --test-controller
```

This will guide you through pressing different buttons and moving joysticks to verify proper functionality and log the button codes for debugging.

### Hardware Testing

Run comprehensive hardware tests for all components:

```bash
sudo python3 servo_controller.py --test-hardware
```

This will test:
- I2C bus connectivity
- PCA9685 connection and functionality
- MPU6050 sensor (if available)
- Controller connection
- Servo movement on all channels

## Logging

The program maintains several log files:

- `logs/servo_controller.log`: Main application logs
- `logs/debug.log`: Detailed operational logs
- `logs/config_debug.log`: Controller testing logs

Data is also stored in an SQLite database (`servo_data.db`) with the following tables:
- `servo_logs`: Periodic logs of servo positions, MPU data, and hardware status
- `test_results`: Results from hardware and controller tests

## Troubleshooting

### Controller Not Detected

1. Check if the controller is properly connected or paired
2. Use `--list-devices` to see available input devices:
   ```bash
   sudo python3 servo_controller.py --list-devices
   ```
3. Specify the device path manually:
   ```bash
   sudo python3 servo_controller.py --device /dev/input/eventX
   ```

### PCA9685 or MPU6050 Not Detected

1. Check I2C connections and power
2. Verify I2C is enabled on your Raspberry Pi:
   ```bash
   sudo raspi-config
   ```
3. Check I2C devices:
   ```bash
   sudo i2cdetect -y 1
   ```

### Permission Issues

If you get permission errors, make sure to run the script with sudo:
```bash
sudo python3 servo_controller.py
```

## Extending the Project

### Adding More Servos

Edit the `SERVO_CHANNELS` constant in the code to include additional servo channels (the PCA9685 supports up to 16).

### Custom Button Mappings

Modify the button mappings in the code:
- `PS3_BUTTON_MAPPINGS` for PS3 controllers
- `XBOX_BUTTON_MAPPINGS` for Xbox controllers

## License

This project is released under the MIT License.

## Acknowledgments

- The Adafruit PCA9685 library for servo control
- The MPU6050 library for motion sensing
- The evdev library for controller input
