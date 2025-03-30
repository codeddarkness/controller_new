#!/usr/bin/env python3

"""
PlayStation Controller Debug Patch Script
This script will update your servo_controller.py file to add debugging functionality
that logs controller input events and servo movements to a debug.log file.
"""

import os
import sys
import re
import shutil
from datetime import datetime

# Configuration
TARGET_FILE = "servo_controller.py"
BACKUP_FILE = f"servo_controller.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}.py"

# ANSI colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

# Debug logging code to be added
DEBUG_IMPORTS = """
# Debug logging imports
import logging
from datetime import datetime
"""

DEBUG_SETUP_FUNCTION = """
# Configure logging for controller inputs and servo movements
def setup_debug_logging():
    \"\"\"Set up a dedicated debug logger for controller inputs and servo movements\"\"\"
    # Create a logger for controller inputs
    controller_logger = logging.getLogger('controller_debug')
    controller_logger.setLevel(logging.DEBUG)
    
    # Create file handler for debug.log
    debug_file = logging.FileHandler('debug.log')
    debug_file.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    debug_file.setFormatter(formatter)
    
    # Add handler to logger
    controller_logger.addHandler(debug_file)
    
    return controller_logger

# Initialize the logger
debug_logger = setup_debug_logging()
"""

LOGGING_FUNCTIONS = """
# Debug logging functions
def log_controller_event(event_type, code, value, description=""):
    \"\"\"Log controller events to debug.log\"\"\"
    if event_type == ecodes.EV_KEY:
        # Log button events
        btn_name = "Unknown"
        # For PS3 controllers
        if controller_type == 'PS3':
            ps3_button_names = {
                304: "Cross (✕)",
                305: "Circle (○)",
                307: "Triangle (△)",
                308: "Square (□)",
                294: "L1",
                295: "R1",
                296: "L3",
                297: "R3",
                298: "L2",
                299: "R2",
                288: "Select",
                291: "Start",
                292: "PS Button",
                310: "L1 (alternate)",
                311: "R1 (alternate)",
                312: "L2 (alternate)",
                313: "R2 (alternate)",
                # Add more button mappings as you discover them
            }
            btn_name = ps3_button_names.get(code, f"Unknown ({code})")
        else:
            # For Xbox controllers
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
                # Add more button mappings as needed
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
            # Add more axis mappings as you discover them
        }
        
        axis_name = axis_names.get(code, f"Unknown Axis ({code})")
        debug_logger.info(f"AXIS - {axis_name} - Value: {value}")
    
    # Add additional custom description if provided
    if description:
        debug_logger.info(f"INFO - {description}")

def log_servo_movement(channel, old_angle, new_angle, cause="controller"):
    \"\"\"Log servo movements to debug.log\"\"\"
    if old_angle != new_angle:
        debug_logger.info(f"SERVO - Channel {channel} - Old: {old_angle}° - New: {new_angle}° - Cause: {cause}")
"""

# Modified function patterns and replacements

# Pattern for move_servo function - we'll replace it with a version that includes logging
MOVE_SERVO_PATTERN = r"def move_servo\(channel, value\):[^}]*?servo_positions\[channel\] = angle(?:[^}]*?)display_status\(\)"

# New move_servo function with logging
MOVE_SERVO_REPLACEMENT = """def move_servo(channel, value):
    \"\"\"Move a servo based on joystick input\"\"\"
    global servo_positions, servo_directions, last_activity
    
    if lock_state or hold_state[channel]:
        log_controller_event(None, None, None, f"Servo {channel} movement blocked (lock_state={lock_state}, hold_state={hold_state[channel]})")
        return  # Don't move if locked or held
    
    # Store old position for logging
    old_position = servo_positions[channel]
    
    # Calculate new position
    pwm_value, angle = joystick_to_pwm(value)
    
    # Update direction
    if angle > old_position:
        servo_directions[channel] = "up" if channel in [1, 2] else "right"
    elif angle < old_position:
        servo_directions[channel] = "down" if channel in [1, 2] else "left"
    else:
        servo_directions[channel] = "neutral"
    
    # Move the servo
    if pca_connected and pwm:
        try:
            pwm.set_pwm(channel, 0, pwm_value)
        except Exception as e:
            debug_logger.error(f"ERROR - Failed to set servo {channel}: {e}")
    
    # Update position
    servo_positions[channel] = angle
    last_activity = time.time()
    
    # Log the movement
    log_servo_movement(old_position, angle, "joystick")
    
    # Update display
    display_status()"""

# Pattern for handle_controller_input function - we'll modify it to add logging
HANDLE_CONTROLLER_PATTERN = r"def handle_controller_input\(gamepad\):[^}]*?try:[^}]*?for event in gamepad\.read_loop\(\):"

