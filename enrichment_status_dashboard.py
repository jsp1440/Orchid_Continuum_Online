"""
GBIF/EOL Enrichment Status Dashboard
Real-time monitoring of data acquisition and enrichment
"""

from flask import render_template, jsonify, Blueprint
from sqlalchemy import func, text
from app import db
from models import OrchidRecord
from datetime import datetime, timedelta
import json

enrichment_status_bp = Blueprint('enrichment_status', __name__)

@enrichment_status_bp.route('/admin/enrichment-status')
def enrichment_status_dashboard():
    """
    Comprehensive dashboard showing GBIF/EOL data acquisition status
    """
    
    # Get overall statistics
    total_orchids = db.session.query(func.count(OrchidRecord.id)).scalar() or 0
    
    stats = {
        'total_orchids': total_orchids,
        'has_habitat': db.session.query(func.count(OrchidRecord.id)).filter(
            OrchidRecord.native_habitat.isnot(None)
        ).scalar() or 0,
        'has_distribution': db.session.query(func.count(OrchidRecord.id)).filter(
            OrchidRecord.native_distribution.isnot(None)
        ).scalar() or 0,
        'has_gbif_data': db.session.query(func.count(OrchidRecord.id)).filter(
            OrchidRecord.gbif_distribution.isnot(None),
            OrchidRecord.gbif_distribution != '{}'
        ).scalar() or 0,
        'has_gdrive_images': db.session.query(func.count(OrchidRecord.id)).filter(
            OrchidRecord.google_drive_id.isnot(None)
        ).scalar() or 0,
        'has_ai_analysis': db.session.query(func.count(OrchidRecord.id)).filter(
            OrchidRecord.ai_description.isnot(None)
        ).scalar() or 0,
        'has_flower_color': db.session.query(func.count(OrchidRecord.id)).filter(
            OrchidRecord.flower_color.isnot(None)
        ).scalar() or 0,
        'has_bloom_stage': db.session.query(func.count(OrchidRecord.id)).filter(
            OrchidRecord.bloom_stage.isnot(None)
        ).scalar() or 0
    }
    
    # Calculate percentages
    if total_orchids > 0:
        for key in stats:
            if key != 'total_orchids':
                stats[f'{key}_pct'] = round((stats[key] / total_orchids) * 100, 1)
    
    # Get recent enrichment activity (last 24 hours)
    yesterday = datetime.now() - timedelta(days=1)
    recent_updates = OrchidRecord.query.filter(
        OrchidRecord.updated_at >= yesterday
    ).order_by(OrchidRecord.updated_at.desc()).limit(20).all()
    
    # Get orchids with GBIF data (proof of acquisition)
    gbif_examples = OrchidRecord.query.filter(
        OrchidRecord.gbif_distribution.isnot(None),
        OrchidRecord.gbif_distribution != '{}'
    ).order_by(OrchidRecord.updated_at.desc()).limit(10).all()
    
    # Get orchids with Google Drive images (proof of image acquisition)
    gdrive_examples = OrchidRecord.query.filter(
        OrchidRecord.google_drive_id.isnot(None)
    ).order_by(OrchidRecord.updated_at.desc()).limit(10).all()
    
    # Parse GBIF data to show what's being acquired
    gbif_data_samples = []
    for orchid in gbif_examples:
        try:
            gbif_info = orchid.gbif_distribution if isinstance(orchid.gbif_distribution, dict) else json.loads(orchid.gbif_distribution or '{}')
            gbif_data_samples.append({
                'id': orchid.id,
                'name': orchid.scientific_name or orchid.display_name,
                'countries': gbif_info.get('countries', []),
                'occurrence_count': gbif_info.get('occurrence_count', 0),
                'coordinates_count': len(gbif_info.get('coordinates', [])),
                'updated': orchid.updated_at
            })
        except:
            pass
    
    return render_template('enrichment_status_dashboard.html',
        stats=stats,
        recent_updates=recent_updates,
        gbif_examples=gbif_data_samples,
        gdrive_examples=gdrive_examples
    )

@enrichment_status_bp.route('/api/enrichment-stats')
def enrichment_stats_api():
    """
    API endpoint for enrichment statistics
    """
    total_orchids = db.session.query(func.count(OrchidRecord.id)).scalar() or 0
    
    return jsonify({
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'total_orchids': total_orchids,
        'enrichment': {
            'habitat_data': {
                'count': db.session.query(func.count(OrchidRecord.id)).filter(
                    OrchidRecord.native_habitat.isnot(None)
                ).scalar() or 0,
                'percentage': round((db.session.query(func.count(OrchidRecord.id)).filter(
                    OrchidRecord.native_habitat.isnot(None)
                ).scalar() or 0) / total_orchids * 100, 1) if total_orchids > 0 else 0
            },
            'gbif_distribution': {
                'count': db.session.query(func.count(OrchidRecord.id)).filter(
                    OrchidRecord.gbif_distribution.isnot(None),
                    OrchidRecord.gbif_distribution != '{}'
                ).scalar() or 0,
                'percentage': round((db.session.query(func.count(OrchidRecord.id)).filter(
                    OrchidRecord.gbif_distribution.isnot(None),
                    OrchidRecord.gbif_distribution != '{}'
                ).scalar() or 0) / total_orchids * 100, 1) if total_orchids > 0 else 0
            },
            'google_drive_images': {
                'count': db.session.query(func.count(OrchidRecord.id)).filter(
                    OrchidRecord.google_drive_id.isnot(None)
                ).scalar() or 0,
                'percentage': round((db.session.query(func.count(OrchidRecord.id)).filter(
                    OrchidRecord.google_drive_id.isnot(None)
                ).scalar() or 0) / total_orchids * 100, 1) if total_orchids > 0 else 0
            },
            'ai_analysis': {
                'count': db.session.query(func.count(OrchidRecord.id)).filter(
                    OrchidRecord.ai_description.isnot(None)
                ).scalar() or 0,
                'percentage': round((db.session.query(func.count(OrchidRecord.id)).filter(
                    OrchidRecord.ai_description.isnot(None)
                ).scalar() or 0) / total_orchids * 100, 1) if total_orchids > 0 else 0
            }
        },
        'scheduler_status': {
            'active': True,
            'image_acquisition_frequency': 'Every 2 hours',
            'metadata_update_frequency': 'Every 2 hours',
            'full_refresh_frequency': 'Daily at 3:00 AM'
        }
    })
