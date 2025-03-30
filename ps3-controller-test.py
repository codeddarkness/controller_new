#!/usr/bin/env python3

"""
PS3 Controller Mapping Test Tool

This script guides the user through testing PS3 controller buttons in a specific sequence
to verify and debug controller mappings. The program follows the keypress_order.txt file
and logs all button presses for debugging purposes.
"""

import os
import sys
import time
import logging
from datetime import datetime
import argparse

# Try to import evdev
try:
    import evdev
    from evdev import InputDevice, ecodes
    EVDEV_AVAILABLE = True
except ImportError:
    print("Error: Evdev library not found. Please install it with: pip install evdev")
    print("Run this command: sudo pip3 install evdev")
    EVDEV_AVAILABLE = False
    sys.exit(1)

# Terminal colors for better readability
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Configure logging
def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/controller_test_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger('controller_test')
    logger.setLevel(logging.DEBUG)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    print(f"Logging to: {log_file}")
    return logger, log_file

# Find PS3 controller
def find_controller():
    logger.info("Searching for PS3 controller...")
    
    try:
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        
        if not devices:
            logger.error("No input devices found. Is your controller connected?")
            return None
        
        # First try to find a PlayStation controller
        for device in devices:
            device_name = device.name
            logger.info(f"Found device: {device_name} at {device.path}")
            
            if 'PLAYSTATION' in device_name.upper() or 'PS3' in device_name.upper() or 'SONY' in device_name.upper():
                logger.info(f"PlayStation controller found: {device_name}")
                return device
        
        # If no PlayStation controller found, list all and ask user
        print(f"\n{Colors.YELLOW}No PlayStation controller automatically detected.{Colors.ENDC}")
        print("Available input devices:")
        
        for i, device in enumerate(devices):
            print(f"{i+1}. {device.name} ({device.path})")
        
        selection = input("\nEnter device number to use, or 'q' to quit: ")
        if selection.lower() == 'q':
            return None
        
        try:
            index = int(selection) - 1
            if 0 <= index < len(devices):
                selected_device = devices[index]
                logger.info(f"Selected device: {selected_device.name}")
                return selected_device
            else:
                logger.error("Invalid selection.")
                return None
        except ValueError:
            logger.error("Invalid input. Please enter a number.")
            return None
            
    except Exception as e:
        logger.error(f"Error finding controller: {e}")
        return None

# Read keypress order from file
def read_keypress_order(filename="keypress_order.txt"):
    try:
        with open(filename, 'r') as f:
            keypress_order = [line.strip() for line in f if line.strip()]
        return keypress_order
    except FileNotFoundError:
        logger.error(f"File {filename} not found. Creating a default keypress order.")
        
        # Default keypress order
        default_order = [
            "d pad down",
            "d pad right",
            "d pad up",
            "d pad left",
            "left shoulder",
            "left trigger",
            "right shoulder",
            "right trigger",
            "select",
            "start",
            "ps button",
            "square (west)",
            "triangle (north)",
            "circle (east)",
            "X button (south)",
            "left joystick down",
            "left joystick right",
            "left joystick up",
            "left joystick left",
            "right joystick down",
            "right joystick right",
            "right joystick up",
            "right joystick left"
        ]
        
        # Write default order to file
        with open(filename, 'w') as f:
            for item in default_order:
                f.write(f"{item}\n")
        
        logger.info(f"Created default {filename} file.")
        return default_order

# Create a mapping dictionary to store button/axis codes
def create_mapping_file(mapping_data, filename="ps3_controller_mapping.py"):
    button_mappings = {}
    axis_mappings = {}
    
    for entry in mapping_data:
        if entry['type'] == 'button':
            button_mappings[entry['code']] = entry['name']
        elif entry['type'] == 'axis':
            axis_mappings[entry['code']] = entry['name']
    
    # Generate Python code for the mappings
    with open(filename, 'w') as f:
        f.write("# PS3 controller button mappings\n")
        f.write("PS3_BUTTON_MAPPINGS = {\n")
        for code, name in sorted(button_mappings.items()):
            f.write(f"    {code}: \"{name}\",\n")
        f.write("}\n\n")
        
        f.write("# PS3 joystick/axis mappings\n")
        f.write("PS3_AXIS_MAPPINGS = {\n")
        for code, name in sorted(axis_mappings.items()):
            f.write(f"    {code}: \"{name}\",\n")
        f.write("}\n")
    
    logger.info(f"Mapping file generated: {filename}")
    print(f"\n{Colors.GREEN}Controller mapping file created: {filename}{Colors.ENDC}")
    return button_mappings, axis_mappings

