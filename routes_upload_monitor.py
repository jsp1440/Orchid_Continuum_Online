"""
Upload Monitor Dashboard
Simple web dashboard to monitor Google Drive upload progress from iPad
"""
from flask import Blueprint, render_template, jsonify
from app import db
import os
from datetime import datetime, timedelta

upload_monitor_bp = Blueprint('upload_monitor', __name__)

@upload_monitor_bp.route('/upload-monitor')
def upload_monitor():
    """Main upload monitor dashboard page"""
    return render_template('upload_monitor.html')

@upload_monitor_bp.route('/api/upload-status')
def upload_status():
    """API endpoint for upload status data"""
    try:
        # Get upload statistics
        query = """
        SELECT 
            COUNT(*) as total_images,
            COUNT(google_drive_url) FILTER (WHERE google_drive_url IS NOT NULL AND google_drive_url != '') as uploaded,
            COUNT(*) FILTER (WHERE google_drive_url IS NULL OR google_drive_url = '') as remaining,
            ROUND(COUNT(google_drive_url) FILTER (WHERE google_drive_url IS NOT NULL) * 100.0 / COUNT(*), 2) as percent_complete
        FROM orchid_images;
        """
        result = db.session.execute(db.text(query)).fetchone()
        
        total = result[0]
        uploaded = result[1]
        remaining = result[2]
        percent = result[3] or 0
        
        # Calculate estimates (13 images per minute)
        UPLOAD_RATE = 13  # images per minute
        minutes_remaining = remaining / UPLOAD_RATE if remaining > 0 else 0
        hours_remaining = minutes_remaining / 60
        days_remaining = hours_remaining / 24
        
        # Get recent uploads with species names
        recent_query = """
        SELECT 
            COALESCE(ot.scientific_name, 'Unknown species') as species,
            oi.updated_at
        FROM orchid_images oi
        LEFT JOIN orchid_taxonomy ot ON oi.taxonomy_id = ot.id
        WHERE oi.google_drive_url IS NOT NULL AND oi.google_drive_url != ''
        ORDER BY oi.updated_at DESC
        LIMIT 10;
        """
        recent_uploads = db.session.execute(db.text(recent_query)).fetchall()
        
        # Format recent uploads
        recent_list = []
        for upload in recent_uploads:
            recent_list.append({
                'species': upload[0] or 'Unknown',
                'time': upload[1].strftime('%Y-%m-%d %H:%M:%S') if upload[1] else 'Unknown'
            })
        
        # Get upload speed (last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        speed_query = """
        SELECT COUNT(*) as uploads_last_hour
        FROM orchid_images
        WHERE google_drive_url IS NOT NULL 
        AND updated_at >= :one_hour_ago;
        """
        speed_result = db.session.execute(db.text(speed_query), {'one_hour_ago': one_hour_ago}).fetchone()
        uploads_last_hour = speed_result[0] if speed_result else 0
        current_rate = uploads_last_hour / 60  # per minute
        
        # Estimate completion time
        if current_rate > 0:
            eta_minutes = remaining / current_rate
            eta_datetime = datetime.utcnow() + timedelta(minutes=eta_minutes)
            eta_str = eta_datetime.strftime('%Y-%m-%d %H:%M UTC')
        else:
            eta_str = "Calculating..."
        
        return jsonify({
            'success': True,
            'total': total,
            'uploaded': uploaded,
            'remaining': remaining,
            'percent': percent,
            'estimates': {
                'minutes': round(minutes_remaining, 1),
                'hours': round(hours_remaining, 1),
                'days': round(days_remaining, 1),
                'eta': eta_str
            },
            'speed': {
                'last_hour': uploads_last_hour,
                'per_minute': round(current_rate, 1),
                'target_rate': UPLOAD_RATE
            },
            'recent_uploads': recent_list,
            'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@upload_monitor_bp.route('/api/upload-log')
def upload_log():
    """Get last 50 lines from upload log"""
    try:
        log_file = 'full_upload.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                last_50 = lines[-50:] if len(lines) > 50 else lines
                return jsonify({
                    'success': True,
                    'log': ''.join(last_50),
                    'total_lines': len(lines)
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Log file not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
