"""
Julius AI Integration API
Secure API endpoints for Julius AI data analyst to access Orchid Continuum data
"""

import os
import secrets
import time
from functools import wraps
from flask import Blueprint, jsonify, request
from sqlalchemy import func, distinct, and_, or_
from models import OrchidRecord, OrchidTaxonomy, JuliusAIQuery, OCUGlossaryTerm
from app import db
from sqlalchemy import text

julius_api = Blueprint('julius_api', __name__, url_prefix='/api/julius')

# Generate secure API key (store this in environment variables)
JULIUS_API_KEY = os.environ.get('JULIUS_API_KEY', 'julius_' + secrets.token_urlsafe(32))

def require_api_key(f):
    """Decorator to require API key authentication - supports both X-API-Key and Bearer formats"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try X-API-Key header first (original format)
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        # If not found, try Authorization Bearer format
        if not api_key:
            auth_header = request.headers.get('Authorization')
            if auth_header:
                try:
                    scheme, token = auth_header.split()
                    if scheme.lower() == 'bearer':
                        api_key = token
                except ValueError:
                    pass
        
        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': 'Provide API key in X-API-Key header, Authorization: Bearer header, or api_key parameter'
            }), 401
        
        if api_key != JULIUS_API_KEY:
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

def log_query(f):
    """Decorator to log Julius AI queries for enrichment insights"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        genus_queried = request.args.get('genus') or request.json.get('genus') if request.json else None
        species_queried = request.args.get('species') or request.json.get('species') if request.json else None
        data_requested = None
        
        if 'habitat' in request.path or request.args.get('habitat'):
            data_requested = 'habitat'
        elif 'bloom' in request.path or request.args.get('bloom'):
            data_requested = 'bloom_time'
        elif 'image' in request.path or request.args.get('image'):
            data_requested = 'images'
        elif 'enrichment' in request.path:
            data_requested = 'enrichment_status'
        
        response = f(*args, **kwargs)
        
        execution_time = (time.time() - start_time) * 1000
        
        try:
            # SECURITY: Scrub api_key from query params before logging to prevent credential exposure
            safe_params = None
            if request.args:
                safe_params = {k: v for k, v in request.args.items() if k != 'api_key'}
                if not safe_params:  # If only api_key was present, set to None
                    safe_params = None
            
            query_log = JuliusAIQuery(
                endpoint=request.path,
                query_params=safe_params,
                genus_queried=genus_queried,
                species_queried=species_queried,
                data_requested=data_requested,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                response_status=response[1] if isinstance(response, tuple) else 200,
                execution_time_ms=execution_time
            )
            db.session.add(query_log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Failed to log Julius AI query: {e}")
        
        return response
    return decorated_function

@julius_api.route('/health')
@require_api_key
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Orchid Continuum Julius AI API',
        'version': '1.0.0'
    })

