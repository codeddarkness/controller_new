#!/usr/bin/env python3

"""
PS3 Controller Event Logger
A standalone tool to log all events from a PlayStation 3 controller
without modifying your existing servo controller code.

Run this script to capture all controller events to debug.log.
"""

import evdev
import time
import logging
from datetime import datetime
import sys
import os

# ANSI colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

# Configure logging
def setup_logging():
    logger = logging.getLogger('ps3_controller_debug')
    logger.setLevel(logging.DEBUG)
    
    # Create console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    
    # Create file handler
    file_handler = logging.FileHandler('debug.log')
    file_handler.setLevel(logging.DEBUG)
    
    # Create formatters
    console_formatter = logging.Formatter('%(message)s')
    file_formatter = logging.Formatter('%(asctime)s - %(message)s')
    
    # Add formatters to handlers
    console.setFormatter(console_formatter)
    file_handler.setFormatter(file_formatter)
    
    # Add handlers to logger
    logger.addHandler(console)
    logger.addHandler(file_handler)
    
    return logger

# Find PlayStation controller
def find_ps3_controller():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    
    # First try to find an exact "PlayStation" match
    for device in devices:
        if 'PLAYSTATION' in device.name or 'PlayStation' in device.name:
            return device
    
    # If no PlayStation controller found, list all available devices
    if devices:
        print(f"\n{YELLOW}No PlayStation controller found. Available devices:{RESET}")
        for i, device in enumerate(devices):
            print(f"{i+1}. {device.name} ({device.path})")
        
        # Let user select a device
        try:
            choice = int(input("Select device number to use (or 0 to quit): "))
            if choice > 0 and choice <= len(devices):
                return devices[choice-1]
        except:
            pass
        
    return None

# Button and axis name dictionaries
ps3_button_names = {
    304: "Cross (✕)",
    305: "Circle (○)",
    307: "Triangle (△)",
    308: "Square (□)",
    310: "L1",
    311: "R1",
    312: "L2",
    313: "R2",
    294: "L1 (alt)",
    295: "R1 (alt)",
    298: "L2 (alt)",
    299: "R2 (alt)",
    288: "Select",
    289: "L3",
    290: "R3",
    291: "Start",
    292: "PS Button",
    # D-pad buttons might be here or as axes
    544: "D-pad",
    704: "PS Button (alt)",
    # Add more as discovered
}

ps3_axis_names = {
    0: "Left Stick X",
    1: "Left Stick Y",
    2: "Right Stick X",
    3: "Right Stick Y",
    4: "L2 Trigger",
    5: "R2 Trigger",
    16: "D-pad X",
    17: "D-pad Y",
    # Add more as discovered
}

def log_events(device, logger):
    print(f"{GREEN}Logging controller events to debug.log{RESET}")
    print(f"Controller: {device.name} at {device.path}")
    print(f"Press Ctrl+C to stop logging")
    print(f"\n{YELLOW}---- Controller Events ----{RESET}")
    
    # Log device info
    logger.info(f"DEVICE - {device.name} - {device.path}")
    
    # Get device capabilities
    caps = device.capabilities(verbose=True)
    logger.info(f"CAPABILITIES - {caps}")
    
    try:
        button_count = 0
        for event in device.read_loop():
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            if event.type == evdev.ecodes.EV_KEY:
                button_name = ps3_button_names.get(event.code, f"Button {event.code}")
                state = "Pressed" if event.value == 1 else "Released" if event.value == 0 else "Held"
                message = f"BUTTON - {button_name} - {state} - Code: {event.code}"
                print(f"{timestamp} - {message}")
                logger.info(message)
                button_count += 1
                
            elif event.type == evdev.ecodes.EV_ABS:
                axis_name = ps3_axis_names.get(event.code, f"Axis {event.code}")
                message = f"AXIS - {axis_name} - Value: {event.value}"
                print(f"{timestamp} - {message}")
                logger.info(message)
                
            # Stop after 500 events to prevent log file from growing too large
            if button_count > 500:
                logger.info("Reached maximum events. Stopping logging.")
                break
                
    except KeyboardInterrupt:
        print(f"\n{GREEN}Logging stopped.{RESET}")
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")

def detect_ps3_connection_type(controller):
    """Try to detect if controller is connected via USB, Bluetooth or SixAxis"""
    connection_type = "Unknown"
    
    # Check if it's connected via USB
    sys_path = controller.path.split('/')[-1]
    usb_path = f"/sys/class/input/{sys_path}/device"
    
    if os.path.exists(usb_path):
        # Try to determine if it's USB or Bluetooth
        try:
            device_path = os.readlink(usb_path)
            if 'usb' in device_path.lower():
                connection_type = "USB"
            elif 'bluetooth' in device_path.lower():
                connection_type = "Bluetooth"
        except:
            pass
    
    # Check if sixad daemon is running
    try:
        with open("/proc/modules", "r") as f:
            if "sixad" in f.read():
                if connection_type == "Bluetooth":
                    connection_type = "SixAxis Bluetooth"
                else:
                    connection_type = "SixAxis"
    except:
        pass
    
    return connection_type

def main():
    print(f"{GREEN}====================================={RESET}")
    print(f"{GREEN} PlayStation Controller Event Logger {RESET}")
    print(f"{GREEN}====================================={RESET}")
    
    # Setup logging
    logger = setup_logging()
    
    # Find PS3 controller
    controller = find_ps3_controller()
    if not controller:
        print(f"{RED}No controller found. Exiting.{RESET}")
        return False
    
    # Detect connection type
    connection_type = detect_ps3_connection_type(controller)
    print(f"Connection type: {connection_type}")
    logger.info(f"CONNECTION - Type: {connection_type}")
    
    # Log controller events
    log_events(controller, logger)
    
    print(f"\n{GREEN}Logging completed.{RESET}")
    print(f"Debug log saved to: {os.path.abspath('debug.log')}")
    print(f"\nView the log file to see all controller events and button codes.")
    
    return True

if __name__ == "__main__":
    main()

