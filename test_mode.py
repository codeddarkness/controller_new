#!/usr/bin/env python3
"""
Controller test functionality for PS3 controller.
"""

import time
import sys
from evdev import ecodes

from logger import main_logger, test_logger
from config import PS3_BUTTON_MAPPINGS, PS3_AXIS_MAPPINGS
from controller_input import controller_type

def run_controller_test_mode(gamepad):
    """Interactive controller test mode"""
    print("\nEntering Controller Test Mode")
    print("-----------------------------")
    print("This mode will help you identify button and axis codes for your controller.")
    print("All events will be logged to config_debug.log")
    print("\nPress buttons or move joysticks when prompted. Press Ctrl+C to exit.")
    
    # First log controller information
    test_logger.info(f"CONTROLLER TEST - Device: {gamepad.name}")
    test_logger.info(f"CONTROLLER TEST - Path: {gamepad.path}")
    test_logger.info(f"CONTROLLER TEST - Type detected: {controller_type}")
    
    try:
        # Interactive test sequence
        tests = [
            "Press the D-pad Up button",
            "Press the D-pad Down button",
            "Press the D-pad Left button",
            "Press the D-pad Right button",
            "Press the Face buttons (X/Square, Circle, Triangle, Cross)",
            "Press the Left Shoulder button (L1)",
            "Press the Right Shoulder button (R1)",
            "Press the Left Trigger button (L2)",
            "Press the Right Trigger button (R2)",
            "Move the Left Stick in all directions",
            "Move the Right Stick in all directions",
            "Press the Left Stick button (L3)",
            "Press the Right Stick button (R3)",
            "Press the Start button",
            "Press the Select button",
            "Press the PS/Xbox button"
        ]
        
        # Results dictionary to store detected button/axis codes
        results = {}
        
        for test_instruction in tests:
            print(f"\n> {test_instruction}")
            test_logger.info(f"INSTRUCTION: {test_instruction}")
            
            # Wait for events for 5 seconds or until significant input detected
            start_time = time.time()
            detected = False
            
            while time.time() - start_time < 5 and not detected:
                try:
                    # Poll for events
                    event = gamepad.read_one()
                    if event:
                        if event.type == ecodes.EV_KEY and event.value == 1:  # Button down
                            btn_name = PS3_BUTTON_MAPPINGS.get(event.code, f"Unknown ({event.code})")
                            test_logger.info(f"TEST - BUTTON - {btn_name} - Pressed - Code: {event.code}")
                            print(f"  Detected: {btn_name} (Code: {event.code})")
                            
                            # Store in results
                            results[test_instruction] = (btn_name, event.code)
                            detected = True
                            
                        elif event.type == ecodes.EV_KEY and event.value == 0:  # Button up
                            btn_name = PS3_BUTTON_MAPPINGS.get(event.code, f"Unknown ({event.code})")
                            test_logger.info(f"TEST - BUTTON - {btn_name} - Released - Code: {event.code}")
                            
                        elif event.type == ecodes.EV_ABS and abs(event.value) > 1000:  # Significant axis movement
                            axis_name = PS3_AXIS_MAPPINGS.get(event.code, f"Unknown Axis ({event.code})")
                            test_logger.info(f"TEST - AXIS - {axis_name} - Value: {event.value}")
                            print(f"  Detected: {axis_name} (Value: {event.value})")
                            
                            # Store in results
                            results[test_instruction] = (axis_name, event.code)
                            detected = True
                            
                    # Short sleep to avoid CPU thrashing
                    time.sleep(0.01)
                except Exception as e:
                    test_logger.error(f"Error reading event: {e}")
                    time.sleep(0.01)
            
            # If nothing detected, note it
            if not detected:
                print("  No significant input detected. Moving to next test...")
                test_logger.info("No significant input detected")
        
        # Print test summary
        print("\n=== Controller Test Results ===")
        for instruction, result in results.items():
            if result:
                name, code = result
                print(f"{instruction}: {name} (Code: {code})")
        
        test_logger.info("Controller test completed")
        print("\nController test complete! Results logged to config_debug.log")
        print("Press Enter to continue to normal operation or Ctrl+C to exit...")
        input()
        
    except KeyboardInterrupt:
        print("\nTest mode interrupted by user.")
        test_logger.info("Test mode interrupted by user")
    except Exception as e:
        print(f"\nError in test mode: {e}")
        test_logger.error(f"Test mode error: {e}")
    
    return

def generate_button_mapping_file():
    """Generate a Python file with updated button mappings from test results"""
    try:
        with open('config_debug.log', 'r') as f:
            lines = f.readlines()
        
        # Parse detected button codes
        button_mappings = {}
        for line in lines:
            if 'TEST - BUTTON' in line and 'Pressed' in line:
                parts = line.split(' - ')
                if len(parts) >= 4:
                    btn_name = parts[2]
                    code_part = parts[3].split('Code: ')[1]
                    code = int(code_part.strip())
                    button_mappings[code] = btn_name
        
        # Parse detected axis codes
        axis_mappings = {}
        for line in lines:
            if 'TEST - AXIS' in line:
                parts = line.split(' - ')
                if len(parts) >= 3:
                    axis_name = parts[2]
                    if 'Left Stick' in axis_name or 'Right Stick' in axis_name:
                        code_part = parts[3].split('(')[1].split(')')[0]
                        code = int(code_part.strip())
                        axis_mappings[code] = axis_name
        
        # Generate Python code
        if button_mappings or axis_mappings:
            with open('controller_mappings.py', 'w') as f:
                f.write("#!/usr/bin/env python3\n")
                f.write("# Generated button and axis mappings from test mode\n\n")
                
                if button_mappings:
                    f.write("BUTTON_MAPPINGS = {\n")
                    for code, name in button_mappings.items():
                        f.write(f"    {code}: \"{name}\",\n")
                    f.write("}\n\n")
                
                if axis_mappings:
                    f.write("AXIS_MAPPINGS = {\n")
                    for code, name in axis_mappings.items():
                        f.write(f"    {code}: \"{name}\",\n")
                    f.write("}\n")
            
            print(f"Generated controller_mappings.py with detected button and axis codes")
            return True
    except Exception as e:
        print(f"Error generating mapping file: {e}")
        main_logger.error(f"Error generating mapping file: {e}")
    
    return False
