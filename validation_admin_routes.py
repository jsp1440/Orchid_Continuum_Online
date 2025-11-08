"""
Admin routes for orchid image validation review.
Mounted into existing Flask app at /admin/validation/*
"""
from flask import Blueprint, render_template, jsonify, request, Response
from admin_system import admin_required
from app import db
from sqlalchemy import text
import json
from datetime import datetime

validation_admin_bp = Blueprint('validation_admin', __name__, url_prefix='/admin/validation')


@validation_admin_bp.route('/review')
@admin_required
def review_page():
    """Main validation review interface."""
    run_id = request.args.get('run_id', type=int)
    
    # Get all validation runs
    runs_query = text("""
        SELECT run_id, started_at, finished_at, images_scanned, notes
        FROM image_validation_runs
        ORDER BY started_at DESC
        LIMIT 20
    """)
    runs = db.session.execute(runs_query).fetchall()
    
    return render_template('admin/validation_review.html', 
                         runs=runs,
                         selected_run_id=run_id)


@validation_admin_bp.route('/api/results')
@admin_required
def get_results():
    """API endpoint to fetch validation results."""
    run_id = request.args.get('run_id', type=int)
    status_filter = request.args.get('status', 'all')
    
    query = """
        SELECT 
            ivr.id,
            ivr.orchid_id,
            ivr.image_path,
            ivr.predicted_genus,
            ivr.predicted_species,
            ivr.vision_score,
            ivr.ocr_text,
            ivr.final_genus,
            ivr.final_species,
            ivr.final_confidence,
            ivr.reasons,
            ivr.status,
            ivr.powo_match,
            ivr.gbif_match,
            ivr.eol_match,
            ivr.filename_check,
            ivr.orchid_verifier,
            ivr.created_at,
            o.scientific_name as current_scientific_name,
            o.display_name as current_display_name,
            o.genus as current_genus,
            o.species as current_species
        FROM image_validation_results ivr
        LEFT JOIN orchid_record o ON ivr.orchid_id = o.id
        WHERE 1=1
    """
    params = {}
    
    if run_id:
        query += " AND ivr.run_id = :run_id"
        params['run_id'] = run_id
    
    if status_filter != 'all':
        query += " AND ivr.status = :status"
        params['status'] = status_filter
    
    query += " ORDER BY ivr.created_at DESC LIMIT 100"
    
    results = db.session.execute(text(query), params).fetchall()
    
    # Convert to list of dicts
    results_list = []
    for row in results:
        # Extract URLs from JSONB match fields
        powo_match = json.loads(row.powo_match) if row.powo_match else {}
        gbif_match = json.loads(row.gbif_match) if row.gbif_match else {}
        eol_match = json.loads(row.eol_match) if row.eol_match else {}
        filename_check = json.loads(row.filename_check) if row.filename_check else {}
        orchid_verifier = json.loads(row.orchid_verifier) if row.orchid_verifier else {}
        
        results_list.append({
            'id': row.id,
            'orchid_id': row.orchid_id,
            'image_path': row.image_path,
            'predicted_genus': row.predicted_genus,
            'predicted_species': row.predicted_species,
            'vision_score': float(row.vision_score) if row.vision_score else 0.0,
            'ocr_text': row.ocr_text,
            'final_genus': row.final_genus,
            'final_species': row.final_species,
            'final_confidence': float(row.final_confidence) if row.final_confidence else 0.0,
            'reasons': json.loads(row.reasons) if row.reasons else [],
            'status': row.status,
            'created_at': row.created_at.isoformat() if row.created_at else None,
            'powo_url': powo_match.get('url'),
            'gbif_url': gbif_match.get('url'),
            'eol_url': eol_match.get('url'),
            'powo_match': powo_match,
            'gbif_match': gbif_match,
            'eol_match': eol_match,
            'filename_check': filename_check,
            'orchid_verifier': orchid_verifier,
            'current_scientific_name': row.current_scientific_name,
            'current_display_name': row.current_display_name,
            'current_genus': row.current_genus,
            'current_species': row.current_species
        })
    
    return jsonify({
        'success': True,
        'results': results_list,
        'count': len(results_list)
    })


