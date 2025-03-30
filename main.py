#!/usr/bin/env python3
"""
Main application for servo controller with PS3/Xbox controller input.
This modular version addresses various bugs in the original implementation.
"""

import signal
import sys
import time
import threading
import argparse
import os

# Import modules
from logger import main_logger, debug_logger, test_logger
from hardware import detect_i2c_devices, update_mpu_data, stop_all_servos
from controller_input import find_game_controller, handle_controller_input, list_available_controllers, exit_flag
from database import setup_database, log_data
from web_interface import init_web_server
from test_mode import run_controller_test_mode, generate_button_mapping_file
from display import update_display

# Exit handler for graceful shutdown
def exit_handler(signal_received=None, frame=None):
    """Handle program exit gracefully"""
    global exit_flag
    
    print("\nExiting program.")
    main_logger.info("Exiting program")
    exit_flag = True
    
    # Stop all servos
    stop_all_servos()
    
    # Exit after a short delay to allow threads to close
    time.sleep(0.5)
    sys.exit(0)

# Update thread for sensors and display
def update_thread():
    """Thread for updating sensor data, display, and logging to database"""
    last_log_time = 0
    
    while not exit_flag:
        # Update MPU data
        update_mpu_data()
        
        # Update display
        update_display()
        
        # Log data to the database (every 5 seconds to avoid overwhelming the DB)
        current_time = int(time.time())
        if current_time - last_log_time >= 5:
            log_data()
            last_log_time = current_time
        
        # Sleep to control update rate
        time.sleep(0.1)

def main():
    """Main function"""
    global exit_flag
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Servo Controller with MPU6050')
    parser.add_argument('--web-only', action='store_true', help='Run in web interface mode only')
    parser.add_argument('--test-controller', action='store_true', help='Run controller testing mode')
    parser.add_argument('--device', help='Specify controller device path')
    parser.add_argument('--list-devices', action='store_true', help='List available input devices')
    args = parser.parse_args()
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, exit_handler)
    
    # Set up database
    setup_database()
    
    # Just list devices if requested
    if args.list_devices:
        list_available_controllers()
        return
    
    # Detect I2C devices
    detect_i2c_devices()
    
    print("Servo Controller")
    print("---------------")
    main_logger.info("Starting servo controller")
    
    # Start web server in a separate thread
    web_thread = init_web_server()
    print("Web interface available at http://localhost:5000/")
    
    # Find game controller if not in web-only mode
    gamepad = None
    if not args.web_only:
        if args.device:
            gamepad = find_game_controller(args.device)
        else:
            gamepad = find_game_controller()
    
    # Start update thread for sensors and display
    update_thread_handle = threading.Thread(target=update_thread)
    update_thread_handle.daemon = True
    update_thread_handle.start()
    
    # Run controller test mode if requested
    if args.test_controller and gamepad:
        run_controller_test_mode(gamepad)
        # Generate button mapping file after test
        generate_button_mapping_file()
    
    # Start controller input handling if available and not in web-only mode
    if gamepad and not args.web_only:
        handle_controller_input(gamepad)
    else:
        # Keep the main thread alive if no controller or in web-only mode
        print("Running in web interface mode. Press Ctrl+C to exit.")
        while not exit_flag:
            time.sleep(0.5)
    
    # Clean exit
    exit_handler()

if __name__ == "__main__":
    main()
