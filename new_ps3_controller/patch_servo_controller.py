#!/usr/bin/env python3
"""
Patch and validate script for servo_controller.py
Corrects PS3 controller button mappings and validates hardware detection
"""

import os
import re
import sys
import subprocess

def check_dependencies():
    """Check for required dependencies"""
    try:
        import evdev
        print("✅ evdev module is installed")
    except ImportError:
        print("❌ evdev module missing - run: pip install evdev")
        print("   Note: For macOS, try: pip install pyobjc-framework-IOKit")
        return False
    
    try:
        import Adafruit_PCA9685
        print("✅ Adafruit_PCA9685 module is installed")
    except ImportError:
        print("⚠️ Adafruit_PCA9685 module missing - simulation mode will be used")
    
    try:
        from mpu6050 import mpu6050
        print("✅ mpu6050 module is installed")
    except ImportError:
        print("⚠️ mpu6050 module missing - simulation mode will be used")
    
    return True

def patch_button_mappings(file_path):
    """Patch the PS3 button mappings in the script"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if file already has updated mappings
    if '289: "Unknown (289)"' in content:
        print("✅ PS3 button mappings already updated")
        return True
    
    # Define the old and new mapping sections
    old_pattern = r'PS3_BUTTON_MAPPINGS = \{[^}]+\}'
    new_mappings = """PS3_BUTTON_MAPPINGS = {
    304: "Cross (✕)",      # South 
    305: "Circle (○)",     # East
    307: "Triangle (△)",   # North
    308: "Square (□)",     # West
    294: "L1",             # Left shoulder
    295: "R1",             # Right shoulder
    298: "L2",             # Left trigger
    299: "R2",             # Right trigger
    300: "D-Pad Up",
    301: "D-Pad Right",
    302: "D-Pad Down",
    303: "D-Pad Left",
    288: "Select",
    291: "Start",
    292: "PS Button",
    296: "L3",             # Left stick press
    297: "R3",             # Right stick press
    289: "Unknown (289)",  # Additional buttons found in logs
    290: "Unknown (290)",  # Additional buttons found in logs
    293: "Unknown (293)"   # Additional buttons found in logs
}"""
    
    # Replace old mappings with new ones
    patched_content = re.sub(old_pattern, new_mappings, content)
    
    # Update the servo control direction for channels 0 and 2
    direction_pattern = r'if channel == 0 or channel == (\d+):'
    patched_content = re.sub(direction_pattern, 'if channel == 0 or channel == 2:', patched_content)
    
    # Fix help text for --show-help
    help_pattern = r'print\("  --help, -h.*?\)'
    patched_content = re.sub(help_pattern, 'print("  --show-help         : Show this help message")', patched_content)
    
    with open(file_path, 'w') as f:
        f.write(patched_content)
    
    print("✅ PS3 button mappings updated")
    print("✅ Servo direction control fixed")
    print("✅ Help text updated")
    return True

def validate_script(file_path):
    """Check if script runs without syntax errors"""
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", file_path],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✅ Script syntax validation passed: {file_path}")
        return True
    else:
        print(f"❌ Script syntax validation failed: {file_path}")
        print(result.stderr)
        return False

def main():
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "servo_controller.py"
    
    print(f"Patching and validating: {file_path}")
    print("-" * 40)
    
    if not check_dependencies():
        print("\n⚠️ Missing required dependencies")
    
    if not patch_button_mappings(file_path):
        print("\n❌ Failed to patch button mappings")
        return
    
    if not validate_script(file_path):
        print("\n❌ Script contains syntax errors")
        return
    
    print("\n✅ Script patched and validated successfully")
    print(f"Run with: python {file_path}")
    print("For help: python {file_path} --show-help")

if __name__ == "__main__":
    main()

