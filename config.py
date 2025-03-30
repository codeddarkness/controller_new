#!/usr/bin/env python3
"""
Configuration settings for the servo controller.
"""

# Servo configuration
SERVO_MIN = 150  # Min pulse length (0 degrees)
SERVO_MAX = 600  # Max pulse length (180 degrees)
SERVO_FREQ = 50  # PWM frequency for servos (50Hz standard)
SERVO_CHANNELS = [0, 1, 2, 3]  # Servo channels to control

# I2C configuration
I2C_BUSES = [0, 1]  # I2C buses to check

# Database configuration
DB_PATH = 'servo_data.db'

# PS3 controller button mappings based on test log
PS3_BUTTON_MAPPINGS = {
    294: "L1",          # Left shoulder
    295: "R1",          # Right shoulder
    298: "L2",          # Left trigger
    299: "R2",          # Right trigger
    292: "PS Button",   # PS button
    300: "D-Pad Up",    # D-pad buttons
    301: "D-Pad Right",
    302: "D-Pad Down",
    303: "D-Pad Left",
    304: "Cross (✕)",   # Face buttons
    305: "Circle (○)",
    307: "Triangle (△)",
    308: "Square (□)",
    288: "Select",      # Other buttons
    291: "Start",
    296: "L3",          # Left stick press
    297: "R3",          # Right stick press
    293: "Unknown (293)"# Unknown button
}

# PS3 joystick/axis mappings
PS3_AXIS_MAPPINGS = {
    0: "Left Stick X",
    1: "Left Stick Y",
    2: "Right Stick X (PS3-Z)",
    3: "Right Stick Y (PS3-RX)",
    4: "Right Stick Y (Xbox)",
    5: "Right Stick X (Xbox)",
    16: "D-pad X",
    17: "D-pad Y",
}

# Direction arrows for display
DIRECTION_ARROWS = {
    "up": "↑", 
    "down": "↓",
    "left": "←", 
    "right": "→",
    "neutral": "○"
}

# Web server settings
WEB_HOST = '0.0.0.0'
WEB_PORT = 5000
