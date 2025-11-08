"""
Julius AI Task Manager - Asynchronous Task Queue
Allows us to send tasks to Julius AI and receive results
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
from app import db
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

julius_tasks_bp = Blueprint('julius_tasks', __name__, url_prefix='/api/julius')

# API Key from environment
JULIUS_API_KEY = os.environ.get('JULIUS_API_KEY', '')

def require_julius_key(f):
    """Require Julius API key"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('x-julius-api-key') or request.args.get('api_key')
        if not key or key != JULIUS_API_KEY:
            return jsonify({'error': 'Invalid API key'}), 403
        return f(*args, **kwargs)
    return decorated

# In-memory task queue (for now - can move to database later)
task_queue = []
completed_results = []
heartbeats = []

@julius_tasks_bp.route('/tasks', methods=['GET'])
@require_julius_key
def get_tasks():
    """Julius polls this to get pending tasks"""
    # Return all pending tasks
    pending = [t for t in task_queue if t['status'] == 'pending']
    
    return jsonify({
        'success': True,
        'tasks': pending,
        'count': len(pending)
    })

@julius_tasks_bp.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task for Julius (no auth required for internal use)"""
    data = request.json
    
    task = {
        'id': str(uuid.uuid4()),
        'subject': data.get('subject', 'Untitled Task'),
        'description': data.get('description', ''),
        'priority': data.get('priority', 'normal'),
        'data': data.get('data', {}),
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    task_queue.append(task)
    
    return jsonify({
        'success': True,
        'message': 'Task created successfully',
        'task_id': task['id'],
        'task': task
    })

@julius_tasks_bp.route('/results', methods=['POST'])
@require_julius_key
def submit_result():
    """Julius posts results here when tasks are complete"""
    data = request.json
    task_id = data.get('task_id')
    status = data.get('status', 'completed')
    result_data = data.get('result_data', {})
    
    # Update task in queue
    for task in task_queue:
        if task['id'] == task_id:
            task['status'] = status
            task['result'] = result_data
            task['completed_at'] = datetime.utcnow().isoformat()
            completed_results.append(task)
            break
    
    return jsonify({
        'success': True,
        'message': 'Result submitted successfully'
    })

@julius_tasks_bp.route('/heartbeat', methods=['POST'])
@require_julius_key
def receive_heartbeat():
    """Julius sends heartbeats to show he's alive"""
    data = request.json
    
    heartbeat = {
        'timestamp': datetime.utcnow().isoformat(),
        'current_task': data.get('current_task'),
        'status_message': data.get('status_message'),
        'ip': request.remote_addr
    }
    
    heartbeats.append(heartbeat)
    # Keep only last 100 heartbeats
    if len(heartbeats) > 100:
        heartbeats.pop(0)
    
    return jsonify({
        'success': True,
        'message': 'Heartbeat received'
    })

@julius_tasks_bp.route('/status', methods=['GET'])
def get_status():
    """Get overall status of Julius task system (no auth)"""
    pending = [t for t in task_queue if t['status'] == 'pending']
    completed = [t for t in task_queue if t['status'] == 'completed']
    
    last_heartbeat = heartbeats[-1] if heartbeats else None
    
    return jsonify({
        'status': 'active' if last_heartbeat else 'unknown',
        'tasks': {
            'total': len(task_queue),
            'pending': len(pending),
            'completed': len(completed)
        },
        'last_heartbeat': last_heartbeat,
        'heartbeat_count': len(heartbeats)
    })

@julius_tasks_bp.route('/results/<task_id>', methods=['GET'])
def get_result(task_id):
    """Get result for a specific task (no auth)"""
    for task in completed_results:
        if task['id'] == task_id:
            return jsonify({
                'success': True,
                'task': task
            })
    
    for task in task_queue:
        if task['id'] == task_id:
            return jsonify({
                'success': True,
                'task': task,
                'note': 'Task not yet completed' if task['status'] == 'pending' else 'Task in progress'
            })
    
    return jsonify({
        'success': False,
        'error': 'Task not found'
    }), 404

print("✅ Julius Task Manager initialized")
