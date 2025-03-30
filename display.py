#!/usr/bin/env python3
"""
Console display functionality for servo controller.
"""

import sys
from config import DIRECTION_ARROWS
from hardware import get_hardware_status
from controller_input import get_controller_status

def get_direction_arrow(direction):
    """Get arrow character based on direction"""
    return DIRECTION_ARROWS.get(direction, "○")

def update_display():
    """Update console display with current status"""
    # Clear the line (carriage return without newline)
    sys.stdout.write("\r" + " " * 120 + "\r")
    
    # Get current status
    hw_status = get_hardware_status()
    controller_status = get_controller_status()
    
    # Hardware status strings
    pca_status = "CONNECTED" if hw_status['pca']['connected'] else "DISCONNECTED"
    mpu_status = "CONNECTED" if hw_status['mpu']['connected'] else "DISCONNECTED"
    ctrl_status = controller_status['type'] if controller_status['connected'] else "DISCONNECTED"
    
    # Servo status
    servo_text = ""
    for ch in hw_status['servos']['positions']:
        arrow = get_direction_arrow(hw_status['servos']['directions'][ch])
        lock = "L" if hw_status['servos']['hold_state'][ch] else " "
        servo_text += f"S{ch}:{arrow}{hw_status['servos']['positions'][ch]:3}°{lock} "
    
    # MPU data
    mpu_text = ""
    mpu_data = hw_status['mpu']['data']
    ax = get_direction_arrow(mpu_data['direction']['x'])
    ay = get_direction_arrow(mpu_data['direction']['y'])
    az = get_direction_arrow(mpu_data['direction']['z'])
    mpu_text = f"Accel: X:{ax}{mpu_data['accel']['x']:5.1f} Y:{ay}{mpu_data['accel']['y']:5.1f} Z:{az}{mpu_data['accel']['z']:5.1f}"
    
    # Full hardware status
    hw_text = f"PCA:{pca_status}({hw_status['pca']['bus']}) MPU:{mpu_status}({hw_status['mpu']['bus']}) Ctrl:{ctrl_status} Spd:{hw_status['servos']['speed']:.1f}x"
    
    # Combine all text
    status_text = f"{servo_text} | {mpu_text} | {hw_text}"
    sys.stdout.write(status_text)
    sys.stdout.flush()
