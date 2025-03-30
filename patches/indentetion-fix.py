#!/usr/bin/env python3

"""
Servo Controller IndentationError Fix Script

This script will patch your servo_controller.py file to fix the indentation error
at line 716 by cleaning up duplicated handler code.
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

def create_backup():
    """Create a backup of the target file"""
    # Ensure backup directory exists
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    # Create backup
    shutil.copy2(TARGET_FILE, BACKUP_FILE)
    print(f"{GREEN}Created backup: {BACKUP_FILE}{RESET}")

def fix_indentation_error():
    """Fix the indentation error by removing duplicated code"""
    try:
        # Read the current file
        with open(TARGET_FILE, 'r') as f:
            content = f.read()
        
        # Find duplicated controller handler function
        # The pattern looks for multiple implementations that are causing conflicts
        pattern = r'def handle_controller_input\(gamepad\):.*?exit_flag = True(\s+break\s+.*?)\s+else:.*?exit_flag = True'
        
        # Replace with a clean implementation
        fixed_content = re.sub(pattern, 
        """def handle_controller_input(gamepad):
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
        exit_flag = True""", 
        content, 
        flags=re.DOTALL)
        
        # Write the fixed file
        with open(TARGET_FILE, 'w') as f:
            f.write(fixed_content)
        
        print(f"{GREEN}Successfully fixed indentation error in {TARGET_FILE}{RESET}")
        return True
    except Exception as e:
        print(f"{RED}Error fixing indentation: {e}{RESET}")
        return False

def main():
    """Main function to fix indentation error"""
    print(f"{GREEN}====================================={RESET}")
    print(f"{GREEN} Servo Controller Indentation Fix {RESET}")
    print(f"{GREEN}====================================={RESET}")
    
    # Check if target file exists
    if not os.path.exists(TARGET_FILE):
        print(f"{RED}Error: {TARGET_FILE} not found!{RESET}")
        return False
    
    print(f"This script will fix the indentation error at line 716 in {TARGET_FILE}.")
    confirm = input("Proceed with the fix? (y/n): ")
    if confirm.lower() != 'y':
        print("Fix cancelled.")
        return False
    
    # Create backup
    create_backup()
    
    # Fix indentation error
    if fix_indentation_error():
        print(f"\n{GREEN}Indentation error fixed successfully!{RESET}")
        print(f"A backup was created at: {BACKUP_FILE}")
        print(f"\nYou can now run: python3 {TARGET_FILE}")
        return True
    else:
        print(f"\n{RED}Failed to fix indentation error.{RESET}")
        print(f"Try restoring from backup: cp {BACKUP_FILE} {TARGET_FILE}")
        return False

if __name__ == "__main__":
    main()

