#!/usr/bin/env python3
"""
PS3 Controller Detection Test
Simple script to verify the controller works
"""

import evdev
import time

def main():
    print("Testing PS3 controller detection...")
    
    # List all input devices
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    
    # Find PS3 controller
    ps3_controller = None
    for device in devices:
        print(f"Found device: {device.path} - {device.name}")
        if "PLAYSTATION" in device.name.upper():
            ps3_controller = device
            print(f"PS3 controller found: {device.name}")
            break
    
    if ps3_controller:
        print("Reading controller input. Press buttons or move joysticks...")
        print("Press Ctrl+C to exit")
        
        try:
            # Read events for 20 seconds
            end_time = time.time() + 20
            while time.time() < end_time:
                event = ps3_controller.read_one()
                if event:
                    print(f"Event: type={event.type}, code={event.code}, value={event.value}")
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("\nTest interrupted.")
    else:
        print("No PS3 controller found.")

if __name__ == "__main__":
    main()