# New handle_controller_input function beginning with logging
HANDLE_CONTROLLER_REPLACEMENT = """def handle_controller_input(gamepad):
    \"\"\"Process input from game controller with debug logging\"\"\"
    global hold_state, servo_speed, q_pressed, exit_flag
    
    debug_logger.info(f"Controller connected: {gamepad.name} ({controller_type})")
    
    try:
        for event in gamepad.read_loop():
            # Log all controller events
            log_controller_event(event.type, event.code, event.value)
            
            # Check for exit flag
            if exit_flag:
                break"""

# Pattern for move_all_servos function - update to include logging
MOVE_ALL_SERVOS_PATTERN = r"def move_all_servos\(angle\):[^}]*?for channel in SERVO_CHANNELS:[^}]*?set_servo_position\(channel, angle\)"

# New move_all_servos function with logging
MOVE_ALL_SERVOS_REPLACEMENT = """def move_all_servos(angle):
    \"\"\"Move all servos to a specified angle\"\"\"
    global last_activity
    if lock_state:
        return  # Don't move if locked
        
    for channel in SERVO_CHANNELS:
        if not hold_state[channel]:
            # Store old position for logging
            old_position = servo_positions[channel]
            
            # Set the new position
            set_servo_position(channel, angle)
            
            # Log the movement
            log_servo_movement(channel, old_position, angle, "move_all_command")"""

# SixAxis handler to add better PS3 controller support
SIXAXIS_HANDLER = """
# SixAxis PS3 controller helper code
def detect_ps3_controller_variant(gamepad):
    \"\"\"Detect which variant of PS3 controller is connected\"\"\"
    controller_variant = "standard"
    
    # Check if SixAxis daemon is running
    try:
        with open("/proc/modules", "r") as f:
            if "sixad" in f.read():
                controller_variant = "sixaxis"
                debug_logger.info("Detected SixAxis daemon running")
    except:
        pass
    
    # Check connection type
    if "Bluetooth" in connection_type:
        controller_variant = "bluetooth"
    elif "USB" in connection_type:
        controller_variant = "usb"
    
    debug_logger.info(f"PS3 controller variant detected: {controller_variant}")
    return controller_variant
"""

PS3_BUTTON_MAPPING = """
# PS3 controller button mapping (add this near controller handling code)
def get_ps3_button_mapping():
    \"\"\"Get appropriate PS3 button mapping based on connection type\"\"\"
    variant = detect_ps3_controller_variant(gamepad)
    
    # Standard mapping (works for most configurations)
    button_map = {
        # Primary mappings
        304: "Cross",
        305: "Circle",
        307: "Triangle",
        308: "Square",
        294: "L1",
        295: "R1",
        298: "L2",
        299: "R2",
        
        # Alternative mappings (for SixAxis/Bluetooth)
        310: "L1_Alt",
        311: "R1_Alt",
        312: "L2_Alt",
        313: "R2_Alt",
    }
    
    # For special variants, we can adjust the mapping
    if variant == "sixaxis":
        # Add SixAxis-specific mappings
        # These would be determined from debug logs
        pass
        
    debug_logger.info(f"Using PS3 button mapping for variant: {variant}")
    return button_map
"""

