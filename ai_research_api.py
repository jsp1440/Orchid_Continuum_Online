"""
AI Research Feed API Endpoints
Provides data for AI Research Feed widget on Neon One CMS
"""

from flask import Blueprint, jsonify, request
from app import db
import psycopg2
import os
from datetime import datetime

ai_research_bp = Blueprint('ai_research', __name__, url_prefix='/api')

DATABASE_URL = os.environ.get("DATABASE_URL")

@ai_research_bp.route('/ai-communication', methods=['GET'])
def get_ai_communication():
    """Get AI communication messages for widget"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                id, task_id, from_agent, to_agent, message_type,
                status, priority, prompt_text, file_path,
                result_summary, error_message, result_file_path,
                created_at, read_at, completed_at
            FROM ai_communication
            ORDER BY created_at DESC
            LIMIT %s;
        """, (limit,))
        
        columns = [
            'id', 'task_id', 'from_agent', 'to_agent', 'message_type',
            'status', 'priority', 'prompt_text', 'file_path',
            'result_summary', 'error_message', 'result_file_path',
            'created_at', 'read_at', 'completed_at'
        ]
        
        rows = cur.fetchall()
        messages = []
        
        for row in rows:
            message = dict(zip(columns, row))
            # Convert datetime to ISO format
            for key in ['created_at', 'read_at', 'completed_at']:
                if message[key]:
                    message[key] = message[key].isoformat()
            messages.append(message)
        
        conn.close()
        
        return jsonify(messages)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_research_bp.route('/research-insights', methods=['GET'])
def get_research_insights():
    """Get research insights for widget"""
    try:
        limit = request.args.get('limit', 20, type=int)
        research_area = request.args.get('area')  # Optional filter
        
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        query = """
            SELECT 
                id, insight_type, research_area, insight_text,
                confidence_level, proposed_followup,
                julius_generated, verified, impact_score,
                created_at, verified_at
            FROM research_insights
        """
        
        params = []
        if research_area:
            query += " WHERE research_area = %s"
            params.append(research_area)
        
        query += " ORDER BY created_at DESC LIMIT %s;"
        params.append(limit)
        
        cur.execute(query, params)
        
        columns = [
            'id', 'insight_type', 'research_area', 'insight_text',
            'confidence_level', 'proposed_followup',
            'julius_generated', 'verified', 'impact_score',
            'created_at', 'verified_at'
        ]
        
        rows = cur.fetchall()
        insights = []
        
        for row in rows:
            insight = dict(zip(columns, row))
            # Convert datetime to ISO format
            for key in ['created_at', 'verified_at']:
                if insight[key]:
                    insight[key] = insight[key].isoformat()
            insights.append(insight)
        
        conn.close()
        
        return jsonify(insights)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_research_bp.route('/ai-stats', methods=['GET'])
def get_ai_stats():
    """Get AI collaboration statistics"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Get task counts
        cur.execute("""
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_tasks,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tasks,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_tasks
            FROM ai_communication;
        """)
        
        task_stats = cur.fetchone()
        
        # Get insight counts
        cur.execute("""
            SELECT 
                COUNT(*) as total_insights,
                SUM(CASE WHEN insight_type = 'hypothesis' THEN 1 ELSE 0 END) as hypotheses_tested,
                SUM(CASE WHEN insight_type = 'finding' THEN 1 ELSE 0 END) as findings,
                SUM(CASE WHEN insight_type = 'correlation' THEN 1 ELSE 0 END) as correlations
            FROM research_insights;
        """)
        
        insight_stats = cur.fetchone()
        
        # Get research proposals count
        cur.execute("""
            SELECT COUNT(*) 
            FROM ai_communication 
            WHERE message_type = 'research_proposal';
        """)
        
        research_proposals = cur.fetchone()[0]
        
        # Get recent activity
        cur.execute("""
            SELECT 
                task_id,
                CASE 
                    WHEN message_type = 'research_proposal' THEN 'Research Proposal: ' || COALESCE(SUBSTRING(prompt_text, 1, 60), task_id)
                    WHEN status = 'completed' AND result_summary IS NOT NULL THEN 'Completed: ' || SUBSTRING(result_summary, 1, 60)
                    WHEN status = 'in_progress' THEN 'In Progress: ' || task_id
                    ELSE 'Task: ' || task_id
                END as title,
                created_at as timestamp
            FROM ai_communication
            ORDER BY created_at DESC
            LIMIT 10;
        """)
        
        recent_activity = []
        for row in cur.fetchall():
            recent_activity.append({
                'task_id': row[0],
                'title': row[1],
                'timestamp': row[2].isoformat() if row[2] else None
            })
        
        conn.close()
        
        stats = {
            'total_tasks': task_stats[0] or 0,
            'completed_tasks': task_stats[1] or 0,
            'pending_tasks': task_stats[2] or 0,
            'in_progress_tasks': task_stats[3] or 0,
            'error_tasks': task_stats[4] or 0,
            'total_insights': insight_stats[0] or 0,
            'hypotheses_tested': insight_stats[1] or 0,
            'findings': insight_stats[2] or 0,
            'correlations': insight_stats[3] or 0,
            'research_proposals': research_proposals or 0,
            'recent_activity': recent_activity
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_research_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for AI research system"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Check if tables exist
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'ai_communication'
            );
        """)
        
        tables_exist = cur.fetchone()[0]
        
        # Get last activity timestamp
        cur.execute("""
            SELECT MAX(created_at) 
            FROM ai_communication;
        """)
        
        last_activity = cur.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'status': 'healthy' if tables_exist else 'initializing',
            'tables_exist': tables_exist,
            'last_activity': last_activity.isoformat() if last_activity else None,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


# Register blueprint in your main app.py:
# from ai_research_api import ai_research_bp
# app.register_blueprint(ai_research_bp)
