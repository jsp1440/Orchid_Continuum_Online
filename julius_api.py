#!/usr/bin/env python3
"""
Julius AI Coordination API - Orchid Continuum
RESTful API for Julius AI to access and contribute to species coverage
"""
import os
import json
import psycopg2
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Allow Julius to call from external

# Authentication (simple API key)
JULIUS_API_KEY = os.environ.get('JULIUS_API_KEY', '')

def verify_api_key():
    """Verify Julius API key"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    token = auth_header.replace('Bearer ', '')
    return token == JULIUS_API_KEY

def get_db():
    """Get database connection"""
    return psycopg2.connect(os.environ['DATABASE_URL'])

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Orchid Continuum Julius API',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/coverage/summary', methods=['GET'])
def coverage_summary():
    """Get overall species coverage summary"""
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get overall stats
    cur.execute("SELECT COUNT(*) FROM orchid_taxonomy")
    total_species = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(DISTINCT taxonomy_id) FROM orchid_images WHERE taxonomy_id IS NOT NULL")
    species_with_images = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM orchid_images")
    total_images = cur.fetchone()[0]
    
    # AI readiness breakdown
    cur.execute("""
        SELECT 
            CASE 
                WHEN img_count = 0 THEN 'no_images'
                WHEN img_count < 10 THEN 'insufficient'
                WHEN img_count < 30 THEN 'minimum'
                WHEN img_count < 50 THEN 'ideal'
                ELSE 'excellent'
            END as category,
            COUNT(*) as species_count
        FROM (
            SELECT ot.id, COUNT(oi.id) as img_count
            FROM orchid_taxonomy ot
            LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
            GROUP BY ot.id
        ) counts
        GROUP BY category
    """)
    
    breakdown = dict(cur.fetchall())
    
    cur.close()
    conn.close()
    
    return jsonify({
        'total_species': total_species,
        'species_with_images': species_with_images,
        'species_missing': total_species - species_with_images,
        'total_images': total_images,
        'coverage_percent': round((species_with_images / total_species) * 100, 2),
        'ai_readiness': {
            'no_images': breakdown.get('no_images', 0),
            'insufficient_1_9': breakdown.get('insufficient', 0),
            'minimum_10_29': breakdown.get('minimum', 0),
            'ideal_30_49': breakdown.get('ideal', 0),
            'excellent_50_plus': breakdown.get('excellent', 0)
        },
        'ai_ready_species': breakdown.get('ideal', 0) + breakdown.get('excellent', 0),
        'ai_ready_percent': round(((breakdown.get('ideal', 0) + breakdown.get('excellent', 0)) / total_species) * 100, 2)
    })

@app.route('/api/species/missing', methods=['GET'])
def get_missing_species():
    """Get list of species needing images"""
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    limit = request.args.get('limit', 100, type=int)
    priority = request.args.get('priority', 'CRITICAL')  # CRITICAL, HIGH, MEDIUM
    
    # Map priority to image count threshold
    threshold_map = {
        'CRITICAL': 0,  # No images
        'HIGH': 9,      # 1-9 images
        'MEDIUM': 29    # 10-29 images
    }
    max_images = threshold_map.get(priority, 0)
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            ot.id,
            ot.scientific_name,
            ot.genus,
            ot.species,
            COUNT(oi.id) as current_images,
            (30 - COUNT(oi.id)) as images_needed
        FROM orchid_taxonomy ot
        LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
        WHERE ot.scientific_name IS NOT NULL
        GROUP BY ot.id, ot.scientific_name, ot.genus, ot.species
        HAVING COUNT(oi.id) <= %s
        ORDER BY COUNT(oi.id) ASC, ot.scientific_name
        LIMIT %s
    """, (max_images, limit))
    
    species_list = []
    for row in cur.fetchall():
        species_list.append({
            'taxonomy_id': row[0],
            'scientific_name': row[1],
            'genus': row[2],
            'species': row[3],
            'current_images': row[4],
            'images_needed': max(0, row[5])
        })
    
    cur.close()
    conn.close()
    
    return jsonify({
        'priority': priority,
        'count': len(species_list),
        'species': species_list
    })

