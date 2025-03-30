#!/usr/bin/env python3
"""
Flask web interface for servo controller.
"""

from flask import Flask, render_template, jsonify, request
import threading

from config import WEB_HOST, WEB_PORT
from logger import main_logger
from hardware import (
    move_servo, 
    move_all_servos, 
    set_servo_position, 
    stop_all_servos, 
    get_hardware_status,
    servo_positions,
    hold_state,
    lock_state,
    SERVO_CHANNELS
)
from database import get_recent_logs
from controller_input import get_controller_status

# Initialize Flask app
app = Flask(__name__)

def start_web_server():
    """Start the Flask web server"""
    try:
        app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)
        main_logger.info(f"Web server started at http://{WEB_HOST}:{WEB_PORT}/")
    except Exception as e:
        main_logger.error(f"Web server error: {e}")
        print(f"Error starting web server: {e}")

# Flask routes
@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('servo_controller.html')

@app.route('/api/status')
def get_status():
    """API endpoint to get current status"""
    hw_status = get_hardware_status()
    controller_status = get_controller_status()
    
    status = {
        'servos': {
            'positions': hw_status['servos']['positions'],
            'hold_states': hw_status['servos']['hold_state'],
            'directions': hw_status['servos']['directions'],
            'speed': hw_status['servos']['speed']
        },
        'mpu': hw_status['mpu']['data'],
        'hardware': {
            'pca_connected': hw_status['pca']['connected'],
            'pca_bus': hw_status['pca']['bus'],
            'mpu_connected': hw_status['mpu']['connected'],
            'mpu_bus': hw_status['mpu']['bus'],
            'controller_connected': controller_status['connected'],
            'controller_type': controller_status['type']
        }
    }
    return jsonify(status)

@app.route('/api/servo/<int:channel>', methods=['POST'])
def control_servo(channel):
    """API endpoint to control a servo"""
    if channel not in SERVO_CHANNELS:
        return jsonify({'error': 'Invalid channel'}), 400
    
    data = request.get_json()
    if not data or 'angle' not in data:
        return jsonify({'error': 'Missing angle parameter'}), 400
    
    try:
        angle = int(data['angle'])
        set_servo_position(channel, angle)
        return jsonify({
            'success': True, 
            'channel': channel, 
            'angle': angle
        })
    except Exception as e:
        main_logger.error(f"API error when setting servo {channel}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/servo/all', methods=['POST'])
def control_all_servos():
    """API endpoint to control all servos"""
    data = request.get_json()
    if not data or 'angle' not in data:
        return jsonify({'error': 'Missing angle parameter'}), 400
    
    try:
        angle = int(data['angle'])
        results = move_all_servos(angle)
        return jsonify({
            'success': True, 
            'angle': angle,
            'results': results
        })
    except Exception as e:
        main_logger.error(f"API error when moving all servos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/servo/hold/<int:channel>', methods=['POST'])
def toggle_hold(channel):
    """API endpoint to toggle servo hold state"""
    if channel not in SERVO_CHANNELS:
        return jsonify({'error': 'Invalid channel'}), 400
    
    try:
        data = request.get_json()
        if data and 'hold' in data:
            hold_state[channel] = bool(data['hold'])
        else:
            hold_state[channel] = not hold_state[channel]
        
        return jsonify({
            'success': True, 
            'channel': channel, 
            'hold': hold_state[channel]
        })
    except Exception as e:
        main_logger.error(f"API error when toggling hold: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/servo/lock', methods=['POST'])
def toggle_lock():
    """API endpoint to toggle global lock state"""
    global lock_state
    
    try:
        data = request.get_json()
        if data and 'lock' in data:
            lock_state = bool(data['lock'])
        else:
            lock_state = not lock_state
        
        return jsonify({
            'success': True, 
            'lock_state': lock_state
        })
    except Exception as e:
        main_logger.error(f"API error when toggling lock: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def get_logs():
    """API endpoint to get log data"""
    try:
        limit = request.args.get('limit', default=100, type=int)
        logs = get_recent_logs(limit)
        return jsonify(logs)
    except Exception as e:
        main_logger.error(f"API error when retrieving logs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_servos():
    """API endpoint to stop all servos"""
    try:
        stop_all_servos()
        return jsonify({'success': True})
    except Exception as e:
        main_logger.error(f"API error when stopping servos: {e}")
        return jsonify({'error': str(e)}), 500

# Start the web server when this module is imported
def init_web_server():
    """Initialize the web server in a separate thread"""
    web_thread = threading.Thread(target=start_web_server)
    web_thread.daemon = True
    web_thread.start()
    return web_thread