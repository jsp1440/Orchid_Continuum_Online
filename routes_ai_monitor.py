"""
AI Communication Monitor API Routes
Provides real-time monitoring dashboard for Replit Agent ↔ Julius AI communication
"""

from flask import Blueprint, render_template, jsonify
from models import db
from datetime import datetime
from sqlalchemy import text

monitor_bp = Blueprint('ai_monitor', __name__, url_prefix='/ai-monitor')

@monitor_bp.route('/')
def monitor_dashboard():
    """Main monitoring dashboard"""
    return render_template('ai_communication_monitor.html')

@monitor_bp.route('/api/ai-monitor/replit-status')
def replit_status():
    """Get Replit Agent status"""
    query = text("""
        SELECT 
            worker_id,
            worker_type,
            status,
            last_heartbeat,
            tasks_processed,
            current_task
        FROM worker_heartbeats
        WHERE worker_type = 'replit_agent'
        ORDER BY last_heartbeat DESC
        LIMIT 1
    """)
    
    result = db.session.execute(query).fetchone()
    
    if result:
        return jsonify({
            'worker_id': result[0],
            'worker_type': result[1],
            'status': result[2],
            'last_heartbeat': result[3].isoformat() if result[3] else None,
            'tasks_processed': result[4],
            'current_task': result[5]
        })
    else:
        return jsonify({
            'status': 'no_heartbeat',
            'last_heartbeat': None,
            'tasks_processed': 0,
            'current_task': None
        })

@monitor_bp.route('/api/ai-monitor/julius-status')
def julius_status():
    """Get Julius AI status"""
    query = text("""
        SELECT 
            worker_id,
            worker_type,
            status,
            last_heartbeat,
            tasks_processed,
            current_task,
            EXTRACT(EPOCH FROM (NOW() - last_heartbeat))/3600 as hours_since_heartbeat
        FROM worker_heartbeats
        WHERE worker_type LIKE '%julius%'
        ORDER BY last_heartbeat DESC
        LIMIT 1
    """)
    
    result = db.session.execute(query).fetchone()
    
    if result:
        return jsonify({
            'worker_id': result[0],
            'worker_type': result[1],
            'status': result[2],
            'last_heartbeat': result[3].isoformat() if result[3] else None,
            'tasks_processed': result[4],
            'current_task': result[5],
            'hours_since_heartbeat': float(result[6]) if result[6] else None
        })
    else:
        return jsonify({
            'status': 'no_heartbeat',
            'last_heartbeat': None,
            'tasks_processed': 0,
            'current_task': None,
            'hours_since_heartbeat': None
        })

@monitor_bp.route('/api/ai-monitor/stats')
def communication_stats():
    """Get communication statistics"""
    query = text("""
        SELECT 
            COUNT(*) as total_messages,
            COUNT(*) FILTER (WHERE status = 'pending') as pending_messages,
            COUNT(*) FILTER (WHERE status = 'completed') as completed_messages,
            MAX(created_at) as last_message_time
        FROM ai_communication
    """)
    
    result = db.session.execute(query).fetchone()
    
    return jsonify({
        'total_messages': result[0] if result else 0,
        'pending_messages': result[1] if result else 0,
        'completed_messages': result[2] if result else 0,
        'last_message_time': result[3].isoformat() if result and result[3] else None
    })

@monitor_bp.route('/api/ai-monitor/messages')
def recent_messages():
    """Get recent messages"""
    query = text("""
        SELECT 
            id,
            from_agent,
            to_agent,
            task_id,
            message_type,
            status,
            prompt_text,
            created_at,
            completed_at
        FROM ai_communication
        ORDER BY created_at DESC
        LIMIT 20
    """)
    
    results = db.session.execute(query).fetchall()
    
    messages = []
    for row in results:
        messages.append({
            'id': row[0],
            'from_agent': row[1],
            'to_agent': row[2],
            'task_id': row[3],
            'message_type': row[4],
            'status': row[5],
            'prompt_text': row[6],
            'created_at': row[7].isoformat() if row[7] else None,
            'completed_at': row[8].isoformat() if row[8] else None
        })
    
    return jsonify({'messages': messages})

@monitor_bp.route('/api/ai-monitor/heartbeats')
def recent_heartbeats():
    """Get recent heartbeats"""
    query = text("""
        SELECT 
            worker_id,
            worker_type,
            status,
            last_heartbeat,
            tasks_processed,
            current_task
        FROM worker_heartbeats
        ORDER BY last_heartbeat DESC
        LIMIT 10
    """)
    
    results = db.session.execute(query).fetchall()
    
    heartbeats = []
    for row in results:
        heartbeats.append({
            'worker_id': row[0],
            'worker_type': row[1],
            'status': row[2],
            'last_heartbeat': row[3].isoformat() if row[3] else None,
            'tasks_processed': row[4],
            'current_task': row[5]
        })
    
    return jsonify({'heartbeats': heartbeats})