@validation_admin_bp.route('/api/update-status', methods=['POST'])
@admin_required
def update_status():
    """Update validation result status (accept/flag)."""
    data = request.json
    result_id = data.get('result_id')
    new_status = data.get('status')
    
    if new_status not in ['pending', 'accepted', 'flagged']:
        return jsonify({'error': 'Invalid status'}), 400
    
    query = text("""
        UPDATE image_validation_results
        SET status = :status
        WHERE id = :result_id
    """)
    
    db.session.execute(query, {
        'status': new_status,
        'result_id': result_id
    })
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Status updated to {new_status}'
    })


@validation_admin_bp.route('/api/apply-correction', methods=['POST'])
@admin_required
def apply_correction():
    """Apply validation result to orchid record."""
    data = request.json
    result_id = data.get('result_id')
    
    # Get validation result
    query = text("""
        SELECT orchid_id, final_genus, final_species
        FROM image_validation_results
        WHERE id = :result_id
    """)
    result = db.session.execute(query, {'result_id': result_id}).fetchone()
    
    if not result:
        return jsonify({'error': 'Result not found'}), 404
    
    # Update orchid record
    update_query = text("""
        UPDATE orchid_record
        SET genus = :genus,
            species = :species,
            scientific_name = :scientific_name
        WHERE id = :orchid_id
    """)
    
    scientific_name = f"{result.final_genus} {result.final_species}".strip() if result.final_genus else None
    
    db.session.execute(update_query, {
        'genus': result.final_genus,
        'species': result.final_species,
        'scientific_name': scientific_name,
        'orchid_id': result.orchid_id
    })
    
    # Mark as accepted
    db.session.execute(
        text("UPDATE image_validation_results SET status = 'accepted' WHERE id = :result_id"),
        {'result_id': result_id}
    )
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Applied correction to orchid {result.orchid_id}'
    })


@validation_admin_bp.route('/export.jsonl')
@admin_required
def export_jsonl():
    """Export validation results as JSON Lines for Julius AI."""
    run_id = request.args.get('run_id', type=int)
    limit = request.args.get('limit', type=int, default=1000)
    
    query = """
        SELECT 
            ivr.id,
            ivr.run_id,
            ivr.orchid_id,
            ivr.image_path,
            ivr.predicted_genus,
            ivr.predicted_species,
            ivr.vision_score,
            ivr.ocr_text,
            ivr.powo_match,
            ivr.gbif_match,
            ivr.eol_match,
            ivr.filename_check,
            ivr.orchid_verifier,
            ivr.final_genus,
            ivr.final_species,
            ivr.final_confidence,
            ivr.reasons,
            ivr.status,
            ivr.created_at,
            o.scientific_name as current_scientific_name,
            o.genus as current_genus,
            o.species as current_species
        FROM image_validation_results ivr
        LEFT JOIN orchid_record o ON ivr.orchid_id = o.id
        WHERE 1=1
    """
    params = {}
    
    if run_id:
        query += " AND ivr.run_id = :run_id"
        params['run_id'] = run_id
    
    query += f" ORDER BY ivr.created_at DESC LIMIT {limit}"
    
    results = db.session.execute(text(query), params).fetchall()
    
    def generate():
        for row in results:
            record = {
                'id': row.id,
                'run_id': row.run_id,
                'orchid_id': row.orchid_id,
                'image_path': row.image_path,
                'predicted_genus': row.predicted_genus,
                'predicted_species': row.predicted_species,
                'vision_score': float(row.vision_score) if row.vision_score else 0.0,
                'ocr_text': row.ocr_text,
                'powo_match': json.loads(row.powo_match) if row.powo_match else {},
                'gbif_match': json.loads(row.gbif_match) if row.gbif_match else {},
                'eol_match': json.loads(row.eol_match) if row.eol_match else {},
                'filename_check': json.loads(row.filename_check) if row.filename_check else {},
                'orchid_verifier': json.loads(row.orchid_verifier) if row.orchid_verifier else {},
                'final_genus': row.final_genus,
                'final_species': row.final_species,
                'final_confidence': float(row.final_confidence) if row.final_confidence else 0.0,
                'reasons': json.loads(row.reasons) if row.reasons else [],
                'status': row.status,
                'created_at': row.created_at.isoformat() if row.created_at else None,
                'current_scientific_name': row.current_scientific_name,
                'current_genus': row.current_genus,
                'current_species': row.current_species
            }
            yield json.dumps(record) + '\n'
    
    return Response(generate(), mimetype='application/x-ndjson')


