# PS3 controller button mappings
PS3_BUTTON_MAPPINGS = {
    # D-pad buttons (these were completely wrong in the original mapping)
    292: "D-Pad Up",       # Originally mapped as PS Button
    293: "D-Pad Right",    # Originally mapped as Unknown (293)
    294: "D-Pad Down",     # Originally mapped as L1
    295: "D-Pad Left",     # Originally mapped as R1
    
    # Face buttons
    300: "Triangle (△)",   # Originally mapped as D-Pad Up
    301: "Circle (○)",     # Originally mapped as D-Pad Right
    302: "Cross (✕)",      # Originally mapped as D-Pad Down
    303: "Square (□)",     # Originally mapped as D-Pad Left
    
    # Shoulder/trigger buttons
    296: "L2",             # Originally mapped as L3
    297: "R2",             # Originally mapped as R3
    298: "L1",             # Originally mapped as L2
    299: "R1",             # Originally mapped as R2
    
    # Other buttons
    288: "Select",         # This was correct
    289: "L3",             # Joystick button left
    290: "R3",             # Joystick button right
    291: "Start",          # This was correct
    304: "PS Button",      # Originally mapped as Cross (✕)
}

# PS3 joystick axis mappings
PS3_AXIS_MAPPINGS = {
    0: "Left Stick X",     # This is correct
    1: "Left Stick Y",     # This is correct
    2: "Right Stick X",    # This is correct
    3: "Right Stick Y"     # This is correct
}

# Button function mappings (for the servo controller)
def get_button_function(button_code):
    """Map button codes to servo control functions"""
    
    # Create mapping of button codes to functions
    function_map = {
        # D-pad
        292: "move_all_servos(90)",       # D-pad Up - all servos to 90°
        294: "toggle_global_lock()",       # D-pad Down - toggle global lock
        295: "move_all_servos(0)",        # D-pad Left - all servos to 0°
        293: "move_all_servos(180)",      # D-pad Right - all servos to 180°
        
        # Face buttons
        302: "toggle_servo_lock(0)",      # Cross (✕) - toggle lock for servo 0
        301: "toggle_servo_lock(1)",      # Circle (○) - toggle lock for servo 1
        303: "toggle_servo_lock(2)",      # Square (□) - toggle lock for servo 2
        300: "toggle_servo_lock(3)",      # Triangle (△) - toggle lock for servo 3
        
        # Shoulder buttons
        298: "decrease_speed()",          # L1 - decrease speed
        299: "increase_speed()",          # R1 - increase speed
        296: "move_all_servos(0)",        # L2 - all servos to 0°
        297: "move_all_servos(180)",      # R2 - all servos to 180°
        
        # Other buttons
        304: "check_exit()",              # PS Button - exit (double press)
        291: "move_all_servos(90)",       # Start - all servos to 90°
    }
    
    return function_map.get(button_code, None)

# Process controller input with corrected mappings
def process_controller_event(event):
    """Process controller events using the correct button mappings"""
    if event.type == ecodes.EV_KEY and event.value == 1:  # Button press
        # Get button name from mapping
        button_name = PS3_BUTTON_MAPPINGS.get(event.code, f"Unknown ({event.code})")
        print(f"Button pressed: {button_name} (Code: {event.code})")
        
        # Get corresponding function
        function = get_button_function(event.code)
        if function:
            return {
                'type': 'button',
                'name': button_name,
                'code': event.code,
                'function': function
            }
    
    elif event.type == ecodes.EV_ABS:  # Joystick movement
        # Only process significant movement
        if abs(event.value) > 10000:
            axis_name = PS3_AXIS_MAPPINGS.get(event.code, f"Unknown Axis ({event.code})")
            
            # Map axes to servos
            if event.code == 0:  # Left Stick X
                return {
                    'type': 'axis',
                    'name': axis_name,
                    'code': event.code,
                    'value': event.value,
                    'servo': 0  # Control servo 0
                }
            elif event.code == 1:  # Left Stick Y
                return {
                    'type': 'axis',
                    'name': axis_name,
                    'code': event.code,
                    'value': event.value,
                    'servo': 1  # Control servo 1
                }
            elif event.code == 2:  # Right Stick X
                return {
                    'type': 'axis',
                    'name': axis_name,
                    'code': event.code,
                    'value': event.value,
                    'servo': 2  # Control servo 2
                }
            elif event.code == 3:  # Right Stick Y
                return {
                    'type': 'axis',
                    'name': axis_name,
                    'code': event.code,
                    'value': event.value,
                    'servo': 3  # Control servo 3
                }
    
    return None
