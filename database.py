#!/usr/bin/env python3
"""
Database handling for servo controller.
"""

import json
import sqlite3
from datetime import datetime
from sqlite3 import Error

from config import DB_PATH
from logger import main_logger
from hardware import get_hardware_status
from controller_input import get_controller_status

def setup_database():
    """Initialize the SQLite database and tables"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create table for servo logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS servo_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                servo_data TEXT,
                mpu_data TEXT,
                hardware_status TEXT
            )
        ''')
        
        conn.commit()
        main_logger.info(f"Database initialized at {DB_PATH}")
        return True
    except Error as e:
        main_logger.error(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def log_data():
    """Log current data to the database"""
    try:
        # Get current hardware status
        hw_status = get_hardware_status()
        controller_status = get_controller_status()
        
        # Prepare data for logging
        timestamp = datetime.now().isoformat()
        
        servo_data = {
            'positions': hw_status['servos']['positions'],
            'hold_states': hw_status['servos']['hold_state'],
            'directions': hw_status['servos']['directions'],
            'speed': hw_status['servos']['speed']
        }
        
        hardware_status = {
            'controller': controller_status,
            'pca9685': hw_status['pca'],
            'mpu6050': {
                'connected': hw_status['mpu']['connected'],
                'bus': hw_status['mpu']['bus']
            }
        }
        
        # Convert to JSON
        servo_json = json.dumps(servo_data)
        mpu_json = json.dumps(hw_status['mpu']['data'])
        status_json = json.dumps(hardware_status)
        
        # Store in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO servo_logs (timestamp, servo_data, mpu_data, hardware_status) VALUES (?, ?, ?, ?)",
            (timestamp, servo_json, mpu_json, status_json)
        )
        conn.commit()
        conn.close()
        
        main_logger.debug("Data logged to database")
        return True
        
    except Exception as e:
        main_logger.error(f"Logging error: {e}")
        return False

def get_recent_logs(limit=100):
    """Get the most recent log entries"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get the most recent log entries
        cursor.execute("SELECT * FROM servo_logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        
        logs = []
        for row in rows:
            log_entry = {
                'id': row[0],
                'timestamp': row[1],
                'servo_data': json.loads(row[2]),
                'mpu_data': json.loads(row[3]),
                'hardware_status': json.loads(row[4])
            }
            logs.append(log_entry)
        
        conn.close()
        return logs
    except Exception as e:
        main_logger.error(f"Error retrieving logs: {e}")
        return []

def clear_logs():
    """Clear all logs from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM servo_logs")
        conn.commit()
        
        main_logger.info("All logs cleared from database")
        return True
    except Exception as e:
        main_logger.error(f"Error clearing logs: {e}")
        return False
    finally:
        if conn:
            conn.close()