# Run the test sequence
def run_test_sequence(controller, keypress_order):
    # Dictionary to store the mappings
    mapping_data = []
    current_test_index = 0
    
    print(f"\n{Colors.HEADER}PS3 Controller Mapping Test{Colors.ENDC}")
    print(f"\nPlease press the following buttons/sticks in order:")
    print(f"{Colors.BLUE}{', '.join(keypress_order)}{Colors.ENDC}")
    
    print(f"\n{Colors.GREEN}Current button to press: {Colors.BOLD}{keypress_order[current_test_index]}{Colors.ENDC}")
    
    # Track the last event to avoid duplicates
    last_event = None
    
    try:
        while current_test_index < len(keypress_order):
            # Listen for events
            timeout = select_timeout(controller, 0.1)  # 100ms timeout
            
            if not timeout:
                # Process events
                for event in controller.read():
                    # Ignore synchronization events
                    if event.type == ecodes.EV_SYN:
                        continue
                    
                    # Only process new events (avoid duplicates from rapid presses)
                    if last_event and event.type == last_event.type and event.code == last_event.code and event.value == last_event.value:
                        continue
                    
                    last_event = event
                    
                    # Log all events
                    logger.debug(f"Event - Type: {event.type}, Code: {event.code}, Value: {event.value}")
                    
                    # Process button presses (EV_KEY) 
                    if event.type == ecodes.EV_KEY and event.value == 1:  # Button press (1 = pressed)
                        button_name = keypress_order[current_test_index]
                        print(f"\n{Colors.YELLOW}Button pressed - Code: {event.code}{Colors.ENDC}")
                        logger.info(f"Button press - Code: {event.code}, Name: {button_name}")
                        
                        # Store the mapping
                        mapping_data.append({
                            'type': 'button',
                            'code': event.code,
                            'name': button_name,
                            'value': event.value
                        })
                        
                        # Move to next button
                        current_test_index += 1
                        if current_test_index < len(keypress_order):
                            print(f"\n{Colors.GREEN}Now press: {Colors.BOLD}{keypress_order[current_test_index]}{Colors.ENDC}")
                        else:
                            print(f"\n{Colors.GREEN}All buttons tested!{Colors.ENDC}")
                        
                    # Process joystick/axis movement (EV_ABS)
                    elif event.type == ecodes.EV_ABS and abs(event.value) > 16000:  # Significant joystick movement
                        if "joystick" in keypress_order[current_test_index]:
                            joystick_name = keypress_order[current_test_index]
                            print(f"\n{Colors.YELLOW}Joystick moved - Axis: {event.code}, Value: {event.value}{Colors.ENDC}")
                            logger.info(f"Joystick movement - Axis: {event.code}, Value: {event.value}, Name: {joystick_name}")
                            
                            # Store the mapping
                            mapping_data.append({
                                'type': 'axis',
                                'code': event.code,
                                'name': joystick_name,
                                'value': event.value
                            })
                            
                            # Move to next input
                            current_test_index += 1
                            if current_test_index < len(keypress_order):
                                print(f"\n{Colors.GREEN}Now press/move: {Colors.BOLD}{keypress_order[current_test_index]}{Colors.ENDC}")
                            else:
                                print(f"\n{Colors.GREEN}All inputs tested!{Colors.ENDC}")
            
            # Short sleep to avoid CPU thrashing
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Test interrupted.{Colors.ENDC}")
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        print(f"\n{Colors.RED}Error: {e}{Colors.ENDC}")
    
    # Generate the mapping file
    if mapping_data:
        button_mappings, axis_mappings = create_mapping_file(mapping_data)
        return button_mappings, axis_mappings, mapping_data
    else:
        logger.warning("No mapping data collected.")
        print(f"\n{Colors.YELLOW}No mapping data was collected.{Colors.ENDC}")
        return {}, {}, []

# Helper function for non-blocking select with timeout
def select_timeout(device, timeout):
    """Wait for input from device with timeout using select."""
    import select
    r, w, x = select.select([device.fd], [], [], timeout)
    return not r  # Return True if timed out, False if there's data

