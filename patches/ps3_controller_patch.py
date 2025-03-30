#!/usr/bin/env python3

"""
PS3 Controller Patch Script - Fixed

This script will update your servo_controller.py file with proper PS3 controller
button mappings based on the test log data, with correct string formatting.
"""

import os
import sys
import re
import shutil
from datetime import datetime

# ANSI colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

# Target file
TARGET_FILE = "servo_controller.py"
BACKUP_DIR = "backups"
BACKUP_FILE = f"{BACKUP_DIR}/servo_controller.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}.py"

# Updated PS3 controller button mappings based on test log
PS3_BUTTON_MAPPINGS_CODE = """
# PS3 controller button mappings based on test log
PS3_BUTTON_MAPPINGS = {
    # Face buttons
    304: "Cross (✕)",     # X button
    305: "Circle (○)",    # Circle
    307: "Triangle (△)",  # Triangle 
    308: "Square (□)",    # Square
    
    # Shoulder/trigger buttons
    294: "L1",            # Left shoulder
    295: "R1",            # Right shoulder
    298: "L2",            # Left trigger
    299: "R2",            # Right trigger
    
    # D-pad buttons
    300: "D-Pad Up",      # D-pad up
    301: "D-Pad Right",   # D-pad right
    302: "D-Pad Down",    # D-pad down
    303: "D-Pad Left",    # D-pad left
    
    # Other buttons
    288: "Select",        # Select button
    291: "Start",         # Start button
    292: "PS Button",     # PS Button
    293: "Unknown (293)", # Unknown button
    296: "L3",            # Left stick press
    297: "R3"             # Right stick press
}
"""

# Updated controller handler function with fixed string literals
CONTROLLER_HANDLER_CODE = """
def handle_controller_input(gamepad):
    \"\"\"Process input from game controller\"\"\"
    global hold_state, servo_speed, q_pressed, exit_flag, lock_state
    
    debug_logger.info(f"Controller connected: {gamepad.name} ({controller_type})")
    
    try:
        for event in gamepad.read_loop():
            # Log all controller events
            log_controller_event(event.type, event.code, event.value)
            
            # Check for exit flag
            if exit_flag:
                break
                
            try:
                # Handle joystick movements
                if event.type == ecodes.EV_ABS:
                    # Left stick
                    if event.code == 0:  # Left Stick X
                        move_servo(0, event.value)
                    elif event.code == 1:  # Left Stick Y
                        move_servo(1, event.value)
                    
                    # Right stick for PS3 controllers
                    if controller_type == 'PS3':
                        if event.code == 2:  # Right Stick X (Z)
                            move_servo(2, event.value)
                        elif event.code == 3:  # Right Stick Y (RX)
                            move_servo(3, event.value)
                    else:  # Xbox
                        if event.code == 5:  # Right Stick X
                            move_servo(3, event.value)
                        elif event.code == 4:  # Right Stick Y
                            move_servo(2, event.value)
                
                # Handle button presses
                elif event.type == ecodes.EV_KEY and event.value == 1:  # Button pressed
                    # Handle PS3 controller buttons based on test log
                    if controller_type == 'PS3':
                        if event.code == 304:  # Cross (✕)
                            hold_state[0] = not hold_state[0]
                        elif event.code == 305:  # Circle (○)
                            hold_state[1] = not hold_state[1]
                        elif event.code == 308:  # Square (□)
                            hold_state[2] = not hold_state[2]
                        elif event.code == 307:  # Triangle (△)
                            hold_state[3] = not hold_state[3]
                        elif event.code == 294:  # L1
                            servo_speed = max(servo_speed - 0.1, 0.1)
                            print(f"Speed decreased to {servo_speed:.1f}x")
                        elif event.code == 295:  # R1
                            servo_speed = min(servo_speed + 0.1, 2.0)
                            print(f"Speed increased to {servo_speed:.1f}x")
                        elif event.code == 298:  # L2
                            move_all_servos(0)
                        elif event.code == 299:  # R2
                            move_all_servos(180)
                        elif event.code == 288:  # Select
                            # Additional function if needed
                            pass
                        elif event.code == 291:  # Start
                            move_all_servos(90)
                        elif event.code == 300:  # D-pad Up
                            move_all_servos(90)
                        elif event.code == 302:  # D-pad Down
                            lock_state = not lock_state
                            status = "LOCKED" if lock_state else "UNLOCKED"
                            print(f"Servos now {status}")
                        elif event.code == 303:  # D-pad Left
                            move_all_servos(0)
                        elif event.code == 301:  # D-pad Right
                            move_all_servos(180)
                        elif event.code == 292:  # PS Button
                            if q_pressed:
                                print("PS button pressed twice. Exiting...")
                                exit_flag = True
                                break
                            else:
                                q_pressed = True
                                print("Press PS button again to exit...")
                    else:
                        # Xbox controller buttons
                        if event.code == ecodes.BTN_SOUTH:  # A
                            hold_state[0] = not hold_state[0]
                        elif event.code == ecodes.BTN_EAST:  # B
                            hold_state[1] = not hold_state[1]
                        elif event.code == ecodes.BTN_WEST:  # X
                            hold_state[2] = not hold_state[2]
                        elif event.code == ecodes.BTN_NORTH:  # Y
                            hold_state[3] = not hold_state[3]
                        elif event.code == ecodes.BTN_TL:  # Left Shoulder
                            servo_speed = max(servo_speed - 0.1, 0.1)
                            print(f"Speed decreased to {servo_speed:.1f}x")
                        elif event.code == ecodes.BTN_TR:  # Right Shoulder
                            servo_speed = min(servo_speed + 0.1, 2.0)
                            print(f"Speed increased to {servo_speed:.1f}x")
                        elif event.code == ecodes.BTN_DPAD_UP:  # Up D-pad
                            move_all_servos(90)
                        elif event.code == ecodes.BTN_DPAD_DOWN:  # Down D-pad
                            lock_state = not lock_state
                            status = "LOCKED" if lock_state else "UNLOCKED"
                            print(f"Servos now {status}")
                        elif event.code == ecodes.BTN_DPAD_LEFT:  # Left D-pad
                            move_all_servos(0)
                        elif event.code == ecodes.BTN_DPAD_RIGHT:  # Right D-pad
                            move_all_servos(180)
                        elif event.code == ecodes.KEY_Q:  # Q key for exit
                            if q_pressed:
                                print("Q pressed twice. Exiting...")
                                exit_flag = True
                                break
                            else:
                                q_pressed = True
                                print("Press Q again to exit...")
                
                # Update display to reflect changes
                display_status()
                
            except Exception as e:
                # Log the error but continue processing events
                logger.error(f"Error processing controller event: {e}")
                debug_logger.error(f"ERROR - {e} - Event: {event}")
    
    except Exception as e:
        logger.error(f"Controller error: {e}")
        print(f"Controller error: {e}")
        exit_flag = True
"""

