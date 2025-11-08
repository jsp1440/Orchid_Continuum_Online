"""
Taxonomy Widget Suite API Blueprint
Provides lightweight, read-only JSON endpoints for embeddable taxonomy widgets
No external dependencies, portable across SQLite/PostgreSQL
"""

import os
import logging
import random
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy import text, func
from app import db

bp_taxonomy = Blueprint('taxonomy', __name__)

# Simple in-memory cache with TTL
_cache = {}
_cache_ttl = {}
CACHE_DURATION = timedelta(minutes=15)

def cached_query(key, query_func, ttl_minutes=15):
    """Simple cache helper with TTL"""
    now = datetime.now()
    if key in _cache and key in _cache_ttl:
        if now < _cache_ttl[key]:
            return _cache[key]
    
    result = query_func()
    _cache[key] = result
    _cache_ttl[key] = now + timedelta(minutes=ttl_minutes)
    return result

@bp_taxonomy.route('/taxonomy/genera', methods=['GET'])
def get_genera():
    """GET /api/taxonomy/genera - Returns list of all unique genera"""
    try:
        def fetch_genera():
            query = text("""
                SELECT DISTINCT genus 
                FROM orchid_taxonomy 
                WHERE genus IS NOT NULL AND genus != '' 
                ORDER BY genus
            """)
            result = db.session.execute(query)
            return [row[0] for row in result]
        
        genera = cached_query('all_genera', fetch_genera, ttl_minutes=60)
        return jsonify(genera)
    except Exception as e:
        logging.error(f"Error fetching genera: {e}")
        return jsonify({"error": "Unable to fetch genera", "demo": True, "data": [
            "Phalaenopsis", "Cattleya", "Dendrobium", "Vanilla", "Cymbidium"
        ]}), 200

@bp_taxonomy.route('/taxonomy/search', methods=['GET'])
def search_taxonomy():
    """GET /api/taxonomy/search?q=&genus=&page=1&limit=12"""
    try:
        query_text = request.args.get('q', '').strip()
        genus_filter = request.args.get('genus', '').strip()
        page = max(1, int(request.args.get('page', 1)))
        limit = min(100, max(1, int(request.args.get('limit', 12))))
        offset = (page - 1) * limit
        
        # Build query
        conditions = ["1=1"]
        params = {}
        
        if query_text:
            conditions.append("(scientific_name ILIKE :query OR genus ILIKE :query OR species ILIKE :query OR common_names ILIKE :query)")
            params['query'] = f'%{query_text}%'
        
        if genus_filter:
            conditions.append("genus = :genus")
            params['genus'] = genus_filter
        
        where_clause = " AND ".join(conditions)
        
        # Count total
        count_query = text(f"SELECT COUNT(*) FROM orchid_taxonomy WHERE {where_clause}")
        total = db.session.execute(count_query, params).scalar()
        
        # Fetch results
        data_query = text(f"""
            SELECT id, scientific_name, genus, species, author, common_names, 
                   country, state_province, image_url, latitude, longitude
            FROM orchid_taxonomy 
            WHERE {where_clause}
            ORDER BY scientific_name
            LIMIT :limit OFFSET :offset
        """)
        params.update({'limit': limit, 'offset': offset})
        
        result = db.session.execute(data_query, params)
        rows = []
        for row in result:
            rows.append({
                'id': row[0],
                'scientific_name': row[1],
                'genus': row[2],
                'species': row[3],
                'author': row[4],
                'common_names': row[5],
                'distribution': f"{row[6] or ''} {row[7] or ''}".strip() or None,
                'image_url': row[8],
                'latitude': float(row[9]) if row[9] else None,
                'longitude': float(row[10]) if row[10] else None
            })
        
        return jsonify({
            'results': rows,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        })
    
    except Exception as e:
        logging.error(f"Search error: {e}")
        return jsonify({"error": "Search unavailable", "results": [], "total": 0}), 200

@bp_taxonomy.route('/taxonomy/random', methods=['GET'])
def get_random():
    """GET /api/taxonomy/random - Returns a random orchid"""
    try:
        query = text("""
            SELECT id, scientific_name, genus, species, author, common_names, 
                   country, state_province, image_url
            FROM orchid_taxonomy 
            WHERE scientific_name IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 1
        """)
        result = db.session.execute(query).fetchone()
        
        if result:
            return jsonify({
                'id': result[0],
                'scientific_name': result[1],
                'genus': result[2],
                'species': result[3],
                'author': result[4],
                'common_names': result[5],
                'distribution': f"{result[6] or ''} {result[7] or ''}".strip() or None,
                'image_url': result[8]
            })
        else:
            return jsonify({"error": "No records found"}), 404
    
    except Exception as e:
        logging.error(f"Random orchid error: {e}")
        return jsonify({"error": "Unable to fetch random orchid"}), 500