@validation_admin_bp.route('/api/feedback', methods=['POST'])
@admin_required
def submit_feedback():
    """Submit human feedback for a validation result."""
    data = request.json
    result_id = data.get('result_id')
    decision = data.get('decision')
    correct_genus = data.get('correct_genus')
    correct_species = data.get('correct_species')
    notes = data.get('notes', '')
    reviewer = data.get('reviewer', 'admin')
    
    if decision not in ['accepted', 'flagged', 'corrected']:
        return jsonify({'error': 'Invalid decision'}), 400
    
    query = text("""
        INSERT INTO image_validation_feedback (
            result_id, reviewer, decision, correct_genus, correct_species, notes
        ) VALUES (
            :result_id, :reviewer, :decision, :correct_genus, :correct_species, :notes
        )
        RETURNING feedback_id
    """)
    
    result = db.session.execute(query, {
        'result_id': result_id,
        'reviewer': reviewer,
        'decision': decision,
        'correct_genus': correct_genus,
        'correct_species': correct_species,
        'notes': notes
    })
    db.session.commit()
    
    feedback_id = result.fetchone()[0]
    
    return jsonify({
        'success': True,
        'feedback_id': feedback_id,
        'message': f'Feedback recorded: {decision}'
    })


@validation_admin_bp.route('/public/export.jsonl')
def public_export_jsonl():
    """PUBLIC endpoint: Export validation results as JSON Lines for Julius AI (no auth required)."""
    run_id = request.args.get('run_id', type=int)
    limit = request.args.get('limit', type=int, default=1000)
    
    query = """
        SELECT 
            ivr.id,
            ivr.run_id,
            ivr.orchid_id,
            ivr.image_path,
            ivr.predicted_genus,
            ivr.predicted_species,
            ivr.vision_score,
            ivr.ocr_text,
            ivr.powo_match,
            ivr.gbif_match,
            ivr.eol_match,
            ivr.filename_check,
            ivr.orchid_verifier,
            ivr.final_genus,
            ivr.final_species,
            ivr.final_confidence,
            ivr.reasons,
            ivr.status,
            ivr.created_at,
            o.scientific_name as current_scientific_name,
            o.genus as current_genus,
            o.species as current_species
        FROM image_validation_results ivr
        LEFT JOIN orchid_record o ON ivr.orchid_id = o.id
        WHERE 1=1
    """
    params = {}
    
    if run_id:
        query += " AND ivr.run_id = :run_id"
        params['run_id'] = run_id
    
    query += f" ORDER BY ivr.created_at DESC LIMIT {limit}"
    
    results = db.session.execute(text(query), params).fetchall()
    
    def generate():
        for row in results:
            record = {
                'id': row.id,
                'run_id': row.run_id,
                'orchid_id': row.orchid_id,
                'image_path': row.image_path,
                'predicted_genus': row.predicted_genus,
                'predicted_species': row.predicted_species,
                'vision_score': float(row.vision_score) if row.vision_score else 0.0,
                'ocr_text': row.ocr_text,
                'powo_match': json.loads(row.powo_match) if row.powo_match else {},
                'gbif_match': json.loads(row.gbif_match) if row.gbif_match else {},
                'eol_match': json.loads(row.eol_match) if row.eol_match else {},
                'filename_check': json.loads(row.filename_check) if row.filename_check else {},
                'orchid_verifier': json.loads(row.orchid_verifier) if row.orchid_verifier else {},
                'final_genus': row.final_genus,
                'final_species': row.final_species,
                'final_confidence': float(row.final_confidence) if row.final_confidence else 0.0,
                'reasons': json.loads(row.reasons) if row.reasons else [],
                'status': row.status,
                'created_at': row.created_at.isoformat() if row.created_at else None,
                'current_scientific_name': row.current_scientific_name,
                'current_genus': row.current_genus,
                'current_species': row.current_species
            }
            yield json.dumps(record) + '\n'
    
    return Response(generate(), mimetype='application/x-ndjson')
