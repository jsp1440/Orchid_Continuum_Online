"""
Autonomous System Monitoring Dashboard
Real-time view of image acquisition progress and worker status
"""

from flask import Blueprint, render_template, jsonify
from app import db
import json
from datetime import datetime, timedelta
from sqlalchemy import text

autonomous_dashboard_bp = Blueprint('autonomous_dashboard', __name__)

@autonomous_dashboard_bp.route('/autonomous-dashboard')
def dashboard():
    """Main monitoring dashboard"""
    return render_template('autonomous_dashboard.html')

@autonomous_dashboard_bp.route('/api/autonomous/metrics')
def get_metrics():
    """Get current system metrics"""
    try:
        # Get total images
        result = db.session.execute(text("SELECT COUNT(*) as count FROM image_assets")).fetchone()
        total_images = result[0] if result else 0
        
        # Get unique species with images
        result = db.session.execute(text("SELECT COUNT(DISTINCT scientific_name) FROM image_assets")).fetchone()
        species_with_images = result[0] if result else 0
        
        # Get total taxonomy
        result = db.session.execute(text("SELECT COUNT(*) FROM orchid_taxonomy")).fetchone()
        total_taxonomy = result[0] if result else 0
        
        # Get task queue status
        result = db.session.execute(text("""
            SELECT 
                status, COUNT(*) as count
            FROM pipeline_tasks
            GROUP BY status
        """)).fetchall()
        
        task_status = {row[0]: row[1] for row in result}
        
        # Get worker heartbeats
        result = db.session.execute(text("""
            SELECT 
                worker_id, worker_type, status, last_heartbeat, tasks_processed, current_task
            FROM worker_heartbeats
            WHERE last_heartbeat > NOW() - INTERVAL '5 minutes'
            ORDER BY last_heartbeat DESC
        """)).fetchall()
        
        workers = []
        for row in result:
            workers.append({
                'worker_id': row[0],
                'worker_type': row[1],
                'status': row[2],
                'last_heartbeat': row[3].isoformat() if row[3] else None,
                'tasks_processed': row[4],
                'current_task': row[5]
            })
        
        # Get recent image acquisitions
        result = db.session.execute(text("""
            SELECT 
                scientific_name, source, pipeline, created_at
            FROM image_assets
            ORDER BY created_at DESC
            LIMIT 10
        """)).fetchall()
        
        recent_images = []
        for row in result:
            recent_images.append({
                'scientific_name': row[0],
                'source': row[1],
                'pipeline': row[2],
                'created_at': row[3].isoformat() if row[3] else None
            })
        
        # Calculate coverage
        coverage_pct = (species_with_images / total_taxonomy * 100) if total_taxonomy > 0 else 0
        progress_to_goal = (total_images / 100000 * 100)
        
        return jsonify({
            'success': True,
            'metrics': {
                'total_images': total_images,
                'species_with_images': species_with_images,
                'total_taxonomy': total_taxonomy,
                'coverage_percent': round(coverage_pct, 2),
                'progress_to_goal': round(progress_to_goal, 2),
                'goal': 100000
            },
            'task_queue': task_status,
            'workers': workers,
            'recent_images': recent_images,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@autonomous_dashboard_bp.route('/api/autonomous/start-cycle')
def start_cycle():
    """Manually trigger a discovery cycle (for testing)"""
    try:
        # Create some test events to kickstart the system
        db.session.execute(text("""
            INSERT INTO julius_ingest_events (
                event_type, scientific_name, pipeline_assigned, priority, status
            )
            SELECT 
                'image_discovered',
                scientific_name,
                'eol_gbif',
                8,
                'pending'
            FROM orchid_taxonomy
            WHERE scientific_name NOT IN (SELECT DISTINCT scientific_name FROM image_assets)
            LIMIT 50
        """))
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '50 discovery events created - triggers will launch pipeline tasks automatically'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
