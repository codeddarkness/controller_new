# Servo Power and Connection Troubleshooting Guide

## Overview
Based on your console logs, I've noticed your PS3 controller is being detected correctly, and the PCA9685 servo controller is also being found on I2C bus 1. However, your servos aren't responding properly. This guide will help you troubleshoot power and connection issues that could be preventing servo movement.

## Common Servo Issues and Solutions

### 1. Inadequate Power Supply

**Symptoms:**
- Servos twitch but don't move fully
- Servos move inconsistently
- PCA9685 resets when servos attempt to move

**Solutions:**
- **Use a dedicated power supply for the servos**
  - Standard servos need 5-6V and can draw 500mA or more each
  - Do NOT power servos directly from the Raspberry Pi's 5V pins
  - Use a separate 5V or 6V power supply with adequate current capacity (2A minimum for 4 servos)

- **Proper Wiring**
  - Connect the power supply GND to both the PCA9685 GND and the Raspberry Pi GND
  - Connect power supply V+ only to the PCA9685 V+ (red terminal)
  - Make sure servo wires are correctly oriented (usually red=power, brown/black=ground, orange/yellow=signal)

### 2. Connection Issues

**Symptoms:**
- Some servos work, others don't
- Servos don't respond at all

**Solutions:**
- **Check Physical Connections**
  - Verify each servo is plugged into the correct channel on the PCA9685
  - Ensure servo connectors are fully seated and oriented correctly
  - Look for bent pins or loose connections

- **Signal Wire Testing**
  - Run the servo diagnostic script to test each channel individually
  - If one channel doesn't work but others do, try moving a working servo to the non-working channel

### 3. Servo Lock States

**Symptoms:**
- Servos don't move when using joysticks
- Console shows "Servo X movement blocked" messages

**Solutions:**
- **Reset Lock States**
  - Press the X button to toggle servo 0 lock (should see "L" indicator disappear)
  - Press D-pad Down to ensure global lock is disabled
  - Restart the program to reset all lock states

### 4. PCA9685 Configuration

**Symptoms:**
- Servos move, but not to expected positions
- Servos move too little or too much

**Solutions:**
- **Adjust Pulse Range**
  - Standard servos expect 1-2ms pulses (SERVO_MIN=150, SERVO_MAX=600 for 50Hz)
  - Some servos may need different min/max pulse lengths
  - Try recalibrating with the diagnostic script

## Step-by-Step Testing Procedure

1. **Power Check**
   - Measure voltage at the PCA9685 power terminals with a multimeter
   - Should read 5-6V when servos are at rest
   - Voltage shouldn't drop below 4.5V when servos are moving

2. **Basic Servo Test**
   - Disconnect all servos except one
   - Connect a single servo to channel 0
   - Run the diagnostic script to test just this servo
   - If it works, add servos one by one

3. **Wiring Verification**
   - Double-check the I2C connections between Raspberry Pi and PCA9685:
     - Pi SDA → PCA9685 SDA
     - Pi SCL → PCA9685 SCL
     - Pi GND → PCA9685 GND
   - Verify servo connections:
     - Red wire → V+ terminal
     - Brown/Black wire → GND terminal
     - Orange/Yellow wire → PWM signal terminal

4. **Power Supply Isolation**
   - Try powering the servos with batteries instead of a power adapter
   - This eliminates potential noise/interference from the power supply

## Hardware Connection Diagram

```
[Power Supply 5-6V]
    |     |
    +     -
    |     |
    |     +------+
    |            |
    |            |
    V+          GND
    |            |
[PCA9685]------+
    |          |
  I2C SDA      |
  I2C SCL      |
    |          |
[Raspberry Pi]-+
    GND
```

## Testing with the Servo Diagnostic Script

The diagnostic script I provided will help you methodically test each component:

1. Run with `--check-permissions` to verify I2C access
2. Run with `--reset` to reset all servo positions
3. Run with `--test-all` for a complete hardware test
4. Use the interactive menu for targeted testing

These tests will help pinpoint exactly where the issue is occurring.

## If All Else Fails

1. Try a different power supply
2. Test the servos directly (without the PCA9685) if possible
3. Check if the PCA9685 is getting too hot during operation
4. Try a different I2C bus speed (`i2cdetect -y 1` confirms device availability)
5. Test with a simpler script that just controls one servo

By following this guide, you should be able to identify and resolve the issues preventing your servos from responding properly.
