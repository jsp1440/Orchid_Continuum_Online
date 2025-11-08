from flask import Blueprint, jsonify, request
from app import db
from sqlalchemy import text
import subprocess
import os
import signal

autonomous_agent_bp = Blueprint('autonomous_agent', __name__)

# Track agent process
agent_process = None

@autonomous_agent_bp.route('/autonomous-agent/start', methods=['POST'])
def start_agent():
    """Start the autonomous enrichment agent"""
    global agent_process
    
    if agent_process and agent_process.poll() is None:
        return jsonify({'success': False, 'message': 'Agent already running', 'pid': agent_process.pid})
    
    try:
        # Start agent as background process
        agent_process = subprocess.Popen(
            ['python3', 'autonomous_enrichment_agent.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        # Log to dashboard
        query = text("""
            INSERT INTO julius_communication (message_from, message_type, subject, message, data)
            VALUES ('agent', 'status_update', 'Autonomous Agent Started', 
                    'User started autonomous enrichment agent. It will monitor Julius and take over if needed.',
                    :data::jsonb)
        """)
        db.session.execute(query, {
            'data': '{"agent_pid": ' + str(agent_process.pid) + ', "status": "running"}'
        })
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Autonomous agent started',
            'pid': agent_process.pid
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@autonomous_agent_bp.route('/autonomous-agent/stop', methods=['POST'])
def stop_agent():
    """Stop the autonomous enrichment agent"""
    global agent_process
    
    if not agent_process or agent_process.poll() is not None:
        return jsonify({'success': False, 'message': 'Agent not running'})
    
    try:
        # Terminate agent process
        os.killpg(os.getpgid(agent_process.pid), signal.SIGTERM)
        agent_process.wait(timeout=5)
        
        # Log to dashboard
        query = text("""
            INSERT INTO julius_communication (message_from, message_type, subject, message)
            VALUES ('agent', 'status_update', 'Autonomous Agent Stopped', 
                    'User stopped autonomous enrichment agent.')
        """)
        db.session.execute(query)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Autonomous agent stopped'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@autonomous_agent_bp.route('/autonomous-agent/status')
def agent_status():
    """Check if agent is running"""
    global agent_process
    
    running = agent_process and agent_process.poll() is None
    
    return jsonify({
        'running': running,
        'pid': agent_process.pid if running else None
    })

@autonomous_agent_bp.route('/autonomous-agent/trigger-analysis', methods=['POST'])
def trigger_analysis():
    """Manually trigger agent to run analysis now (don't wait for timeout)"""
    try:
        # Post message to trigger agent
        query = text("""
            INSERT INTO julius_communication (message_from, message_type, subject, message, data)
            VALUES ('agent', 'status_update', 'Manual Analysis Trigger', 
                    'User manually triggered agent analysis. Agent will run full analysis workflow now.',
                    '{"trigger": "manual", "reason": "user_request"}'::jsonb)
        """)
        db.session.execute(query)
        db.session.commit()
        
        # Run analysis directly
        from autonomous_enrichment_agent import AutonomousEnrichmentAgent
        agent = AutonomousEnrichmentAgent()
        agent.run_full_analysis()
        
        return jsonify({'success': True, 'message': 'Analysis triggered successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