@bp_taxonomy.route('/taxonomy/bloomdata', methods=['GET'])
def get_bloom_data():
    """GET /api/taxonomy/bloomdata?genus= - Returns seasonal bloom pattern"""
    try:
        genus = request.args.get('genus', '').strip()
        if not genus:
            return jsonify({"error": "Genus parameter required"}), 400
        
        # Try to get real data from month_observed
        query = text("""
            SELECT month_observed, COUNT(*) as count
            FROM orchid_taxonomy
            WHERE genus = :genus AND month_observed IS NOT NULL
            GROUP BY month_observed
            ORDER BY month_observed
        """)
        result = db.session.execute(query, {'genus': genus})
        
        months_data = {i: 0 for i in range(1, 13)}
        has_real_data = False
        
        for row in result:
            if row[0] and 1 <= row[0] <= 12:
                months_data[row[0]] = row[1]
                has_real_data = True
        
        if has_real_data:
            return jsonify({
                'genus': genus,
                'months': [months_data[i] for i in range(1, 13)],
                'demo': False,
                'note': 'Based on observation data'
            })
        else:
            # Return demo pattern
            demo_pattern = [2, 3, 8, 15, 20, 15, 8, 5, 3, 2, 1, 2]  # Spring peak
            return jsonify({
                'genus': genus,
                'months': demo_pattern,
                'demo': True,
                'note': 'Demo data - actual bloom times may vary'
            })
    
    except Exception as e:
        logging.error(f"Bloom data error: {e}")
        demo_pattern = [2, 3, 8, 15, 20, 15, 8, 5, 3, 2, 1, 2]
        return jsonify({
            'genus': genus if 'genus' in locals() else 'Unknown',
            'months': demo_pattern,
            'demo': True,
            'error': str(e)
        }), 200

@bp_taxonomy.route('/taxonomy/distribution', methods=['GET'])
def get_distribution():
    """GET /api/taxonomy/distribution?genus= - Returns geographic distribution"""
    try:
        genus = request.args.get('genus', '').strip()
        if not genus:
            return jsonify({"error": "Genus parameter required"}), 400
        
        query = text("""
            SELECT country, continent, COUNT(*) as count
            FROM orchid_taxonomy
            WHERE genus = :genus AND country IS NOT NULL
            GROUP BY country, continent
            ORDER BY count DESC
            LIMIT 10
        """)
        result = db.session.execute(query, {'genus': genus})
        
        regions = []
        for row in result:
            regions.append({
                'country': row[0],
                'continent': row[1],
                'count': row[2]
            })
        
        if regions:
            return jsonify({
                'genus': genus,
                'regions': regions,
                'demo': False
            })
        else:
            return jsonify({
                'genus': genus,
                'regions': [
                    {'country': 'Demo', 'continent': 'Unknown', 'count': 0}
                ],
                'demo': True,
                'note': 'No distribution data available'
            })
    
    except Exception as e:
        logging.error(f"Distribution error: {e}")
        return jsonify({
            'genus': genus if 'genus' in locals() else 'Unknown',
            'regions': [],
            'demo': True,
            'error': str(e)
        }), 200

@bp_taxonomy.route('/taxonomy/pollinator', methods=['GET'])
def get_pollinator():
    """GET /api/taxonomy/pollinator?species= - Returns pollinator quiz question"""
    try:
        species_name = request.args.get('species', '').strip()
        
        # Get species info
        if species_name:
            query = text("""
                SELECT scientific_name, genus, habitat_description, common_names
                FROM orchid_taxonomy
                WHERE scientific_name ILIKE :species OR species ILIKE :species
                LIMIT 1
            """)
            result = db.session.execute(query, {'species': f'%{species_name}%'}).fetchone()
        else:
            # Random species
            query = text("""
                SELECT scientific_name, genus, habitat_description, common_names
                FROM orchid_taxonomy
                WHERE scientific_name IS NOT NULL
                ORDER BY RANDOM()
                LIMIT 1
            """)
            result = db.session.execute(query).fetchone()
        
        if not result:
            return jsonify({"error": "Species not found"}), 404
        
        scientific_name, genus, habitat, common_name = result
        
        # Simple heuristic for pollinator
        options = ['Bee', 'Moth', 'Hummingbird', 'Fly', 'Wind', 'Unknown']
        
        # Basic inference
        correct_index = 5  # Default to Unknown
        rationale = "Pollinator data not available in database."
        
        # Simple pattern matching
        if habitat:
            habitat_lower = habitat.lower()
            if 'night' in habitat_lower or 'evening' in habitat_lower:
                correct_index = 1  # Moth
                rationale = "Night-blooming orchids are typically pollinated by moths."
            elif 'bee' in habitat_lower:
                correct_index = 0
                rationale = "Habitat notes suggest bee pollination."
        
        # Shuffle options but remember correct answer
        correct_answer = options[correct_index]
        random.shuffle(options)
        new_correct_index = options.index(correct_answer)
        
        return jsonify({
            'species': scientific_name,
            'genus': genus,
            'common_name': common_name,
            'options': options,
            'correct_index': new_correct_index,
            'rationale': rationale,
            'demo': True  # Always demo until we have real pollinator data
        })
    
    except Exception as e:
        logging.error(f"Pollinator error: {e}")
        return jsonify({"error": "Unable to generate pollinator quiz"}), 500

