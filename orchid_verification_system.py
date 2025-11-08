"""
ORCHID VERIFICATION SYSTEM
Automatically validates all orchid names against GBIF
Flags suspicious entries and provides bulk correction tools
"""

from flask import Blueprint, render_template, jsonify, request
from admin_system import admin_required
from app import db
from models import OrchidRecord
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

verification_bp = Blueprint('verification', __name__)

def verify_orchid_name(scientific_name):
    """Verify orchid name against GBIF database"""
    if not scientific_name or scientific_name.strip() == '':
        return {'valid': False, 'confidence': 0, 'matched_name': None, 'status': 'missing_name'}
    
    try:
        # Query GBIF species match API
        response = requests.get(
            'https://api.gbif.org/v1/species/match',
            params={
                'name': scientific_name,
                'family': 'Orchidaceae'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check match type and confidence
            match_type = data.get('matchType', 'NONE')
            confidence = data.get('confidence', 0)
            matched_name = data.get('scientificName', '')
            
            return {
                'valid': match_type in ['EXACT', 'FUZZY', 'HIGHERRANK'] and confidence >= 80,
                'confidence': confidence,
                'matched_name': matched_name,
                'match_type': match_type,
                'status': data.get('status', 'UNKNOWN'),
                'synonym': data.get('synonym', False)
            }
        
        return {'valid': False, 'confidence': 0, 'matched_name': None, 'status': 'api_error'}
        
    except Exception as e:
        logger.error(f"GBIF verification error for '{scientific_name}': {e}")
        return {'valid': False, 'confidence': 0, 'matched_name': None, 'status': 'error'}

@verification_bp.route('/admin/verify-all-orchids')
@admin_required
def verify_all_orchids():
    """Admin page to verify all orchids"""
    # Get counts
    total = OrchidRecord.query.count()
    with_images = OrchidRecord.query.filter(
        db.or_(OrchidRecord.google_drive_id.isnot(None), OrchidRecord.image_url.isnot(None))
    ).count()
    
    return render_template('admin/verify_all_orchids.html',
                         total_orchids=total,
                         orchids_with_images=with_images)

@verification_bp.route('/api/admin/batch-verify', methods=['POST'])
@admin_required
def batch_verify():
    """Verify all orchids in batches"""
    try:
        data = request.json
        batch_size = data.get('batch_size', 50)
        offset = data.get('offset', 0)
        
        # Get batch of orchids with images
        orchids = OrchidRecord.query.filter(
            db.or_(OrchidRecord.google_drive_id.isnot(None), OrchidRecord.image_url.isnot(None))
        ).offset(offset).limit(batch_size).all()
        
        results = []
        for orchid in orchids:
            verification = verify_orchid_name(orchid.scientific_name)
            
            # Determine issue level
            issue_level = 'none'
            if not verification['valid']:
                if orchid.scientific_name and orchid.scientific_name.strip():
                    issue_level = 'invalid'
                else:
                    issue_level = 'missing'
            elif verification['confidence'] < 90:
                issue_level = 'low_confidence'
            
            results.append({
                'id': orchid.id,
                'current_name': orchid.scientific_name or '',
                'display_name': orchid.display_name,
                'gbif_match': verification.get('matched_name'),
                'confidence': verification.get('confidence', 0),
                'valid': verification['valid'],
                'issue_level': issue_level,
                'match_type': verification.get('match_type'),
                'has_image': bool(orchid.google_drive_id or orchid.image_url)
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'batch_size': len(results),
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Batch verification error: {e}")
        return jsonify({'error': str(e)}), 500

@verification_bp.route('/api/admin/fix-orchid-name', methods=['POST'])
@admin_required
def fix_orchid_name():
    """Fix an orchid's scientific name"""
    try:
        data = request.json
        orchid_id = data.get('orchid_id')
        new_name = data.get('new_name')
        
        orchid = OrchidRecord.query.get_or_404(orchid_id)
        
        # Parse new name
        parts = new_name.split(' ', 1)
        orchid.genus = parts[0] if len(parts) > 0 else ''
        orchid.species = parts[1] if len(parts) > 1 else ''
        orchid.scientific_name = new_name
        
        # Update display name if it was auto-generated
        if not orchid.display_name or 'Unknown' in orchid.display_name:
            orchid.display_name = new_name
        
        db.session.commit()
        
        logger.info(f"✅ Fixed orchid {orchid_id}: {new_name}")
        
        return jsonify({
            'success': True,
            'message': f'Updated to {new_name}'
        })
        
    except Exception as e:
        logger.error(f"Error fixing orchid name: {e}")
        return jsonify({'error': str(e)}), 500

@verification_bp.route('/api/admin/bulk-fix', methods=['POST'])
@admin_required
def bulk_fix():
    """Bulk fix orchids using GBIF matched names"""
    try:
        data = request.json
        fixes = data.get('fixes', [])
        
        count = 0
        for fix in fixes:
            orchid = OrchidRecord.query.get(fix['orchid_id'])
            if orchid and fix.get('gbif_match'):
                parts = fix['gbif_match'].split(' ', 1)
                orchid.genus = parts[0] if len(parts) > 0 else ''
                orchid.species = parts[1] if len(parts) > 1 else ''
                orchid.scientific_name = fix['gbif_match']
                
                if not orchid.display_name or 'Unknown' in orchid.display_name:
                    orchid.display_name = fix['gbif_match']
                
                count += 1
        
        db.session.commit()
        
        logger.info(f"✅ Bulk fixed {count} orchids")
        
        return jsonify({
            'success': True,
            'count': count,
            'message': f'Fixed {count} orchids'
        })
        
    except Exception as e:
        logger.error(f"Bulk fix error: {e}")
        return jsonify({'error': str(e)}), 500