@julius_api.route('/stats/overview')
@require_api_key
@log_query
def overview_stats():
    """Get comprehensive overview statistics"""
    try:
        total_records = db.session.query(func.count(OrchidRecord.id)).scalar()
        total_genera = db.session.query(func.count(distinct(OrchidRecord.genus))).scalar()
        total_species = db.session.query(func.count(distinct(OrchidRecord.species))).scalar()
        records_with_images = db.session.query(func.count(OrchidRecord.id)).filter(
            OrchidRecord.image_url.isnot(None)
        ).scalar()
        records_with_habitat = db.session.query(func.count(OrchidRecord.id)).filter(
            OrchidRecord.native_habitat.isnot(None)
        ).scalar()
        # Note: gbif_enriched and eol_enriched columns may not exist in current schema
        # Using alternative approach - count orchids with GBIF/EOL data
        records_with_gbif = db.session.query(func.count(OrchidRecord.id)).filter(
            OrchidRecord.gbif_taxon_key.isnot(None)
        ).scalar() if hasattr(OrchidRecord, 'gbif_taxon_key') else 0
        records_with_eol = db.session.query(func.count(OrchidRecord.id)).filter(
            OrchidRecord.eol_page_id.isnot(None)
        ).scalar() if hasattr(OrchidRecord, 'eol_page_id') else 0
        
        return jsonify({
            'total_records': total_records,
            'total_genera': total_genera,
            'total_species': total_species,
            'records_with_images': records_with_images,
            'image_coverage_percent': round((records_with_images / total_records * 100), 2) if total_records > 0 else 0,
            'records_with_habitat': records_with_habitat,
            'habitat_coverage_percent': round((records_with_habitat / total_records * 100), 2) if total_records > 0 else 0,
            'records_enriched_gbif': records_with_gbif,
            'records_enriched_eol': records_with_eol,
            'enrichment_stats': {
                'gbif_percent': round((records_with_gbif / total_records * 100), 2) if total_records > 0 else 0,
                'eol_percent': round((records_with_eol / total_records * 100), 2) if total_records > 0 else 0
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@julius_api.route('/stats/by-genus')
@require_api_key
@log_query
def stats_by_genus():
    """Get statistics grouped by genus"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        genus_stats = db.session.query(
            OrchidRecord.genus,
            func.count(OrchidRecord.id).label('total_records'),
            func.count(distinct(OrchidRecord.species)).label('species_count'),
            func.count(OrchidRecord.image_url).label('with_images'),
            func.count(OrchidRecord.native_habitat).label('with_habitat')
        ).group_by(OrchidRecord.genus).order_by(func.count(OrchidRecord.id).desc()).limit(limit).all()
        
        results = []
        for genus, total, species, images, habitat in genus_stats:
            results.append({
                'genus': genus,
                'total_records': total,
                'species_count': species,
                'records_with_images': images,
                'image_coverage': round((images / total * 100), 2) if total > 0 else 0,
                'records_with_habitat': habitat,
                'habitat_coverage': round((habitat / total * 100), 2) if total > 0 else 0
            })
        
        return jsonify({
            'count': len(results),
            'genera': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@julius_api.route('/stats/enrichment-status')
@require_api_key
def enrichment_status():
    """Get enrichment status breakdown"""
    try:
        total = db.session.query(func.count(OrchidRecord.id)).scalar()
        
        # Use taxon keys to determine enrichment status
        both_enriched = db.session.query(func.count(OrchidRecord.id)).filter(
            and_(
                OrchidRecord.gbif_taxon_key.isnot(None) if hasattr(OrchidRecord, 'gbif_taxon_key') else True,
                OrchidRecord.eol_page_id.isnot(None) if hasattr(OrchidRecord, 'eol_page_id') else True
            )
        ).scalar() if hasattr(OrchidRecord, 'gbif_taxon_key') and hasattr(OrchidRecord, 'eol_page_id') else 0
        
        only_gbif = db.session.query(func.count(OrchidRecord.id)).filter(
            and_(
                OrchidRecord.gbif_taxon_key.isnot(None) if hasattr(OrchidRecord, 'gbif_taxon_key') else False,
                OrchidRecord.eol_page_id.is_(None) if hasattr(OrchidRecord, 'eol_page_id') else True
            )
        ).scalar() if hasattr(OrchidRecord, 'gbif_taxon_key') else 0
        
        only_eol = db.session.query(func.count(OrchidRecord.id)).filter(
            and_(
                OrchidRecord.gbif_taxon_key.is_(None) if hasattr(OrchidRecord, 'gbif_taxon_key') else True,
                OrchidRecord.eol_page_id.isnot(None) if hasattr(OrchidRecord, 'eol_page_id') else False
            )
        ).scalar() if hasattr(OrchidRecord, 'eol_page_id') else 0
        
        not_enriched = total - both_enriched - only_gbif - only_eol
        
        return jsonify({
            'total_records': total,
            'enrichment_breakdown': {
                'both_sources': {
                    'count': both_enriched,
                    'percent': round((both_enriched / total * 100), 2) if total > 0 else 0
                },
                'gbif_only': {
                    'count': only_gbif,
                    'percent': round((only_gbif / total * 100), 2) if total > 0 else 0
                },
                'eol_only': {
                    'count': only_eol,
                    'percent': round((only_eol / total * 100), 2) if total > 0 else 0
                },
                'not_enriched': {
                    'count': not_enriched,
                    'percent': round((not_enriched / total * 100), 2) if total > 0 else 0
                }
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@julius_api.route('/orchids/search')
@require_api_key
def search_orchids():
    """Search orchids with filters"""
    try:
        query = db.session.query(OrchidRecord)
        
        # Filter by genus
        genus = request.args.get('genus')
        if genus:
            query = query.filter(OrchidRecord.genus.ilike(f'%{genus}%'))
        
        # Filter by species
        species = request.args.get('species')
        if species:
            query = query.filter(OrchidRecord.species.ilike(f'%{species}%'))
        
        # Filter by has_image
        has_image = request.args.get('has_image')
        if has_image == 'true':
            query = query.filter(OrchidRecord.image_url.isnot(None))
        elif has_image == 'false':
            query = query.filter(OrchidRecord.image_url.is_(None))
        
        # Filter by enrichment status (using taxon keys)
        gbif_enriched = request.args.get('gbif_enriched')
        if gbif_enriched == 'true' and hasattr(OrchidRecord, 'gbif_taxon_key'):
            query = query.filter(OrchidRecord.gbif_taxon_key.isnot(None))
        
        eol_enriched = request.args.get('eol_enriched')
        if eol_enriched == 'true' and hasattr(OrchidRecord, 'eol_page_id'):
            query = query.filter(OrchidRecord.eol_page_id.isnot(None))
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        per_page = min(per_page, 500)  # Max 500 per page
        
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        results = []
        for orchid in paginated.items:
            results.append({
                'id': orchid.id,
                'genus': orchid.genus,
                'species': orchid.species,
                'full_name': f"{orchid.genus} {orchid.species}",
                'common_name': orchid.common_names if hasattr(orchid, 'common_names') else None,
                'has_image': orchid.image_url is not None,
                'native_habitat': orchid.native_habitat if hasattr(orchid, 'native_habitat') else None,
                'bloom_time': orchid.bloom_time if hasattr(orchid, 'bloom_time') else None,
                'water_requirements': orchid.water_requirements if hasattr(orchid, 'water_requirements') else None,
                'has_gbif_data': orchid.gbif_taxon_key is not None if hasattr(orchid, 'gbif_taxon_key') else False,
                'has_eol_data': orchid.eol_page_id is not None if hasattr(orchid, 'eol_page_id') else False,
                'created_at': orchid.created_at.isoformat() if orchid.created_at else None
            })
        
        return jsonify({
            'count': len(results),
            'total': paginated.total,
            'page': page,
            'pages': paginated.pages,
            'per_page': per_page,
            'orchids': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@julius_api.route('/orchids/<int:orchid_id>')
@require_api_key
def get_orchid_detail(orchid_id):
    """Get detailed information for a specific orchid"""
    try:
        orchid = OrchidRecord.query.get_or_404(orchid_id)
        
        return jsonify({
            'id': orchid.id,
            'genus': orchid.genus,
            'species': orchid.species,
            'full_name': f"{orchid.genus} {orchid.species}",
            'common_name': orchid.common_names if hasattr(orchid, 'common_names') else None,
            'author': orchid.author if hasattr(orchid, 'author') else None,
            'has_image': orchid.image_url is not None,
            'image_url': orchid.image_url if hasattr(orchid, 'image_url') else None,
            'native_habitat': orchid.native_habitat if hasattr(orchid, 'native_habitat') else None,
            'bloom_time': orchid.bloom_time if hasattr(orchid, 'bloom_time') else None,
            'water_requirements': orchid.water_requirements if hasattr(orchid, 'water_requirements') else None,
            'light_requirements': orchid.light_requirements if hasattr(orchid, 'light_requirements') else None,
            'temperature_min': orchid.temperature_min if hasattr(orchid, 'temperature_min') else None,
            'temperature_max': orchid.temperature_max if hasattr(orchid, 'temperature_max') else None,
            'has_gbif_data': orchid.gbif_taxon_key is not None if hasattr(orchid, 'gbif_taxon_key') else False,
            'has_eol_data': orchid.eol_page_id is not None if hasattr(orchid, 'eol_page_id') else False,
            'gbif_taxon_key': orchid.gbif_taxon_key if hasattr(orchid, 'gbif_taxon_key') else None,
            'eol_page_id': orchid.eol_page_id if hasattr(orchid, 'eol_page_id') else None,
            'source': orchid.source,
            'photographer': orchid.photographer,
            'created_at': orchid.created_at.isoformat() if orchid.created_at else None,
            'updated_at': orchid.updated_at.isoformat() if orchid.updated_at else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@julius_api.route('/taxonomy/list')
@require_api_key
def list_taxonomy():
    """Get list of all taxonomy entries"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        taxonomies = OrchidTaxonomy.query.limit(limit).all()
        
        results = []
        for tax in taxonomies:
            results.append({
                'id': tax.id,
                'genus': tax.genus,
                'species': tax.species,
                'full_name': f"{tax.genus} {tax.species}" if tax.species else tax.genus,
                'common_name': tax.common_name,
                'family': tax.family,
                'subfamily': tax.subfamily,
                'source': tax.source
            })
        
        return jsonify({
            'count': len(results),
            'taxonomies': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@julius_api.route('/get-api-key')
def get_api_key():
    """Get API key for Julius AI integration (admin access recommended)"""
    # For security, you might want to add authentication here
    return jsonify({
        'api_key': JULIUS_API_KEY,
        'note': 'Keep this key secure. Use it in Julius AI to access Orchid Continuum data.',
        'documentation': '/api/julius/docs'
    })

@julius_api.route('/docs')
def api_documentation():
    """API documentation (no auth required for docs)"""
    return jsonify({
        'service': 'Orchid Continuum Julius AI API',
        'version': '1.0.0',
        'authentication': {
            'type': 'API Key',
            'methods': [
                'Header: X-API-Key: your_api_key',
                'Header: Authorization: Bearer your_api_key',
                'Query parameter: ?api_key=your_api_key'
            ],
            'note': 'Get your API key from /api/julius/get-api-key'
        },
        'endpoints': {
            'GET /api/julius/health': 'Health check',
            'GET /api/julius/stats/overview': 'Overall statistics',
            'GET /api/julius/stats/by-genus': 'Statistics by genus (params: limit)',
            'GET /api/julius/stats/enrichment-status': 'Enrichment status breakdown',
            'GET /api/julius/orchids/search': 'Search orchids (params: genus, species, has_image, gbif_enriched, eol_enriched, page, per_page)',
            'GET /api/julius/orchids/<id>': 'Get orchid details',
            'GET /api/julius/taxonomy/list': 'List taxonomy entries (params: limit)',
            'GET /api/julius/glossary': 'Get botanical glossary terms (params: page, per_page, category, search, has_etymology)',
            'GET /api/julius/keys': 'Get dichotomous key sources (params: page, per_page, genus, region, key_type)',
            'GET /api/julius/images/gbif': 'Get GBIF image metadata (params: page, per_page, genus, has_coordinates)',
            'GET /api/julius/docs': 'This documentation'
        },
        'examples': {
            'overview_stats': '/api/julius/stats/overview?api_key=YOUR_KEY',
            'top_genera': '/api/julius/stats/by-genus?limit=20&api_key=YOUR_KEY',
            'search_phalaenopsis': '/api/julius/orchids/search?genus=Phalaenopsis&api_key=YOUR_KEY',
            'enriched_orchids': '/api/julius/orchids/search?gbif_enriched=true&api_key=YOUR_KEY',
            'glossary_morphology': '/api/julius/glossary?category=morphology&has_etymology=true',
            'cattleya_keys': '/api/julius/keys?genus=Cattleya',
            'california_keys': '/api/julius/keys?region=California',
            'gbif_georeferenced': '/api/julius/images/gbif?has_coordinates=true&genus=Dendrobium'
        }
    })


# ===== NEW ENDPOINTS FOR GLOSSARY, KEYS, TAXONOMY & GBIF IMAGES =====

@julius_api.route('/glossary')
@require_api_key
@log_query
def get_glossary():
    """Get botanical glossary terms with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 100, type=int), 500)
    category = request.args.get('category')
    search = request.args.get('search')
    has_etymology = request.args.get('has_etymology')
    
    query = OCUGlossaryTerm.query
    
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(or_(
            OCUGlossaryTerm.term.ilike(f'%{search}%'),
            OCUGlossaryTerm.definition.ilike(f'%{search}%')
        ))
    if has_etymology == 'true':
        query = query.filter(OCUGlossaryTerm.etymology.isnot(None))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'status': 'success',
        'data': {
            'terms': [{
                'id': t.id,
                'term': t.term,
                'definition': t.definition,
                'etymology': t.etymology,
                'pronunciation': t.pronunciation,
                'category': t.category
            } for t in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }
    })


@julius_api.route('/keys')
@require_api_key
@log_query
def get_dichotomous_keys():
    """Get dichotomous key sources"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 200)
    genus = request.args.get('genus')
    region = request.args.get('region')
    key_type = request.args.get('key_type')
    
    sql = """
        SELECT id, genus, species, source_organization, source_url,
               key_type, morphological_characters, key_text, key_metadata
        FROM orchid_taxonomic_keys
        WHERE 1=1
    """
    params = {}
    
    if genus:
        sql += " AND genus = :genus"
        params['genus'] = genus
    if region:
        sql += " AND key_metadata->>'region' ILIKE :region"
        params['region'] = f'%{region}%'
    if key_type:
        sql += " AND key_type = :key_type"
        params['key_type'] = key_type
    
    sql += " ORDER BY genus, source_organization"
    sql += f" LIMIT :per_page OFFSET :offset"
    params['per_page'] = per_page
    params['offset'] = (page - 1) * per_page
    
    count_sql = sql.replace('SELECT id, genus', 'SELECT COUNT(*) as total').split('ORDER BY')[0]
    total_result = db.session.execute(text(count_sql), params).fetchone()
    total = total_result[0] if total_result else 0
    
    result = db.session.execute(text(sql), params)
    
    keys = []
    for row in result:
        keys.append({
            'id': row[0],
            'genus': row[1],
            'source': row[3],
            'url': row[4],
            'type': row[5],
            'description': row[7],
            'metadata': row[8] or {}
        })
    
    return jsonify({
        'status': 'success',
        'data': {
            'keys': keys,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }
    })


@julius_api.route('/images/gbif')
@require_api_key
@log_query
def get_gbif_images():
    """Get GBIF orchid image metadata"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 200)
    genus_filter = request.args.get('genus')
    has_coordinates = request.args.get('has_coordinates')
    
    sql = """
        SELECT i.id, i.gbif_id, i.image_url, i.scientific_name,
               i.latitude, i.longitude, i.country, i.locality,
               i.recorded_by, i.collection_date,
               t.genus, t.species
        FROM orchid_images i
        LEFT JOIN orchid_taxonomy t ON i.taxonomy_id = t.id
        WHERE 1=1
    """
    params = {}
    
    if genus_filter:
        sql += " AND t.genus = :genus"
        params['genus'] = genus_filter
    if has_coordinates == 'true':
        sql += " AND i.latitude IS NOT NULL AND i.longitude IS NOT NULL"
    
    sql += " ORDER BY i.id DESC"
    sql += f" LIMIT :per_page OFFSET :offset"
    params['per_page'] = per_page
    params['offset'] = (page - 1) * per_page
    
    count_sql = sql.replace('SELECT i.id, i.gbif_id', 'SELECT COUNT(*) as total').split('ORDER BY')[0]
    total_result = db.session.execute(text(count_sql), params).fetchone()
    total = total_result[0] if total_result else 0
    
    result = db.session.execute(text(sql), params)
    
    images = []
    for row in result:
        images.append({
            'id': row[0],
            'gbif_id': row[1],
            'image_url': row[2],
            'scientific_name': row[3],
            'latitude': row[4],
            'longitude': row[5],
            'country': row[6],
            'genus': row[10],
            'species': row[11]
        })
    
    return jsonify({
        'status': 'success',
        'data': {
            'images': images,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total
            }
        }
    })


# Register blueprint in main app
def register_julius_api(app):
    """Register Julius API blueprint with the Flask app"""
    app.register_blueprint(julius_api)
    print(f"✅ Julius AI API registered with key: {JULIUS_API_KEY[:20]}...")
