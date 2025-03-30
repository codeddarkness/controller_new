#!/bin/bash

# ANSI colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Print header
echo -e "\n${BOLD}Servo Controller - Modular Installation Script${NC}"
echo "================================================="

# Function to check dependencies
check_dependencies() {
    echo -e "\n${BOLD}Checking dependencies...${NC}"
    
    # Check Python version
    python3 --version > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${RED}Python 3 is not installed. Please install Python 3.${NC}"
        exit 1
    fi
    
    # Check pip
    python3 -m pip --version > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Installing pip...${NC}"
        sudo apt-get update
        sudo apt-get install -y python3-pip
    fi
    
    # Check required packages
    echo -e "${BOLD}Installing required Python packages...${NC}"
    python3 -m pip install --user evdev flask
    
    # Try to install hardware-specific packages
    echo -e "${BOLD}Installing hardware interface packages...${NC}"
    python3 -m pip install --user Adafruit_PCA9685 mpu6050-raspberrypi || true
    
    echo -e "${GREEN}Dependencies installed successfully.${NC}"
}

# Function to create backup of files
backup_files() {
    echo -e "\n${BOLD}Creating backup of existing files...${NC}"
    
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Find existing Python files
    find . -maxdepth 1 -name "*.py" -exec cp {} "$BACKUP_DIR/" \;
    
    echo -e "${GREEN}Backup created in: $BACKUP_DIR${NC}"
}

# Function to verify file integrity
verify_files() {
    echo -e "\n${BOLD}Verifying file integrity...${NC}"
    
    # Check for required modules
    FILES=(
        "servo_controller.py"
        "config.py"
        "logger.py"
        "hardware.py"
        "controller_input.py"
        "database.py"
        "display.py"
        "web_interface.py"
        "test_mode.py"
    )
    
    for FILE in "${FILES[@]}"; do
        if [ ! -f "$FILE" ]; then
            echo -e "${RED}Missing required file: $FILE${NC}"
            return 1
        else
            # Verify file is complete by checking for expected content
            case "$FILE" in
                "config.py")
                    grep -q "SERVO_MIN" "$FILE" || { echo -e "${RED}$FILE appears incomplete${NC}"; return 1; }
                    ;;
                "logger.py")
                    grep -q "initialize_loggers" "$FILE" || { echo -e "${RED}$FILE appears incomplete${NC}"; return 1; }
                    ;;
                "hardware.py")
                    grep -q "stop_all_servos" "$FILE" || { echo -e "${RED}$FILE appears incomplete${NC}"; return 1; }
                    ;;
                "controller_input.py")
                    grep -q "find_game_controller" "$FILE" || { echo -e "${RED}$FILE appears incomplete${NC}"; return 1; }
                    grep -q "handle_controller_input" "$FILE" || { echo -e "${RED}$FILE appears incomplete${NC}"; return 1; }
                    ;;
                "web_interface.py")
                    grep -q "app.route('/api/servo/all" "$FILE" || { echo -e "${RED}$FILE appears incomplete${NC}"; return 1; }
                    grep -q "start_web_server" "$FILE" || { echo -e "${RED}$FILE appears incomplete${NC}"; return 1; }
                    ;;
                "servo_controller.py")
                    grep -q "main()" "$FILE" || { echo -e "${RED}$FILE appears incomplete${NC}"; return 1; }
                    ;;
            esac
            
            echo -e "${GREEN}✓ $FILE verified${NC}"
        fi
    done
    
    # Check templates directory
    if [ ! -d "templates" ]; then
        echo -e "${YELLOW}Templates directory not found. Creating...${NC}"
        mkdir -p templates
    fi
    
    if [ ! -f "templates/servo_controller.html" ]; then
        echo -e "${YELLOW}HTML template missing. Using existing template if available...${NC}"
        if [ -f "$BACKUP_DIR/templates/servo_controller.html" ]; then
            cp "$BACKUP_DIR/templates/servo_controller.html" "templates/"
            echo -e "${GREEN}✓ Restored servo_controller.html from backup${NC}"
        else
            echo -e "${RED}Could not find servo_controller.html template.${NC}"
            echo -e "${YELLOW}Web interface may not work correctly.${NC}"
            # Create minimal template
            mkdir -p templates
            echo '<html><head><title>Servo Controller</title></head><body><h1>Servo Controller</h1><p>Web interface template is missing.</p></body></html>' > templates/servo_controller.html
        fi
    else
        echo -e "${GREEN}✓ templates/servo_controller.html verified${NC}"
    fi
    
    return 0
}

# Function to make executable
make_executable() {
    echo -e "\n${BOLD}Making scripts executable...${NC}"
    chmod +x servo_controller.py
    echo -e "${GREEN}Scripts are now executable.${NC}"
}

# Function to test the controller
test_controller() {
    echo -e "\n${BOLD}Testing controller functionality...${NC}"
    
    # Python syntax check
    echo "Running Python syntax check..."
    for FILE in *.py; do
        python3 -m py_compile "$FILE" 2>/dev/null
        if [ $? -ne 0 ]; then
            echo -e "${RED}Syntax error in $FILE${NC}"
            python3 -m py_compile "$FILE"
            return 1
        fi
    done
    
    echo -e "${GREEN}All Python files passed syntax check.${NC}"
    
    # Show available devices
    echo -e "\n${BOLD}Available input devices:${NC}"
    python3 -c "import evdev; print('\n'.join([f'{path}: {evdev.InputDevice(path).name}' for path in evdev.list_devices()]))" 2>/dev/null || echo "No devices found or evdev not installed."
    
    echo -e "\n${GREEN}Installation and verification complete.${NC}"
    echo -e "\nTo run the controller:"
    echo -e "  ${BOLD}./servo_controller.py${NC} - Normal operation"
    echo -e "  ${BOLD}./servo_controller.py --test-controller${NC} - Test controller mode"
    echo -e "  ${BOLD}./servo_controller.py --web-only${NC} - Web interface only"
    echo -e "  ${BOLD}./servo_controller.py --device /dev/input/eventX${NC} - Specify controller device"
    echo -e "  ${BOLD}./servo_controller.py --list-devices${NC} - List available input devices"
}

# Main installation process
main() {
    # Check if we're in the right directory
    if [ ! -f "install.sh" ]; then
        echo -e "${RED}Error: This script should be run from the directory containing install.sh${NC}"
        exit 1
    fi
    
    # Create backup
    backup_files
    
    # Check dependencies
    check_dependencies
    
    # Verify files
    verify_files
    if [ $? -ne 0 ]; then
        echo -e "${RED}File verification failed.${NC}"
        echo -e "${YELLOW}Please ensure all required files are present and complete.${NC}"
        exit 1
    fi
    
    # Make executable
    make_executable
    
    # Test controller
    test_controller
}

# Execute main function
main
