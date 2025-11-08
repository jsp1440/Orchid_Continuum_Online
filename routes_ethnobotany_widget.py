"""
Ethnobotany Widget Routes
Display traditional knowledge and cultural significance of orchids
"""

from flask import Blueprint, render_template, jsonify
from models import OrchidRecord
from app import db
import logging

logger = logging.getLogger(__name__)

ethnobotany_widget_bp = Blueprint('ethnobotany_widget', __name__)


@ethnobotany_widget_bp.route('/ethnobotany/<int:orchid_id>')
def ethnobotany_widget(orchid_id):
    """Display ethnobotany widget for an orchid"""
    try:
        orchid = db.session.query(OrchidRecord).get(orchid_id)
        
        if not orchid:
            return jsonify({'error': 'Orchid not found'}), 404
        
        ethnobotany = orchid.ethnobotany_data if orchid.ethnobotany_data else None
        
        return render_template('ethnobotany_widget.html',
                             orchid=orchid,
                             ethnobotany=ethnobotany)
    
    except Exception as e:
        logger.error(f"Error displaying ethnobotany widget: {e}")
        return jsonify({'error': str(e)}), 500


@ethnobotany_widget_bp.route('/api/ethnobotany/<int:orchid_id>')
def ethnobotany_api(orchid_id):
    """API endpoint for ethnobotany data"""
    try:
        orchid = db.session.query(OrchidRecord).get(orchid_id)
        
        if not orchid:
            return jsonify({'error': 'Orchid not found'}), 404
        
        if not orchid.ethnobotany_data:
            return jsonify({
                'orchid_id': orchid_id,
                'genus': orchid.genus,
                'species': orchid.species,
                'has_ethnobotany_data': False
            })
        
        return jsonify({
            'orchid_id': orchid_id,
            'genus': orchid.genus,
            'species': orchid.species,
            'has_ethnobotany_data': True,
            'ethnobotany_data': orchid.ethnobotany_data
        })
    
    except Exception as e:
        logger.error(f"Error fetching ethnobotany data: {e}")
        return jsonify({'error': str(e)}), 500


logger.info("🌿 Ethnobotany Widget routes initialized")
