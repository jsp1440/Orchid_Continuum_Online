#!/usr/bin/env python3
"""Simple parallel harvester - no complex queries"""
import os
import sys
import time
import requests
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')
INSTANCE_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 0
COUNTRIES = ['AU', 'PG', 'ID', 'MY', 'PH', 'TH', 'VN', 'CR', 'PA', 'KE', 'TZ', 'MG', 'ZA']

stats = {'added': 0, 'start': time.time()}

def get_my_species():
    """Get species where id MOD 8 = instance_id"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, scientific_name 
        FROM orchid_taxonomy 
        WHERE MOD(id, 8) = %s 
        LIMIT 500
    """, (INSTANCE_ID,))
    results = cur.fetchall()
    conn.close()
    return results

def fetch_gbif(species_name, country=None):
    """Fetch images from GBIF"""
    params = {
        'scientificName': species_name,
        'mediaType': 'StillImage',
        'limit': 3,
        'hasCoordinate': 'true'
    }
    if country:
        params['country'] = country
    
    try:
        r = requests.get("https://api.gbif.org/v1/occurrence/search", params=params, timeout=10)
        if r.status_code != 200:
            return []
        
        images = []
        for rec in r.json().get('results', []):
            for m in rec.get('media', []):
                if m.get('type') == 'StillImage' and m.get('identifier'):
                    images.append({
                        'url': m['identifier'],
                        'tax_id': None,
                        'country': rec.get('country'),
                        'lat': rec.get('decimalLatitude'),
                        'lon': rec.get('decimalLongitude'),
                        'year': rec.get('year'),
                        'gbif_key': str(rec.get('key', '')),
                    })
        return images
    except:
        return []

def save_image(img, tax_id):
    """Save image to database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Check if exists
        cur.execute("SELECT 1 FROM orchid_images WHERE image_url = %s", (img['url'],))
        if cur.fetchone():
            conn.close()
            return False
        
        # Insert
        cur.execute("""
            INSERT INTO orchid_images (
                taxonomy_id, image_url, image_source, image_type,
                country, latitude, longitude, year_observed,
                gbif_occurrence_key, created_at, updated_at
            ) VALUES (%s, %s, 'GBIF', 'observation', %s, %s, %s, %s, %s, NOW(), NOW())
        """, (tax_id, img['url'], img['country'], img['lat'], img['lon'], img['year'], img['gbif_key']))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

print(f"[#{INSTANCE_ID}] Starting continuous harvester...")

cycle = 0
while True:
    cycle += 1
    species_list = get_my_species()
    
    if not species_list:
        print(f"[#{INSTANCE_ID}] No more species found, sleeping...")
        time.sleep(30)
        continue
    
    print(f"[#{INSTANCE_ID}] Cycle {cycle}: Processing {len(species_list)} species")
    
    for tax_id, sci_name in species_list:
        # Try global first
        images = fetch_gbif(sci_name)
        
        # Then try priority countries
        for country in COUNTRIES[:3]:  # Just top 3 to speed up
            images.extend(fetch_gbif(sci_name, country))
            time.sleep(0.05)
        
        # Save images
        saved = 0
        for img in images[:20]:
            if save_image(img, tax_id):
                stats['added'] += 1
                saved += 1
            time.sleep(0.02)
        
        if saved > 0:
            rate = stats['added'] / ((time.time() - stats['start']) / 60)
            print(f"[#{INSTANCE_ID}] {sci_name[:40]}: +{saved} | Total: {stats['added']} | {rate:.1f}/min")
    
    print(f"[#{INSTANCE_ID}] Cycle {cycle} complete. Total: {stats['added']} images. Next cycle in 3 seconds...")
    time.sleep(3)
