#!/usr/bin/env python3
"""
Controller input handling for servo controller.
"""

import evdev
from evdev import InputDevice, ecodes
import time
import sys

from config import PS3_BUTTON_MAPPINGS, PS3_AXIS_MAPPINGS
from logger import main_logger, debug_logger
from hardware import (
    move_servo, 
    move_all_servos, 
    servo_speed, 
    hold_state, 
    lock_state
)

# Controller state
controller_type = None
controller_connected = False
q_pressed = False
exit_flag = False

def find_game_controller(device_path=None):
    """Find and return a PlayStation or Xbox controller device"""
    global controller_type, controller_connected
    
    try:
        if device_path:
            # Use specified device path
            try:
                device = InputDevice(device_path)
                if 'PLAYSTATION' in device.name or 'PlayStation' in device.name:
                    controller_type = 'PS3' if '3' in device.name else 'PS'
                    controller_connected = True
                    return device
                elif 'Xbox' in device.name:
                    controller_type = 'Xbox'
                    controller_connected = True
                    return device
                else:
                    controller_type = 'Generic'
                    controller_connected = True
                    main_logger.info(f"Generic controller found: {device.name}")
                    return device
            except Exception as e:
                main_logger.error(f"Error using specified device: {e}")
                print(f"Could not open specified device {device_path}: {e}")
        
        # Auto-detect controller
        devices = [InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            if 'PLAYSTATION(R)3' in device.name or 'PlayStation 3' in device.name:
                controller_type = 'PS3'
                controller_connected = True
                main_logger.info(f"PS3 controller found: {device.name}")
                return device
            elif 'PLAYSTATION' in device.name or 'PlayStation' in device.name:
                controller_type = 'PS'
                controller_connected = True
                main_logger.info(f"PlayStation controller found: {device.name}")
                return device
            elif 'Xbox' in device.name:
                controller_type = 'Xbox'
                controller_connected = True
                main_logger.info(f"Xbox controller found: {device.name}")
                return device
    except Exception as e:
        main_logger.error(f"Error finding controller: {e}")
    
    main_logger.warning("No game controller found")
    print("No game controller found. Using keyboard or web interface.")
    return None

def log_controller_event(event_type, code, value, description=""):
    """Log controller events to debug.log"""
    try:
        if event_type == ecodes.EV_KEY:
            # Log button events
            btn_name = "Unknown"
            if controller_type == 'PS3' or controller_type == 'PS':
                btn_name = PS3_BUTTON_MAPPINGS.get(code, f"Unknown ({code})")
            else:
                # Xbox button names
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
                }
                btn_name = btn_names.get(code, f"Unknown ({code})")
            
            btn_state = "Pressed" if value == 1 else "Released" if value == 0 else "Held"
            debug_logger.info(f"BUTTON - {btn_name} - {btn_state} - Code: {code}")
            
        elif event_type == ecodes.EV_ABS:
            # Log joystick/axis events
            axis_name = PS3_AXIS_MAPPINGS.get(code, f"Unknown Axis ({code})")
            debug_logger.info(f"AXIS - {axis_name} - Value: {value}")
        
        # Add additional custom description if provided
        if description:
            debug_logger.info(f"INFO - {description}")
    except Exception as e:
        main_logger.error(f"Error logging controller event: {e}")

def handle_controller_input(gamepad):
    """Process input from game controller"""
    global servo_speed, q_pressed, exit_flag, lock_state, hold_state
    
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
                    if controller_type == 'PS3' or controller_type == 'PS':
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
                    if controller_type == 'PS3' or controller_type == 'PS':
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
                            print(f"\nSpeed decreased to {servo_speed:.1f}x")
                        elif event.code == 295:  # R1
                            servo_speed = min(servo_speed + 0.1, 2.0)
                            print(f"\nSpeed increased to {servo_speed:.1f}x")
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
                            print(f"\nServos now {status}")
                        elif event.code == 303:  # D-pad Left
                            move_all_servos(0)
                        elif event.code == 301:  # D-pad Right
                            move_all_servos(180)
                        elif event.code == 292:  # PS Button
                            if q_pressed:
                                print("\nPS button pressed twice. Exiting...")
                                exit_flag = True
                            else:
                                q_pressed = True
                                print("\nPress PS button again to exit...")
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
                            print(f"\nSpeed decreased to {servo_speed:.1f}x")
                        elif event.code == ecodes.BTN_TR:  # Right Shoulder
                            servo_speed = min(servo_speed + 0.1, 2.0)
                            print(f"\nSpeed increased to {servo_speed:.1f}x")
                        elif event.code == ecodes.BTN_DPAD_UP:  # Up D-pad
                            move_all_servos(90)
                        elif event.code == ecodes.BTN_DPAD_DOWN:  # Down D-pad
                            lock_state = not lock_state
                            status = "LOCKED" if lock_state else "UNLOCKED"
                            print(f"\nServos now {status}")
                        elif event.code == ecodes.BTN_DPAD_LEFT:  # Left D-pad
                            move_all_servos(0)
                        elif event.code == ecodes.BTN_DPAD_RIGHT:  # Right D-pad
                            move_all_servos(180)
                        elif event.code == ecodes.KEY_Q:  # Q key for exit
                            if q_pressed:
                                print("\nQ pressed twice. Exiting...")
                                exit_flag = True
                            else:
                                q_pressed = True
                                print("\nPress Q again to exit...")
                
                # Update display
                from display import update_display
                update_display()
                
            except Exception as e:
                # Log the error but continue processing events
                main_logger.error(f"Error processing controller event: {e}")
                debug_logger.error(f"ERROR - {e} - Event: {event}")
    
    except Exception as e:
        main_logger.error(f"Controller error: {e}")
        print(f"\nController error: {e}")
        exit_flag = True
        
def list_available_controllers():
    """List all available input devices"""
    print("Available input devices:")
    for i, path in enumerate(evdev.list_devices()):
        try:
            device = evdev.InputDevice(path)
            print(f"  {i+1}. {path}: {device.name}")
        except:
            print(f"  {i+1}. {path}: [Error accessing device]")
    print("")

def get_controller_status():
    """Get current controller status"""
    return {
        'connected': controller_connected,
        'type': controller_type,
        'exit_flag': exit_flag
    }
