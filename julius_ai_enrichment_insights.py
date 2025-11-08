"""
Julius AI Enrichment Insights
Admin dashboard showing what Julius AI users are querying to guide database enrichment
"""

from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from models import JuliusAIQuery, OrchidRecord
from app import db
from admin_system import admin_required

julius_insights_bp = Blueprint('julius_insights', __name__, url_prefix='/admin/julius-insights')

@julius_insights_bp.route('/dashboard')
@admin_required
def insights_dashboard():
    """Admin dashboard showing Julius AI query insights for enrichment guidance"""
    
    last_30_days = datetime.utcnow() - timedelta(days=30)
    
    total_queries = db.session.query(func.count(JuliusAIQuery.id)).filter(
        JuliusAIQuery.created_at >= last_30_days
    ).scalar() or 0
    
    most_queried_genera = db.session.query(
        JuliusAIQuery.genus_queried,
        func.count(JuliusAIQuery.id).label('query_count')
    ).filter(
        JuliusAIQuery.genus_queried.isnot(None),
        JuliusAIQuery.created_at >= last_30_days
    ).group_by(JuliusAIQuery.genus_queried).order_by(desc('query_count')).limit(20).all()
    
    most_queried_species = db.session.query(
        JuliusAIQuery.genus_queried,
        JuliusAIQuery.species_queried,
        func.count(JuliusAIQuery.id).label('query_count')
    ).filter(
        JuliusAIQuery.species_queried.isnot(None),
        JuliusAIQuery.created_at >= last_30_days
    ).group_by(JuliusAIQuery.genus_queried, JuliusAIQuery.species_queried).order_by(desc('query_count')).limit(20).all()
    
    data_requested_breakdown = db.session.query(
        JuliusAIQuery.data_requested,
        func.count(JuliusAIQuery.id).label('request_count')
    ).filter(
        JuliusAIQuery.data_requested.isnot(None),
        JuliusAIQuery.created_at >= last_30_days
    ).group_by(JuliusAIQuery.data_requested).order_by(desc('request_count')).all()
    
    popular_endpoints = db.session.query(
        JuliusAIQuery.endpoint,
        func.count(JuliusAIQuery.id).label('hit_count'),
        func.avg(JuliusAIQuery.execution_time_ms).label('avg_time')
    ).filter(
        JuliusAIQuery.created_at >= last_30_days
    ).group_by(JuliusAIQuery.endpoint).order_by(desc('hit_count')).limit(10).all()
    
    enrichment_recommendations = []
    for genus, species, count in most_queried_species[:10]:
        orchid = db.session.query(OrchidRecord).filter_by(
            genus=genus,
            species=species
        ).first()
        
        if orchid:
            missing_data = []
            if not orchid.native_habitat:
                missing_data.append('habitat')
            if not orchid.bloom_time:
                missing_data.append('bloom_time')
            if not orchid.light_requirements:
                missing_data.append('light_requirements')
            if not orchid.cultural_notes:
                missing_data.append('cultural_notes')
            if not orchid.image_url:
                missing_data.append('image')
            
            if missing_data:
                enrichment_recommendations.append({
                    'orchid_id': orchid.id,
                    'genus': genus,
                    'species': species,
                    'query_count': count,
                    'missing_data': missing_data,
                    'priority_score': count * len(missing_data)
                })
    
    enrichment_recommendations.sort(key=lambda x: x['priority_score'], reverse=True)
    
    return render_template('admin/julius_insights_dashboard.html',
                         total_queries=total_queries,
                         most_queried_genera=most_queried_genera,
                         most_queried_species=most_queried_species,
                         data_requested_breakdown=data_requested_breakdown,
                         popular_endpoints=popular_endpoints,
                         enrichment_recommendations=enrichment_recommendations[:20])

