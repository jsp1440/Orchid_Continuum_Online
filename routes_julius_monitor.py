from flask import Blueprint, render_template, jsonify, request
from app import db
from sqlalchemy import text
from datetime import datetime

julius_monitor_bp = Blueprint('julius_monitor', __name__)

@julius_monitor_bp.route('/julius-monitor')
def julius_monitor_dashboard():
    """Dashboard to monitor Julius AI activity and communication"""
    return render_template('julius_monitor.html')

@julius_monitor_bp.route('/julius-monitor/api/messages')
def get_messages():
    """Get all communication messages"""
    limit = request.args.get('limit', 50, type=int)
    
    query = text("""
        SELECT 
            id,
            message_from,
            message_type,
            subject,
            message,
            data,
            created_at,
            read_by_other
        FROM julius_communication
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    
    result = db.session.execute(query, {'limit': limit})
    messages = []
    for row in result:
        messages.append({
            'id': row.id,
            'from': row.message_from,
            'type': row.message_type,
            'subject': row.subject,
            'message': row.message,
            'data': row.data,
            'created_at': row.created_at.isoformat() if row.created_at else None,
            'read': row.read_by_other
        })
    
    return jsonify({'messages': messages})

@julius_monitor_bp.route('/julius-monitor/api/enrichment-log')
def get_enrichment_log():
    """Get enrichment actions log"""
    limit = request.args.get('limit', 100, type=int)
    
    query = text("""
        SELECT 
            el.id,
            el.performed_by,
            el.action_type,
            el.orchid_id,
            el.orchid_ids,
            el.field_updated,
            el.old_value,
            el.new_value,
            el.data_source,
            el.attribution,
            el.confidence,
            el.notes,
            el.created_at,
            o.genus,
            o.species,
            o.scientific_name
        FROM enrichment_actions_log el
        LEFT JOIN orchid_record o ON el.orchid_id = o.id
        ORDER BY el.created_at DESC
        LIMIT :limit
    """)
    
    result = db.session.execute(query, {'limit': limit})
    actions = []
    for row in result:
        actions.append({
            'id': row.id,
            'performed_by': row.performed_by,
            'action_type': row.action_type,
            'orchid_id': row.orchid_id,
            'orchid_ids': row.orchid_ids,
            'field_updated': row.field_updated,
            'old_value': row.old_value,
            'new_value': row.new_value,
            'data_source': row.data_source,
            'attribution': row.attribution,
            'confidence': row.confidence,
            'notes': row.notes,
            'created_at': row.created_at.isoformat() if row.created_at else None,
            'orchid': {
                'genus': row.genus,
                'species': row.species,
                'scientific_name': row.scientific_name
            } if row.orchid_id else None
        })
    
    return jsonify({'actions': actions})

@julius_monitor_bp.route('/julius-monitor/api/stats')
def get_stats():
    """Get current statistics"""
    
    # Overall stats
    stats_query = text("""
        SELECT 
            COUNT(*) as total_messages,
            COUNT(CASE WHEN message_from = 'julius' THEN 1 END) as julius_messages,
            COUNT(CASE WHEN message_from = 'agent' THEN 1 END) as agent_messages,
            MAX(CASE WHEN message_from = 'julius' THEN created_at END) as julius_last_activity
        FROM julius_communication
    """)
    stats_result = db.session.execute(stats_query).fetchone()
    
    # Enrichment stats
    enrichment_query = text("""
        SELECT 
            COUNT(*) as total_actions,
            COUNT(CASE WHEN performed_by = 'julius' THEN 1 END) as julius_actions,
            COUNT(DISTINCT orchid_id) as orchids_affected,
            MAX(CASE WHEN performed_by = 'julius' THEN created_at END) as julius_last_enrichment
        FROM enrichment_actions_log
    """)
    enrichment_result = db.session.execute(enrichment_query).fetchone()
    
    # Database stats
    db_query = text("""
        SELECT 
            COUNT(*) as total_orchids,
            COUNT(CASE WHEN image_url IS NOT NULL THEN 1 END) as with_images,
            COUNT(CASE WHEN native_habitat IS NOT NULL AND native_habitat != '' THEN 1 END) as with_habitat,
            MAX(updated_at) as last_update
        FROM orchid_record
    """)
    db_result = db.session.execute(db_query).fetchone()
    
    return jsonify({
        'communication': {
            'total_messages': stats_result.total_messages,
            'julius_messages': stats_result.julius_messages,
            'agent_messages': stats_result.agent_messages,
            'julius_last_activity': stats_result.julius_last_activity.isoformat() if stats_result.julius_last_activity else None
        },
        'enrichment': {
            'total_actions': enrichment_result.total_actions,
            'julius_actions': enrichment_result.julius_actions,
            'orchids_affected': enrichment_result.orchids_affected,
            'julius_last_enrichment': enrichment_result.julius_last_enrichment.isoformat() if enrichment_result.julius_last_enrichment else None
        },
        'database': {
            'total_orchids': db_result.total_orchids,
            'with_images': db_result.with_images,
            'with_habitat': db_result.with_habitat,
            'image_coverage_pct': round(100.0 * db_result.with_images / db_result.total_orchids, 1) if db_result.total_orchids > 0 else 0,
            'last_update': db_result.last_update.isoformat() if db_result.last_update else None
        }
    })

@julius_monitor_bp.route('/julius-monitor/api/file-operations')
def get_file_operations():
    """Get file operations log"""
    limit = request.args.get('limit', 100, type=int)
    
    query = text("""
        SELECT 
            fo.id,
            fo.performed_by,
            fo.operation_type,
            fo.file_path,
            fo.file_url,
            fo.orchid_id,
            fo.file_size,
            fo.status,
            fo.error_message,
            fo.created_at,
            o.scientific_name as orchid_name
        FROM file_operations_log fo
        LEFT JOIN orchid_record o ON fo.orchid_id = o.id
        ORDER BY fo.created_at DESC
        LIMIT :limit
    """)
    
    result = db.session.execute(query, {'limit': limit})
    operations = []
    for row in result:
        operations.append({
            'id': row.id,
            'performed_by': row.performed_by,
            'operation_type': row.operation_type,
            'file_path': row.file_path,
            'file_url': row.file_url,
            'orchid_id': row.orchid_id,
            'orchid_name': row.orchid_name,
            'file_size': row.file_size,
            'status': row.status,
            'error_message': row.error_message,
            'created_at': row.created_at.isoformat() if row.created_at else None
        })
    
    return jsonify({'operations': operations})

@julius_monitor_bp.route('/julius-monitor/api/database-changes')
def get_database_changes():
    """Get database changes log"""
    limit = request.args.get('limit', 100, type=int)
    
    query = text("""
        SELECT 
            id,
            performed_by,
            operation_type,
            table_name,
            record_id,
            field_name,
            old_value,
            new_value,
            orchid_scientific_name,
            created_at
        FROM database_changes_log
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    
    result = db.session.execute(query, {'limit': limit})
    changes = []
    for row in result:
        changes.append({
            'id': row.id,
            'performed_by': row.performed_by,
            'operation_type': row.operation_type,
            'table_name': row.table_name,
            'record_id': row.record_id,
            'field_name': row.field_name,
            'old_value': row.old_value[:100] if row.old_value and len(row.old_value) > 100 else row.old_value,
            'new_value': row.new_value[:100] if row.new_value and len(row.new_value) > 100 else row.new_value,
            'orchid_scientific_name': row.orchid_scientific_name,
            'created_at': row.created_at.isoformat() if row.created_at else None
        })
    
    return jsonify({'changes': changes})

@julius_monitor_bp.route('/julius-monitor/api/post-message', methods=['POST'])
def post_message():
    """Post a message to Julius (from agent or user)"""
    data = request.json
    
    # Determine who is sending the message
    message_from = 'user' if data.get('type') == 'user_message' else 'agent'
    
    query = text("""
        INSERT INTO julius_communication (message_from, message_type, subject, message, data)
        VALUES (:from, :message_type, :subject, :message, :data::jsonb)
        RETURNING id
    """)
    
    result = db.session.execute(query, {
        'from': message_from,
        'message_type': data.get('type', 'status_update'),
        'subject': data.get('subject'),
        'message': data.get('message'),
        'data': data.get('data')
    })
    db.session.commit()
    
    return jsonify({'success': True, 'id': result.fetchone().id})