@bp_taxonomy.route('/taxonomy/quiz/mystery', methods=['GET'])
def get_mystery_quiz():
    """GET /api/taxonomy/quiz/mystery - Returns mystery orchid quiz question"""
    try:
        # Get random species
        query = text("""
            SELECT id, scientific_name, genus, species, author, image_url, 
                   country, state_province
            FROM orchid_taxonomy
            WHERE genus IS NOT NULL AND scientific_name IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 1
        """)
        result = db.session.execute(query).fetchone()
        
        if not result:
            return jsonify({"error": "No records available"}), 404
        
        orchid_id, sci_name, correct_genus, species, author, image_url, country, state = result
        
        # Get 3 random distractor genera (different from correct)
        distractor_query = text("""
            SELECT DISTINCT genus
            FROM orchid_taxonomy
            WHERE genus IS NOT NULL AND genus != :correct_genus
            ORDER BY RANDOM()
            LIMIT 3
        """)
        distractors = db.session.execute(distractor_query, {'correct_genus': correct_genus})
        distractor_genera = [row[0] for row in distractors]
        
        # Build options list
        options = [correct_genus] + distractor_genera
        random.shuffle(options)
        correct_index = options.index(correct_genus)
        
        distribution = f"{country or ''} {state or ''}".strip() or "Unknown"
        
        return jsonify({
            'question': f'What genus does this orchid belong to?',
            'species_hint': species or 'Unknown species',
            'options': options,
            'correct_index': correct_index,
            'species': sci_name,
            'genus': correct_genus,
            'author': author,
            'image_url': image_url,
            'distribution': distribution
        })
    
    except Exception as e:
        logging.error(f"Mystery quiz error: {e}")
        return jsonify({"error": "Unable to generate quiz"}), 500

@bp_taxonomy.route('/member/taxonomy/resolve', methods=['POST'])
def resolve_member_taxonomy():
    """POST /api/member/taxonomy/resolve - Batch resolve plant names to taxonomy"""
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({"error": "Missing 'items' array in request body"}), 400
        
        items = data['items'][:50]  # Limit to 50 items
        results = []
        
        for item in items:
            if not item or not isinstance(item, str):
                continue
            
            search_term = item.strip()
            if not search_term:
                continue
            
            # Try to find match
            query = text("""
                SELECT id, scientific_name, genus, species, author, common_names,
                       country, habitat_description, image_url
                FROM orchid_taxonomy
                WHERE scientific_name ILIKE :term 
                   OR genus ILIKE :term
                   OR common_names ILIKE :term
                LIMIT 3
            """)
            matches = db.session.execute(query, {'term': f'%{search_term}%'})
            
            matched_records = []
            for row in matches:
                matched_records.append({
                    'id': row[0],
                    'scientific_name': row[1],
                    'genus': row[2],
                    'species': row[3],
                    'author': row[4],
                    'common_names': row[5],
                    'native_region': row[6],
                    'habitat': row[7],
                    'image_url': row[8],
                    'confidence': 'high' if row[1].lower() == search_term.lower() else 'medium'
                })
            
            results.append({
                'input': search_term,
                'matches': matched_records,
                'match_count': len(matched_records)
            })
        
        return jsonify({
            'resolved': results,
            'total_input': len(items),
            'total_matched': sum(1 for r in results if r['match_count'] > 0)
        })
    
    except Exception as e:
        logging.error(f"Taxonomy resolve error: {e}")
        return jsonify({"error": "Unable to resolve taxonomy"}), 500

@bp_taxonomy.route('/ai/status', methods=['GET'])
def get_ai_status():
    """GET /api/ai/status - Returns AI feature status"""
    ai_enabled = os.environ.get('ORCHID_AI_ENABLED', 'false').lower() == 'true'
    return jsonify({
        'status': 'enabled' if ai_enabled else 'disabled',
        'message': 'AI features active' if ai_enabled else 'AI features paused to conserve resources'
    })

logging.info("✅ Taxonomy Widget Suite API blueprint loaded")