@julius_insights_bp.route('/api/enrichment-priorities')
@admin_required
def enrichment_priorities():
    """API endpoint returning enrichment priorities based on Julius AI queries"""
    
    last_30_days = datetime.utcnow() - timedelta(days=30)
    
    most_queried_species = db.session.query(
        JuliusAIQuery.genus_queried,
        JuliusAIQuery.species_queried,
        func.count(JuliusAIQuery.id).label('query_count')
    ).filter(
        JuliusAIQuery.species_queried.isnot(None),
        JuliusAIQuery.created_at >= last_30_days
    ).group_by(JuliusAIQuery.genus_queried, JuliusAIQuery.species_queried).order_by(desc('query_count')).limit(50).all()
    
    priorities = []
    for genus, species, count in most_queried_species:
        orchid = db.session.query(OrchidRecord).filter_by(
            genus=genus,
            species=species
        ).first()
        
        if orchid:
            missing_data = []
            if not orchid.native_habitat:
                missing_data.append('habitat')
            if not orchid.bloom_time:
                missing_data.append('bloom_time')
            if not orchid.light_requirements:
                missing_data.append('light')
            if not orchid.cultural_notes:
                missing_data.append('culture')
            if not orchid.image_url:
                missing_data.append('image')
            
            if missing_data:
                priorities.append({
                    'orchid_id': orchid.id,
                    'genus': genus,
                    'species': species,
                    'query_count': count,
                    'missing_data': missing_data,
                    'priority_score': count * len(missing_data)
                })
    
    priorities.sort(key=lambda x: x['priority_score'], reverse=True)
    
    return jsonify({
        'total_priorities': len(priorities),
        'recommendations': priorities[:30]
    })

@julius_insights_bp.route('/api/top-missing-metadata')
@admin_required
def top_missing_metadata():
    """Get top 100 orchids with the most missing metadata fields"""
    limit = request.args.get('limit', 100, type=int)
    
    all_orchids = db.session.query(OrchidRecord).all()
    
    orchids_with_scores = []
    for orchid in all_orchids:
        missing_count = 0
        missing_fields = []
        
        if not orchid.native_habitat:
            missing_count += 1
            missing_fields.append('habitat')
        if not orchid.bloom_time:
            missing_count += 1
            missing_fields.append('bloom_time')
        if not orchid.light_requirements:
            missing_count += 1
            missing_fields.append('light')
        if not orchid.cultural_notes:
            missing_count += 1
            missing_fields.append('culture')
        if not orchid.temperature_requirements:
            missing_count += 1
            missing_fields.append('temperature')
        if not orchid.water_requirements:
            missing_count += 1
            missing_fields.append('water')
        if not orchid.image_url:
            missing_count += 1
            missing_fields.append('image')
        
        if missing_count > 0:
            orchids_with_scores.append({
                'orchid_id': orchid.id,
                'genus': orchid.genus,
                'species': orchid.species,
                'common_name': orchid.common_name,
                'missing_count': missing_count,
                'missing_fields': missing_fields
            })
    
    orchids_with_scores.sort(key=lambda x: x['missing_count'], reverse=True)
    
    return jsonify({
        'total_orchids_with_missing_data': len(orchids_with_scores),
        'top_missing': orchids_with_scores[:limit]
    })

@julius_insights_bp.route('/api/auto-enrich-batch', methods=['POST'])
@admin_required
def auto_enrich_batch():
    """Automatically enrich a batch of orchids using EOL and GBIF"""
    from orchid_data_enrichment import enricher
    
    data = request.json
    orchid_ids = data.get('orchid_ids', [])
    
    if not orchid_ids:
        return jsonify({'error': 'No orchid IDs provided'}), 400
    
    results = {
        'total_processed': 0,
        'successful': 0,
        'failed': 0,
        'details': []
    }
    
    for orchid_id in orchid_ids[:100]:
        try:
            result = enricher.enrich_orchid_record(orchid_id, force_refresh=False)
            results['total_processed'] += 1
            
            if result.get('status') == 'success':
                results['successful'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append(result)
        except Exception as e:
            results['failed'] += 1
            results['details'].append({
                'orchid_id': orchid_id,
                'status': 'error',
                'message': str(e)
            })
    
    return jsonify(results)