# Run button mapping test
def test_button_mappings(controller, button_mappings, axis_mappings):
    """Test the generated mappings."""
    print(f"\n{Colors.BLUE}Testing Button Mappings{Colors.ENDC}")
    print(f"Press any button to see its mapping. Press Ctrl+C to exit.\n")
    
    # Combine both mappings for lookup
    combined_mappings = {**button_mappings, **axis_mappings}
    
    try:
        for event in controller.read_loop():
            if event.type == ecodes.EV_KEY and event.value == 1:  # Button press
                if event.code in button_mappings:
                    name = button_mappings[event.code]
                    print(f"{Colors.GREEN}Button: {name} (Code: {event.code}){Colors.ENDC}")
                else:
                    print(f"{Colors.YELLOW}Unknown button: Code {event.code}{Colors.ENDC}")
            
            elif event.type == ecodes.EV_ABS and abs(event.value) > 16000:  # Significant axis movement
                if event.code in axis_mappings:
                    name = axis_mappings[event.code]
                    print(f"{Colors.BLUE}Axis: {name} (Code: {event.code}, Value: {event.value}){Colors.ENDC}")
                else:
                    print(f"{Colors.YELLOW}Unknown axis: Code {event.code}, Value: {event.value}{Colors.ENDC}")
    
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}Button mapping test finished.{Colors.ENDC}")
    except Exception as e:
        logger.error(f"Error testing mappings: {e}")
        print(f"\n{Colors.RED}Error: {e}{Colors.ENDC}")

# Print the final report
def print_report(button_mappings, axis_mappings, log_file):
    print(f"\n{Colors.HEADER}PS3 Controller Mapping Report{Colors.ENDC}")
    print(f"\nButton Mappings:")
    for code, name in sorted(button_mappings.items()):
        print(f"  Code {code} → {name}")
    
    print(f"\nAxis Mappings:")
    for code, name in sorted(axis_mappings.items()):
        print(f"  Code {code} → {name}")
    
    print(f"\nLog file: {log_file}")
    print(f"Mapping file: ps3_controller_mapping.py")
    
    print(f"\n{Colors.GREEN}To use these mappings in your code:{Colors.ENDC}")
    print(f"1. Copy ps3_controller_mapping.py to your project directory")
    print(f"2. Import it with: from ps3_controller_mapping import PS3_BUTTON_MAPPINGS, PS3_AXIS_MAPPINGS")
    print(f"3. Use the mappings when processing controller events")

# Main function 
def main():
    parser = argparse.ArgumentParser(description="PS3 Controller Mapping Test Tool")
    parser.add_argument('--test', action='store_true', help='Test existing mappings')
    parser.add_argument('--list', action='store_true', help='List available input devices')
    args = parser.parse_args()
    
    global logger
    logger, log_file = setup_logging()
    
    # List available devices if requested
    if args.list:
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        print("\nAvailable input devices:")
        for i, device in enumerate(devices):
            print(f"{i+1}. {device.name} ({device.path})")
        return
    
    # Find controller
    controller = find_controller()
    if not controller:
        print(f"{Colors.RED}No controller found or selected. Exiting.{Colors.ENDC}")
        return
    
    # Test existing mappings if requested
    if args.test and os.path.exists("ps3_controller_mapping.py"):
        try:
            from ps3_controller_mapping import PS3_BUTTON_MAPPINGS, PS3_AXIS_MAPPINGS
            test_button_mappings(controller, PS3_BUTTON_MAPPINGS, PS3_AXIS_MAPPINGS)
            return
        except ImportError:
            print(f"{Colors.YELLOW}Mapping file not found or contains errors. Proceeding with new mapping.{Colors.ENDC}")
    
    # Read keypress order
    keypress_order = read_keypress_order()
    
    # Run the test sequence
    button_mappings, axis_mappings, mapping_data = run_test_sequence(controller, keypress_order)
    
    # Print report if mappings were generated
    if button_mappings or axis_mappings:
        print_report(button_mappings, axis_mappings, log_file)
        
        # Offer to test the mappings
        test_now = input(f"\n{Colors.BLUE}Do you want to test the mappings now? (y/n): {Colors.ENDC}")
        if test_now.lower() == 'y':
            test_button_mappings(controller, button_mappings, axis_mappings)

if __name__ == "__main__":
    main()
