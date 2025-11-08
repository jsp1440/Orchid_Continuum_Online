"""
SIMPLE WORKING MONITORING DASHBOARD
Shows real-time AI processing status, database stats, and system health
"""

from flask import Blueprint, render_template, jsonify
from app import db
from models import BotanistVisionResult, OrchidRecord, OrchidTaxonomy
from sqlalchemy import func
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

monitor_bp = Blueprint('monitor', __name__)


@monitor_bp.route('/monitor')
def monitoring_dashboard():
    """Simple, working monitoring dashboard"""
    return render_template('simple_monitor.html')


@monitor_bp.route('/api/monitor/stats')
def get_stats():
    """Get current system statistics"""
    try:
        # Database counts
        total_orchids = db.session.query(func.count(OrchidRecord.id)).scalar() or 0
        total_taxonomy = db.session.query(func.count(OrchidTaxonomy.id)).scalar() or 0
        total_ai_analyses = db.session.query(func.count(BotanistVisionResult.id)).scalar() or 0
        
        # Recent activity (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_analyses = db.session.query(func.count(BotanistVisionResult.id)).filter(
            BotanistVisionResult.created_at >= yesterday
        ).scalar() or 0
        
        # AI provider breakdown
        provider_stats = db.session.query(
            BotanistVisionResult.ai_provider,
            func.count(BotanistVisionResult.id)
        ).group_by(BotanistVisionResult.ai_provider).all()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'database': {
                'total_orchids': total_orchids,
                'total_taxonomy': total_taxonomy,
                'total_ai_analyses': total_ai_analyses
            },
            'activity': {
                'last_24h_analyses': recent_analyses
            },
            'ai_providers': {
                provider: count for provider, count in provider_stats
            },
            'status': 'All systems operational ✓'
        })
        
    except Exception as e:
        logger.error(f"Monitor stats error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })


@monitor_bp.route('/api/monitor/recent-activity')
def get_recent_activity():
    """Get recent AI processing activity"""
    try:
        recent = db.session.query(BotanistVisionResult).order_by(
            BotanistVisionResult.created_at.desc()
        ).limit(10).all()
        
        return jsonify({
            'success': True,
            'activities': [{
                'species': r.scientific_name,
                'provider': r.ai_provider,
                'processing_time': r.processing_time,
                'created_at': r.created_at.isoformat() if r.created_at else None
            } for r in recent]
        })
        
    except Exception as e:
        logger.error(f"Recent activity error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })
