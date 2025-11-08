"""
Admin routes for massive orchid scraping
"""

from flask import Blueprint, render_template, jsonify
from admin_system import admin_required
import threading
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

massive_scrape_bp = Blueprint('massive_scrape', __name__)

# Global state tracker
scrape_status = {
    'running': False,
    'start_time': None,
    'progress': {},
    'results': None
}

def run_scrape_background():
    """Run the massive scrape in background thread"""
    global scrape_status
    
    try:
        scrape_status['running'] = True
        scrape_status['start_time'] = datetime.now()
        scrape_status['progress'] = {'status': 'Starting...'}
        
        from massive_orchid_scraper import run_massive_scrape
        results = run_massive_scrape()
        
        scrape_status['results'] = results
        scrape_status['running'] = False
        scrape_status['progress'] = {'status': 'Complete'}
        
        logger.info(f"✅ Background scrape complete: {results}")
        
    except Exception as e:
        logger.error(f"❌ Background scrape failed: {e}")
        scrape_status['running'] = False
        scrape_status['progress'] = {'status': f'Error: {str(e)}'}

@massive_scrape_bp.route('/admin/massive-scrape')
@admin_required
def massive_scrape_page():
    """Admin page to trigger massive scrape"""
    from models import OrchidRecord
    from app import db
    
    total_orchids = db.session.query(db.func.count(OrchidRecord.id)).scalar() or 0
    with_images = db.session.query(db.func.count(OrchidRecord.id)).filter(
        OrchidRecord.google_drive_id.isnot(None)
    ).scalar() or 0
    
    return render_template('massive_scrape.html',
        total_orchids=total_orchids,
        with_images=with_images,
        scrape_status=scrape_status
    )

@massive_scrape_bp.route('/admin/api/trigger-massive-scrape', methods=['POST'])
@admin_required
def trigger_massive_scrape():
    """Trigger the massive scrape"""
    global scrape_status
    
    if scrape_status['running']:
        return jsonify({
            'success': False,
            'error': 'Scrape already running'
        }), 400
    
    # Start scrape in background thread
    thread = threading.Thread(target=run_scrape_background, daemon=True)
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Massive scrape started in background',
        'start_time': datetime.now().isoformat()
    })

@massive_scrape_bp.route('/admin/api/scrape-status')
@admin_required
def get_scrape_status():
    """Get current scrape status"""
    from models import OrchidRecord
    from app import db
    
    total_orchids = db.session.query(db.func.count(OrchidRecord.id)).scalar() or 0
    with_images = db.session.query(db.func.count(OrchidRecord.id)).filter(
        OrchidRecord.google_drive_id.isnot(None)
    ).scalar() or 0
    
    return jsonify({
        'running': scrape_status['running'],
        'start_time': scrape_status['start_time'].isoformat() if scrape_status['start_time'] else None,
        'progress': scrape_status['progress'],
        'results': scrape_status['results'],
        'current_stats': {
            'total_orchids': total_orchids,
            'with_images': with_images
        }
    })
