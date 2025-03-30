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

# PS3 joystick mappings
PS3_AXIS_MAPPINGS = {
    0: "Left Stick X",      # Left stick horizontal
    1: "Left Stick Y",      # Left stick vertical
    2: "Right Stick X (Z)", # Right stick horizontal
    3: "Right Stick Y (RX)"  # Right stick vertical
}

# Update the controller input function based on these mappings
def handle_ps3_button(event):
    """Handle PS3 controller button press"""
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
    elif event.code == 291:  # Start
        move_all_servos(90)
    elif event.code == 300:  # D-pad Up
        move_all_servos(90)
    elif event.code == 302:  # D-pad Down
        lock_state = not lock_state
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
    
    # Additional buttons can be mapped here
    display_status()
