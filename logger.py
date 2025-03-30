#!/usr/bin/env python3
"""
Logging setup for the servo controller.
"""

import logging
from datetime import datetime

# Initialize loggers
main_logger = None
debug_logger = None
test_logger = None

def setup_logging():
    """Set up the main application logger"""
    global main_logger
    
    main_logger = logging.getLogger('servo_controller')
    main_logger.setLevel(logging.INFO)
    
    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    
    # Add handler
    main_logger.addHandler(console)
    
    return main_logger

def setup_debug_logging():
    """Set up a dedicated debug logger for controller inputs"""
    global debug_logger
    
    debug_logger = logging.getLogger('controller_debug')
    debug_logger.setLevel(logging.DEBUG)
    
    # Create file handler for debug.log
    debug_file = logging.FileHandler('debug.log')
    debug_file.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    debug_file.setFormatter(formatter)
    
    # Add handler to logger
    debug_logger.addHandler(debug_file)
    
    return debug_logger

def setup_test_logging():
    """Set up a dedicated logger for controller testing"""
    global test_logger
    
    test_logger = logging.getLogger('controller_test')
    test_logger.setLevel(logging.DEBUG)
    
    # Create file handler for config_debug.log
    test_file = logging.FileHandler('config_debug.log')
    test_file.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    test_file.setFormatter(formatter)
    
    # Add handler to logger
    test_logger.addHandler(test_file)
    
    return test_logger

def initialize_loggers():
    """Initialize all loggers"""
    setup_logging()
    setup_debug_logging()
    setup_test_logging()
    
    main_logger.info("Loggers initialized")
    return main_logger, debug_logger, test_logger

# Initialize loggers if this module is imported
if __name__ != "__main__":
    main_logger, debug_logger, test_logger = initialize_loggers()
