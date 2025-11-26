#!/usr/bin/env python3
"""
Simple API for external AI access to Orchid Database
Usage: Give the API key to Julius or other AIs
"""
import os
import json
import secrets
from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

# Generate a secure API key (or use existing one)
API_KEY = os.environ.get('ORCHID_API_KEY', 'oc_' + secrets.token_hex(16))

def get_db():
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({'error': 'Invalid API key'}), 401
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM orchid_taxonomy")
    total_species = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM orchid_images")
    total_images = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(DISTINCT taxonomy_id) FROM orchid_images WHERE taxonomy_id IS NOT NULL")
    species_with_images = cur.fetchone()[0]
    
    cur.execute("""
        SELECT image_source, COUNT(*) 
        FROM orchid_images 
        GROUP BY image_source 
        ORDER BY COUNT(*) DESC
    """)
    sources = dict(cur.fetchall())
    
    conn.close()
    
    return jsonify({
        'total_species': total_species,
        'total_images': total_images,
        'species_with_images': species_with_images,
        'images_by_source': sources
    })

@app.route('/api/v1/species', methods=['GET'])
def get_species():
    """Get species list with image counts"""
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({'error': 'Invalid API key'}), 401
    
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    genus = request.args.get('genus', None)
    
    conn = get_db()
    cur = conn.cursor()
    
    query = """
        SELECT t.id, t.genus, t.species, t.author, 
               COUNT(i.id) as image_count
        FROM orchid_taxonomy t
        LEFT JOIN orchid_images i ON t.id = i.taxonomy_id
    """
    
    params = []
    if genus:
        query += " WHERE LOWER(t.genus) = LOWER(%s)"
        params.append(genus)
    
    query += " GROUP BY t.id, t.genus, t.species, t.author"
    query += " ORDER BY image_count DESC"
    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    cur.execute(query, params)
    
    species = []
    for row in cur.fetchall():
        species.append({
            'id': row[0],
            'genus': row[1],
            'species': row[2],
            'author': row[3],
            'image_count': row[4]
        })
    
    conn.close()
    
    return jsonify({'species': species, 'count': len(species)})

@app.route('/api/v1/images/<int:taxonomy_id>', methods=['GET'])
def get_images(taxonomy_id):
    """Get images for a specific species"""
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({'error': 'Invalid API key'}), 401
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, image_url, image_source, country, image_license
        FROM orchid_images
        WHERE taxonomy_id = %s
        LIMIT 50
    """, (taxonomy_id,))
    
    images = []
    for row in cur.fetchall():
        images.append({
            'id': row[0],
            'url': row[1],
            'source': row[2],
            'country': row[3],
            'license': row[4]
        })
    
    conn.close()
    
    return jsonify({'images': images, 'count': len(images)})

if __name__ == '__main__':
    print(f"\n🔑 ORCHID API KEY: {API_KEY}")
    print(f"\nShare this with Julius AI to access your database.")
    print(f"\nEndpoints:")
    print(f"  GET /api/v1/stats - Database statistics")
    print(f"  GET /api/v1/species?limit=100&genus=Phalaenopsis - Species list")
    print(f"  GET /api/v1/images/<taxonomy_id> - Images for species")
    print(f"\nHeader required: X-API-Key: {API_KEY}")
    app.run(host='0.0.0.0', port=5001)
