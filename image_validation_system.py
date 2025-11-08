"""
IMAGE VALIDATION & REPORTING SYSTEM
Users can flag incorrect orchid identifications
Admins review and correct misidentified orchids
"""

from flask import Blueprint, request, jsonify, render_template
from admin_system import admin_required
from app import db, csrf
from models import OrchidRecord
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

validation_bp = Blueprint('validation', __name__)

# Create validation tracking table
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean

class OrchidValidationReport(db.Model):
    __tablename__ = 'orchid_validation_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    orchid_id = db.Column(db.Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    reporter_email = db.Column(db.String(255))
    report_reason = db.Column(db.Text, nullable=False)
    suggested_name = db.Column(db.String(255))
    status = db.Column(db.String(50), default='pending')  # pending, reviewed, corrected, rejected
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.String(255))
    
    orchid = db.relationship('OrchidRecord', backref='validation_reports')

# Create table - will be created automatically when app starts

@validation_bp.route('/api/report-incorrect-id', methods=['POST'])
@csrf.exempt
def report_incorrect_id():
    """User reports an incorrect orchid identification"""
    try:
        data = request.json
        orchid_id = data.get('orchid_id')
        reason = data.get('reason', 'Incorrect identification')
        suggested_name = data.get('suggested_name', '')
        reporter_email = data.get('email', 'anonymous')
        
        if not orchid_id:
            return jsonify({'error': 'Orchid ID required'}), 400
        
        # Create report
        report = OrchidValidationReport(
            orchid_id=orchid_id,
            reporter_email=reporter_email,
            report_reason=reason,
            suggested_name=suggested_name,
            status='pending'
        )
        
        db.session.add(report)
        db.session.commit()
        
        logger.info(f"📝 New validation report for orchid {orchid_id}: {reason}")
        
        return jsonify({
            'success': True,
            'message': 'Thank you! Your report has been submitted for admin review.',
            'report_id': report.id
        })
        
    except Exception as e:
        logger.error(f"Error creating validation report: {e}")
        return jsonify({'error': str(e)}), 500

@validation_bp.route('/admin/validation-reports')
@admin_required
def validation_dashboard():
    """Admin dashboard for reviewing validation reports"""
    pending_reports = OrchidValidationReport.query.filter_by(status='pending').order_by(
        OrchidValidationReport.created_at.desc()
    ).all()
    
    reviewed_reports = OrchidValidationReport.query.filter(
        OrchidValidationReport.status.in_(['reviewed', 'corrected', 'rejected'])
    ).order_by(OrchidValidationReport.reviewed_at.desc()).limit(50).all()
    
    return render_template('validation_dashboard.html',
                         pending_reports=pending_reports,
                         reviewed_reports=reviewed_reports)

@validation_bp.route('/api/admin/review-report/<int:report_id>', methods=['POST'])
@admin_required
def review_report(report_id):
    """Admin reviews and acts on a validation report"""
    try:
        data = request.json
        action = data.get('action')  # 'correct', 'reject', 'mark_reviewed'
        new_name = data.get('new_name')
        admin_notes = data.get('notes', '')
        
        report = OrchidValidationReport.query.get_or_404(report_id)
        orchid = report.orchid
        
        if action == 'correct':
            # Update orchid with correct identification
            if new_name:
                parts = new_name.split(' ', 1)
                orchid.genus = parts[0] if len(parts) > 0 else new_name
                orchid.species = parts[1] if len(parts) > 1 else ''
                orchid.scientific_name = new_name
                orchid.display_name = new_name
                
            report.status = 'corrected'
            logger.info(f"✅ Orchid {orchid.id} corrected to: {new_name}")
            
        elif action == 'reject':
            report.status = 'rejected'
            
        else:
            report.status = 'reviewed'
        
        report.reviewed_at = datetime.utcnow()
        report.reviewed_by = 'admin'
        report.admin_notes = admin_notes
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Report {action}ed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error reviewing report: {e}")
        return jsonify({'error': str(e)}), 500

@validation_bp.route('/api/admin/bulk-validate', methods=['POST'])
@admin_required
def bulk_validate():
    """Validate multiple orchids against GBIF"""
    try:
        import requests
        
        data = request.json
        orchid_ids = data.get('orchid_ids', [])
        
        results = []
        for orchid_id in orchid_ids:
            orchid = OrchidRecord.query.get(orchid_id)
            if not orchid:
                continue
            
            # Query GBIF for validation
            try:
                response = requests.get(
                    'https://api.gbif.org/v1/species/match',
                    params={'name': orchid.scientific_name},
                    timeout=5
                )
                
                if response.status_code == 200:
                    gbif_data = response.json()
                    confidence = gbif_data.get('confidence', 0)
                    matched_name = gbif_data.get('scientificName', '')
                    
                    results.append({
                        'orchid_id': orchid_id,
                        'current_name': orchid.scientific_name,
                        'gbif_matched': matched_name,
                        'confidence': confidence,
                        'match': matched_name.lower() == orchid.scientific_name.lower()
                    })
                    
            except Exception as e:
                logger.error(f"GBIF validation error for {orchid_id}: {e}")
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Bulk validation error: {e}")
        return jsonify({'error': str(e)}), 500
