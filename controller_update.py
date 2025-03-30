# Replace the existing controller handling with this updated version:

def handle_controller_input(gamepad):
    """Process input from game controller"""
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
                                break
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
                                break
                            else:
                                q_pressed = True
                                print("\nPress Q again to exit...")
                
                # Update display to reflect changes
                display_status()
                
            except Exception as e:
                # Log the error but continue processing events
                logger.error(f"Error processing controller event: {e}")
                debug_logger.error(f"ERROR - {e} - Event: {event}")
    
    except Exception as e:
        logger.error(f"Controller error: {e}")
        print(f"\nController error: {e}")
        exit_flag = True