def backup_file():
    """Create a backup of the target file"""
    # Ensure backup directory exists
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    # Create backup
    shutil.copy2(TARGET_FILE, BACKUP_FILE)
    print(f"{GREEN}Created backup: {BACKUP_FILE}{RESET}")

def update_file():
    """Update the servo_controller.py file with PS3 controller mappings"""
    # Read the file
    with open(TARGET_FILE, 'r') as file:
        content = file.read()
    
    # Add button mappings if needed
    mappings_added = False
    if "PS3_BUTTON_MAPPINGS" not in content:
        # Find a good spot to add mappings - after global variables
        global_vars_pattern = r'# Global variables.*?lock_state\s*=\s*False'
        match = re.search(global_vars_pattern, content, re.DOTALL)
        
        if match:
            insertion_point = match.end()
            content = content[:insertion_point] + "\n" + PS3_BUTTON_MAPPINGS_CODE + content[insertion_point:]
            mappings_added = True
        else:
            print(f"{YELLOW}Could not find global variables section to add PS3 button mappings.{RESET}")
    else:
        print(f"{YELLOW}PS3_BUTTON_MAPPINGS already exists, will not add again.{RESET}")
        
    # Replace controller handler function
    handle_controller_pattern = r'def handle_controller_input\(gamepad\):.*?exit_flag = True'
    
    # Use re.DOTALL to match across multiple lines
    if re.search(handle_controller_pattern, content, re.DOTALL):
        content = re.sub(handle_controller_pattern, CONTROLLER_HANDLER_CODE.strip(), content, flags=re.DOTALL)
        print(f"{GREEN}Updated handle_controller_input function.{RESET}")
    else:
        print(f"{YELLOW}Could not find handle_controller_input function to replace.{RESET}")

    # Write updated content
    with open(TARGET_FILE, 'w') as file:
        file.write(content)
        
    print(f"{GREEN}Successfully updated {TARGET_FILE} with PS3 controller mappings.{RESET}")

def main():
    """Main function"""
    print(f"{GREEN}====================================={RESET}")
    print(f"{GREEN} PS3 Controller Patch Script {RESET}")
    print(f"{GREEN}====================================={RESET}")
    
    # Check if target file exists
    if not os.path.exists(TARGET_FILE):
        print(f"{RED}Error: {TARGET_FILE} not found!{RESET}")
        return False
    
    print(f"This script will update {TARGET_FILE} with the correct PS3 controller mappings.")
    print(f"A backup will be created at {BACKUP_FILE}")
    
    proceed = input(f"Proceed with the update? (y/n): ")
    if proceed.lower() != 'y':
        print("Update cancelled.")
        return False
    
    # Create backup
    backup_file()
    
    # Update file
    update_file()
    
    print(f"\n{GREEN}Update completed successfully!{RESET}")
    print(f"The script has been updated with the correct PS3 controller mappings based on your test log.")
    print(f"\nIf you encounter any issues, you can restore from the backup:")
    print(f"  cp {BACKUP_FILE} {TARGET_FILE}")
    
    return True

if __name__ == "__main__":
    main()

