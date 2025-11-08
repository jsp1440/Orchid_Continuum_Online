"""
Manual Image Acquisition Trigger
Allows admin to trigger massive image downloads on demand
"""

from flask import Blueprint, jsonify, render_template
from app import db
from models import OrchidRecord
from admin_system import admin_required
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

manual_acquisition_bp = Blueprint('manual_acquisition', __name__)

@manual_acquisition_bp.route('/admin/trigger-image-acquisition')
@admin_required
def trigger_acquisition_page():
    """Page to manually trigger image acquisition"""
    
    # Get current stats
    total_orchids = db.session.query(db.func.count(OrchidRecord.id)).scalar() or 0
    with_images = db.session.query(db.func.count(OrchidRecord.id)).filter(
        OrchidRecord.google_drive_id.isnot(None)
    ).scalar() or 0
    without_images = total_orchids - with_images
    
    return render_template('manual_acquisition_trigger.html',
        total_orchids=total_orchids,
        with_images=with_images,
        without_images=without_images
    )

@manual_acquisition_bp.route('/admin/api/trigger-acquisition/<int:batch_size>')
@admin_required
def trigger_acquisition(batch_size):
    """
    API endpoint to manually trigger image acquisition
    """
    try:
        from gbif_eol_image_acquisition import run_image_acquisition
        
        logger.info(f"🚀 MANUAL TRIGGER: Starting acquisition for {batch_size} orchids")
        start_time = datetime.now()
        
        # Run acquisition
        results = run_image_acquisition(limit=batch_size)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Manual acquisition complete in {duration}s")
        
        return jsonify({
            'success': True,
            'results': results,
            'duration_seconds': duration,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Manual acquisition failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@manual_acquisition_bp.route('/admin/api/acquisition-status')
@admin_required
def acquisition_status():
    """Get current acquisition status"""
    
    total = db.session.query(db.func.count(OrchidRecord.id)).scalar() or 0
    with_images = db.session.query(db.func.count(OrchidRecord.id)).filter(
        OrchidRecord.google_drive_id.isnot(None)
    ).scalar() or 0
    
    return jsonify({
        'total_orchids': total,
        'with_images': with_images,
        'without_images': total - with_images,
        'percentage': round((with_images / total * 100), 1) if total > 0 else 0,
        'timestamp': datetime.now().isoformat()
    })