@app.route('/api/species/by-genus/<genus>', methods=['GET'])
def get_species_by_genus(genus):
    """Get all species in a specific genus with coverage stats"""
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            ot.id,
            ot.scientific_name,
            ot.species,
            COUNT(oi.id) as image_count,
            CASE 
                WHEN COUNT(oi.id) >= 30 THEN 'ai_ready'
                WHEN COUNT(oi.id) >= 10 THEN 'minimum'
                WHEN COUNT(oi.id) > 0 THEN 'insufficient'
                ELSE 'no_images'
            END as status
        FROM orchid_taxonomy ot
        LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
        WHERE ot.genus = %s
        GROUP BY ot.id, ot.scientific_name, ot.species
        ORDER BY image_count ASC, ot.scientific_name
    """, (genus,))
    
    species_list = []
    for row in cur.fetchall():
        species_list.append({
            'taxonomy_id': row[0],
            'scientific_name': row[1],
            'species': row[2],
            'image_count': row[3],
            'status': row[4]
        })
    
    cur.close()
    conn.close()
    
    return jsonify({
        'genus': genus,
        'species_count': len(species_list),
        'species': species_list
    })

@app.route('/api/images/submit', methods=['POST'])
def submit_images():
    """Julius can submit discovered image URLs for a species"""
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    taxonomy_id = data.get('taxonomy_id')
    images = data.get('images', [])  # List of image objects
    
    if not taxonomy_id or not images:
        return jsonify({'error': 'Missing taxonomy_id or images'}), 400
    
    conn = get_db()
    cur = conn.cursor()
    
    inserted = 0
    for img in images:
        try:
            metadata = {
                'source': img.get('source', 'Julius AI'),
                'photographer': img.get('photographer'),
                'submitted_by': 'Julius AI',
                'submitted_at': datetime.now().isoformat()
            }
            
            cur.execute("""
                INSERT INTO orchid_images 
                (taxonomy_id, image_url, image_source, image_license,
                 latitude, longitude, observer_name, media_metadata, created_at)
                SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s
                WHERE NOT EXISTS (
                    SELECT 1 FROM orchid_images WHERE image_url = %s
                )
            """, (
                taxonomy_id,
                img.get('url'),
                img.get('source', 'Julius AI'),
                img.get('license'),
                img.get('latitude'),
                img.get('longitude'),
                img.get('photographer'),
                json.dumps(metadata),
                datetime.now(),
                img.get('url')
            ))
            
            if cur.rowcount > 0:
                inserted += 1
        
        except Exception as e:
            conn.rollback()
            continue
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({
        'success': True,
        'images_submitted': len(images),
        'images_inserted': inserted,
        'duplicates_skipped': len(images) - inserted
    })

@app.route('/api/progress/daily', methods=['GET'])
def daily_progress():
    """Get daily progress stats"""
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            DATE(created_at) as day,
            COUNT(*) as images_added,
            COUNT(DISTINCT taxonomy_id) as species_touched
        FROM orchid_images
        WHERE created_at >= NOW() - INTERVAL '30 days'
        GROUP BY DATE(created_at)
        ORDER BY day DESC
    """)
    
    daily_stats = []
    for row in cur.fetchall():
        daily_stats.append({
            'date': row[0].isoformat(),
            'images_added': row[1],
            'species_touched': row[2]
        })
    
    cur.close()
    conn.close()
    
    return jsonify({
        'period': 'last_30_days',
        'daily_stats': daily_stats
    })

@app.route('/api/genera/priority', methods=['GET'])
def priority_genera():
    """Get genera ranked by priority (most species with no images)"""
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    limit = request.args.get('limit', 50, type=int)
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            ot.genus,
            COUNT(DISTINCT ot.id) as total_species,
            COUNT(DISTINCT CASE WHEN oi.id IS NULL THEN ot.id END) as species_no_images,
            COUNT(DISTINCT CASE WHEN oi.id IS NOT NULL THEN ot.id END) as species_with_images,
            COALESCE(SUM(CASE WHEN oi.id IS NOT NULL THEN 1 ELSE 0 END), 0) as total_images
        FROM orchid_taxonomy ot
        LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
        WHERE ot.genus IS NOT NULL
        GROUP BY ot.genus
        HAVING COUNT(DISTINCT CASE WHEN oi.id IS NULL THEN ot.id END) > 0
        ORDER BY species_no_images DESC, total_species DESC
        LIMIT %s
    """, (limit,))
    
    genera = []
    for row in cur.fetchall():
        genera.append({
            'genus': row[0],
            'total_species': row[1],
            'species_no_images': row[2],
            'species_with_images': row[3],
            'total_images': row[4],
            'coverage_percent': round((row[3] / row[1]) * 100, 1) if row[1] > 0 else 0
        })
    
    cur.close()
    conn.close()
    
    return jsonify({
        'count': len(genera),
        'genera': genera
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
