"""
Orchid Image Reporting System
Critical for data integrity - allows users to report image/name mismatches
"""

from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from app import db
from models import OrchidImageReport, OrchidRecord
from datetime import datetime
import logging
from admin_system import admin_required
from julius_ai_validator import validator as name_validator

logger = logging.getLogger(__name__)

orchid_report_bp = Blueprint('orchid_report', __name__)

@orchid_report_bp.route('/api/report-orchid-image', methods=['POST'])
def report_orchid_image():
    """Submit a report about an orchid image"""
    try:
        data = request.get_json() if request.is_json else request.form
        
        orchid_id = data.get('orchid_id')
        issue_type = data.get('issue_type')
        description = data.get('description')
        reported_by_email = data.get('email')
        reported_by_name = data.get('name')
        suggested_name = data.get('suggested_name')
        
        if not orchid_id or not issue_type or not description:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        # Get orchid details
        orchid = OrchidRecord.query.get(orchid_id)
        if not orchid:
            return jsonify({
                'success': False,
                'error': 'Orchid not found'
            }), 404
        
        # Validate suggested name if provided
        if suggested_name and suggested_name.strip():
            # Try expanding AOS abbreviations first
            expanded_name = name_validator.expand_aos_abbreviation(suggested_name)
            if expanded_name:
                suggested_name = expanded_name
                logger.info(f"📝 Expanded abbreviation to: {expanded_name}")
            
            # Validate against GBIF
            validation = name_validator.validate_scientific_name(suggested_name)
            if not validation.get('is_valid'):
                logger.warning(f"⚠️ Suggested name '{suggested_name}' not found in GBIF - needs manual review")
            elif validation.get('match_type') == 'EXACT':
                logger.info(f"✓ Suggested name '{suggested_name}' verified in GBIF")
        
        # Create report
        report = OrchidImageReport(
            orchid_id=orchid_id,
            issue_type=issue_type,
            description=description,
            reported_by_email=reported_by_email,
            reported_by_name=reported_by_name,
            current_scientific_name=orchid.scientific_name,
            suggested_name=suggested_name,
            image_source=orchid.image_source,
            image_url=orchid.image_url,
            priority='high' if issue_type == 'wrong_orchid' else 'normal',
            status='pending'
        )
        
        db.session.add(report)
        db.session.commit()
        
        logger.info(f"🚨 New orchid image report #{report.id}: {issue_type} for orchid #{orchid_id}")
        
        # Send notification email (future enhancement)
        # send_report_notification(report)
        
        return jsonify({
            'success': True,
            'message': 'Report submitted successfully! We will review this issue immediately.',
            'report_id': report.id
        })
        
    except Exception as e:
        logger.error(f"Error submitting orchid report: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to submit report'
        }), 500


@orchid_report_bp.route('/admin/image-reports')
@admin_required
def admin_image_reports():
    """Admin dashboard for reviewing image reports"""
    status_filter = request.args.get('status', 'pending')
    
    query = OrchidImageReport.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    reports = query.order_by(OrchidImageReport.created_at.desc()).all()
    
    # Get counts by status
    pending_count = OrchidImageReport.query.filter_by(status='pending').count()
    in_progress_count = OrchidImageReport.query.filter_by(status='in_progress').count()
    resolved_count = OrchidImageReport.query.filter_by(status='resolved').count()
    
    return render_template('admin/image_reports.html',
                         reports=reports,
                         status_filter=status_filter,
                         pending_count=pending_count,
                         in_progress_count=in_progress_count,
                         resolved_count=resolved_count)


@orchid_report_bp.route('/admin/image-report/<int:report_id>/resolve', methods=['POST'])
@admin_required
def resolve_report(report_id):
    """Resolve an image report"""
    try:
        report = OrchidImageReport.query.get_or_404(report_id)
        
        resolution_notes = request.form.get('resolution_notes')
        action = request.form.get('action')
        
        if action == 'fix_name':
            # Update the orchid's scientific name
            suggested_name = request.form.get('suggested_name')
            if suggested_name:
                orchid = OrchidRecord.query.get(report.orchid_id)
                orchid.scientific_name = suggested_name
                report.resolution_notes = f"Updated scientific name to: {suggested_name}. {resolution_notes or ''}"
        
        elif action == 'remove_image':
            # Remove the problematic image
            orchid = OrchidRecord.query.get(report.orchid_id)
            orchid.image_url = None
            orchid.image_source = None
            report.resolution_notes = f"Image removed. {resolution_notes or ''}"
        
        elif action == 'mark_correct':
            # Mark as incorrectly reported
            report.resolution_notes = f"Verified correct. {resolution_notes or ''}"
        
        report.status = 'resolved'
        report.resolved_at = datetime.utcnow()
        report.resolved_by = request.form.get('resolved_by', 'admin')
        
        db.session.commit()
        
        flash(f'Report #{report_id} resolved successfully!', 'success')
        logger.info(f"✅ Resolved orchid image report #{report_id}: {action}")
        
        return redirect(url_for('orchid_report.admin_image_reports'))
        
    except Exception as e:
        logger.error(f"Error resolving report: {e}")
        flash('Error resolving report', 'error')
        return redirect(url_for('orchid_report.admin_image_reports'))


@orchid_report_bp.route('/admin/image-report/<int:report_id>/status', methods=['POST'])
@admin_required
def update_report_status(report_id):
    """Update report status"""
    try:
        report = OrchidImageReport.query.get_or_404(report_id)
        new_status = request.form.get('status')
        
        if new_status in ['pending', 'in_progress', 'resolved', 'dismissed']:
            report.status = new_status
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Status updated to {new_status}'
            })
        
        return jsonify({
            'success': False,
            'error': 'Invalid status'
        }), 400
        
    except Exception as e:
        logger.error(f"Error updating report status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
