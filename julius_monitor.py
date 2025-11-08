"""
Julius AI Activity Monitor
Tracks Julius's heartbeat and task progress in real-time
"""
from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
import json
import os

monitor_bp = Blueprint('julius_monitor', __name__)

# Store Julius's status in memory (could use database if needed)
JULIUS_STATUS = {
    'last_heartbeat': None,
    'current_task': None,
    'progress': {},
    'is_active': False,
    'heartbeat_count': 0,
    'started_at': None,
    'task_history': []
}

# Heartbeat timeout (if no heartbeat for 10 minutes, Julius is considered stalled)
HEARTBEAT_TIMEOUT_MINUTES = 10


@monitor_bp.route('/julius/heartbeat', methods=['POST'])
def julius_heartbeat():
    """
    Julius calls this endpoint every few minutes to report status
    
    Expected payload:
    {
        "task_id": "eol-taxonomy-extraction",
        "status_message": "Processed 5,000/13,429 species, extracted 85,000 names",
        "progress_pct": 37.2,
        "records_processed": 5000,
        "total_records": 13429
    }
    """
    data = request.json
    
    now = datetime.now()
    
    # Update status
    JULIUS_STATUS['last_heartbeat'] = now.isoformat()
    JULIUS_STATUS['current_task'] = data.get('task_id')
    JULIUS_STATUS['is_active'] = True
    JULIUS_STATUS['heartbeat_count'] += 1
    
    if not JULIUS_STATUS['started_at']:
        JULIUS_STATUS['started_at'] = now.isoformat()
    
    # Update progress
    JULIUS_STATUS['progress'] = {
        'message': data.get('status_message'),
        'percent': data.get('progress_pct', 0),
        'records_processed': data.get('records_processed', 0),
        'total_records': data.get('total_records', 0),
        'updated_at': now.isoformat()
    }
    
    # Add to history
    JULIUS_STATUS['task_history'].append({
        'timestamp': now.isoformat(),
        'task': data.get('task_id'),
        'message': data.get('status_message')
    })
    
    # Keep only last 50 history entries
    if len(JULIUS_STATUS['task_history']) > 50:
        JULIUS_STATUS['task_history'] = JULIUS_STATUS['task_history'][-50:]
    
    return jsonify({
        'success': True,
        'message': 'Heartbeat received',
        'your_uptime_minutes': (now - datetime.fromisoformat(JULIUS_STATUS['started_at'])).total_seconds() / 60 if JULIUS_STATUS['started_at'] else 0
    })


@monitor_bp.route('/julius/status')
def julius_status():
    """Get current Julius status (for API calls)"""
    
    # Check if Julius has stalled
    is_stalled = False
    minutes_since_heartbeat = None
    
    if JULIUS_STATUS['last_heartbeat']:
        last_beat = datetime.fromisoformat(JULIUS_STATUS['last_heartbeat'])
        minutes_since_heartbeat = (datetime.now() - last_beat).total_seconds() / 60
        
        if minutes_since_heartbeat > HEARTBEAT_TIMEOUT_MINUTES:
            is_stalled = True
            JULIUS_STATUS['is_active'] = False
    
    return jsonify({
        'is_active': JULIUS_STATUS['is_active'] and not is_stalled,
        'is_stalled': is_stalled,
        'last_heartbeat': JULIUS_STATUS['last_heartbeat'],
        'minutes_since_heartbeat': minutes_since_heartbeat,
        'current_task': JULIUS_STATUS['current_task'],
        'progress': JULIUS_STATUS['progress'],
        'heartbeat_count': JULIUS_STATUS['heartbeat_count'],
        'uptime_hours': (datetime.now() - datetime.fromisoformat(JULIUS_STATUS['started_at'])).total_seconds() / 3600 if JULIUS_STATUS['started_at'] else 0,
        'recent_activity': JULIUS_STATUS['task_history'][-10:]  # Last 10 activities
    })


@monitor_bp.route('/julius/monitor')
def julius_monitor_page():
    """Monitoring dashboard page"""
    return render_template('julius_live_monitor.html')


@monitor_bp.route('/julius/reset', methods=['POST'])
def reset_monitor():
    """Reset the monitor (admin only)"""
    global JULIUS_STATUS
    JULIUS_STATUS = {
        'last_heartbeat': None,
        'current_task': None,
        'progress': {},
        'is_active': False,
        'heartbeat_count': 0,
        'started_at': None,
        'task_history': []
    }
    return jsonify({'success': True, 'message': 'Monitor reset'})