def update_file():
    """Update the servo_controller.py file with debug logging"""
    if not os.path.exists(TARGET_FILE):
        print(f"{RED}Error: {TARGET_FILE} not found!{RESET}")
        return False
    
    # Create backup
    try:
        shutil.copy2(TARGET_FILE, BACKUP_FILE)
        print(f"{GREEN}Created backup: {BACKUP_FILE}{RESET}")
    except Exception as e:
        print(f"{RED}Error creating backup: {e}{RESET}")
        return False
    
    # Read the entire file
    try:
        with open(TARGET_FILE, 'r') as file:
            content = file.read()
    except Exception as e:
        print(f"{RED}Error reading {TARGET_FILE}: {e}{RESET}")
        return False
    
    # Step 1: Add imports if they don't exist
    if "import logging" not in content:
        # Find the last import line
        import_lines = re.findall(r'import .*|from .* import .*', content)
        if import_lines:
            last_import = import_lines[-1]
            content = content.replace(last_import, last_import + DEBUG_IMPORTS)
        else:
            # No imports found, add at the beginning
            content = DEBUG_IMPORTS + content
    
    # Step 2: Add debug setup function after global variables
    if "setup_debug_logging" not in content:
        # Find a good place to insert the debug setup - after global variables
        global_vars_pattern = r'# Global variables[^\n]*\n[^#]*?(?=\n\w)'
        global_vars_match = re.search(global_vars_pattern, content, re.DOTALL)
        
        if global_vars_match:
            content = content[:global_vars_match.end()] + DEBUG_SETUP_FUNCTION + content[global_vars_match.end():]
        else:
            # Try another approach - look for commonly defined variables
            app_def_match = re.search(r'app = Flask\(__name__\)', content)
            if app_def_match:
                content = content[:app_def_match.end()] + "\n" + DEBUG_SETUP_FUNCTION + content[app_def_match.end():]
            else:
                # Just add before the first function
                first_func_match = re.search(r'def \w+\(', content)
                if first_func_match:
                    content = content[:first_func_match.start()] + DEBUG_SETUP_FUNCTION + content[first_func_match.start():]
                else:
                    # Just append it (less than ideal)
                    content += "\n" + DEBUG_SETUP_FUNCTION
    
    # Step 3: Add logging functions
    if "log_controller_event" not in content:
        # Find a good spot - before the first function that might use these
        func_pattern = r'def (move_servo|handle_controller_input|set_servo_position)'
        func_match = re.search(func_pattern, content)
        
        if func_match:
            content = content[:func_match.start()] + LOGGING_FUNCTIONS + "\n\n" + content[func_match.start():]
        else:
            # Add before main function
            main_match = re.search(r'def main\(\):', content)
            if main_match:
                content = content[:main_match.start()] + LOGGING_FUNCTIONS + "\n\n" + content[main_match.start():]
            else:
                # Just append it (less than ideal)
                content += "\n" + LOGGING_FUNCTIONS
    
    # Step 4: Replace move_servo function
    if "log_servo_movement" not in content and "move_servo" in content:
        content = re.sub(MOVE_SERVO_PATTERN, MOVE_SERVO_REPLACEMENT, content)
    
    # Step 5: Update handle_controller_input function
    if "handle_controller_input" in content:
        content = re.sub(HANDLE_CONTROLLER_PATTERN, HANDLE_CONTROLLER_REPLACEMENT, content)
    
    # Step 6: Update move_all_servos function
    if "move_all_servos" in content:
        content = re.sub(MOVE_ALL_SERVOS_PATTERN, MOVE_ALL_SERVOS_REPLACEMENT, content)
    
    # Step 7: Add SixAxis handler close to controller detection
    if "detect_ps3_controller_variant" not in content:
        # Find the controller detection code
        find_controller_match = re.search(r'def find_\w*controller\(', content)
        if find_controller_match:
            content = content[:find_controller_match.start()] + SIXAXIS_HANDLER + "\n\n" + content[find_controller_match.start():]
        else:
            # Add near the handle_controller_input function
            handle_match = re.search(r'def handle_controller_input\(', content)
            if handle_match:
                content = content[:handle_match.start()] + SIXAXIS_HANDLER + "\n\n" + content[handle_match.start():]
    
    # Step 8: Add PS3 button mapping function
    if "get_ps3_button_mapping" not in content:
        handle_match = re.search(r'def handle_controller_input\(', content)
        if handle_match:
            content = content[:handle_match.start()] + PS3_BUTTON_MAPPING + "\n\n" + content[handle_match.start():]
    
    # Write the updated content
    try:
        with open(TARGET_FILE, 'w') as file:
            file.write(content)
        print(f"{GREEN}Successfully updated {TARGET_FILE} with debug logging!{RESET}")
        return True
    except Exception as e:
        print(f"{RED}Error writing to {TARGET_FILE}: {e}{RESET}")
        return False

def main():
    """Main function"""
    print(f"{GREEN}====================================={RESET}")
    print(f"{GREEN} PS3 Controller Debug Patch Utility {RESET}")
    print(f"{GREEN}====================================={RESET}")
    print("")
    print("This script will update your servo_controller.py file to add:")
    print("- Detailed controller input logging to debug.log")
    print("- Servo movement tracking")
    print("- Better PS3 controller support")
    print("")
    
    if not os.path.exists(TARGET_FILE):
        print(f"{RED}Error: {TARGET_FILE} not found in current directory!{RESET}")
        print(f"Make sure you run this script from the same directory as {TARGET_FILE}")
        return False
    
    proceed = input(f"Proceed with updating {TARGET_FILE}? (y/n): ")
    if proceed.lower() != 'y':
        print("Update cancelled.")
        return False
    
    if update_file():
        print("")
        print(f"{GREEN}Update completed successfully!{RESET}")
        print(f"A backup was created at: {BACKUP_FILE}")
        print("")
        print("To test the debug logging:")
        print(f"1. Run your controller application: {GREEN}python3 {TARGET_FILE}{RESET}")
        print(f"2. Connect your PS3 controller and press all buttons, especially L1/R1/L2/R2")
        print(f"3. Check the debug.log file to see which button codes are being detected")
        print("")
        print(f"{YELLOW}Note: If you encounter any issues, you can restore from the backup:{RESET}")
        print(f"  cp {BACKUP_FILE} {TARGET_FILE}")
        return True
    else:
        print(f"{RED}Update failed.{RESET}")
        return False

if __name__ == "__main__":
    main()

