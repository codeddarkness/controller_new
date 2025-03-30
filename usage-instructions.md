# PS3 Controller Mapping Test Tool - Usage Guide

## Overview

This tool helps you properly map your PS3 controller buttons and joysticks to match the expected values in your servo control application. The tool will guide you through pressing buttons in a specific sequence (as defined in your `keypress_order.txt` file) and will generate a Python module with the correct mapping for your controller.

## Installation

1. Download the script and make it executable:
   ```bash
   chmod +x ps3-controller-test.py
   ```

2. Make sure you have the required dependencies:
   ```bash
   sudo pip3 install evdev
   ```

3. Connect your PS3 controller via USB or Bluetooth.

## Using the Tool

### Basic Usage

Run the script with:

```bash
sudo python3 ps3-controller-test.py
```

The `sudo` is important because accessing input devices typically requires root privileges.

### Command Line Options

- `--list`: List all available input devices
  ```bash
  sudo python3 ps3-controller-test.py --list
  ```

- `--test`: Test existing mappings (after you've generated them)
  ```bash
  sudo python3 ps3-controller-test.py --test
  ```

## Test Procedure

1. The script will scan for available input devices and attempt to find your PS3 controller.

2. If multiple devices are found, you may be asked to select which one to use.

3. You'll be guided through pressing each button and moving each joystick in the order specified in `keypress_order.txt`.

4. For each input, press the requested button or move the joystick as directed.

5. The script will record all button presses and joystick movements.

6. After completing all inputs, the script will generate `ps3_controller_mapping.py` containing the correct mappings.

7. You'll be shown a report of all mappings found and offered the option to test them immediately.

## Output Files

The tool generates the following files:

1. **ps3_controller_mapping.py** - Contains the button and axis mappings
   ```python
   # Example content
   PS3_BUTTON_MAPPINGS = {
       300: "D-Pad Up",
       301: "D-Pad Right",
       302: "D-Pad Down",
       303: "D-Pad Left",
       # ...other buttons
   }
   
   PS3_AXIS_MAPPINGS = {
       0: "Left Stick X",
       1: "Left Stick Y",
       # ...other axes
   }
   ```

2. **logs/controller_test_[TIMESTAMP].log** - Detailed log of all events during testing

## Using the Generated Mappings

After generating the mapping file, you can use it in your servo controller application:

1. Copy `ps3_controller_mapping.py` to your project directory

2. Import the mappings in your code:
   ```python
   from ps3_controller_mapping import PS3_BUTTON_MAPPINGS, PS3_AXIS_MAPPINGS
   ```

3. Use these mappings to interpret controller events:
   ```python
   def process_event(event):
       if event.type == ecodes.EV_KEY and event.value == 1:  # Button press
           if event.code in PS3_BUTTON_MAPPINGS:
               button_name = PS3_BUTTON_MAPPINGS[event.code]
               print(f"Button pressed: {button_name}")
               
               # Handle specific buttons
               if button_name == "D-Pad Up":
                   # Move servos to 90°
                   pass
               elif button_name == "Cross (✕)":
                   # Toggle servo 0 lock
                   pass
       
       elif event.type == ecodes.EV_ABS:  # Joystick movement
           if event.code in PS3_AXIS_MAPPINGS:
               axis_name = PS3_AXIS_MAPPINGS[event.code]
               # Handle joystick movement
               if axis_name == "Left Stick X":
                   # Control servo 0
                   pass
   ```

## Troubleshooting

- **Permission denied errors**: Make sure to run the script with `sudo`
- **Controller not detected**: Try disconnecting and reconnecting the controller
- **Bluetooth connection issues**: Try connecting via USB first to verify functionality
- **Button presses not registering**: Press and hold the button briefly until it's recognized

## Next Steps

After generating the correct mappings, update your `servo_controller.py` script with the new mappings to ensure your controller works properly with your servos.
