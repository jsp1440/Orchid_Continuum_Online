#!/usr/bin/env python3
"""
PARALLEL ORCHID HARVESTER - Instance #{INSTANCE_ID}
Each instance works on different species to maximize throughput
"""
import os
import sys
import time
import requests
import psycopg2
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')
INSTANCE_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 0
TOTAL_INSTANCES = int(sys.argv[2]) if len(sys.argv) > 2 else 8

# Priority regions
PRIORITY_COUNTRIES = ['AU', 'PG', 'ID', 'MY', 'PH', 'TH', 'VN', 'CR', 'PA', 'KE', 'TZ', 'MG', 'ZA']

stats = {'cataloged': 0, 'failed': 0, 'start_time': time.time()}

def get_species_batch(limit=50):
    """Get species needing images - partitioned by instance"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Simple partition - use MOD on taxonomy_id
    cur.execute("""
        SELECT ot.id, ot.scientific_name
        FROM orchid_taxonomy ot
        LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
        WHERE MOD(ot.id, %s) = %s
        GROUP BY ot.id, ot.scientific_name
        HAVING COUNT(oi.id) < 30
        ORDER BY COUNT(oi.id) ASC
        LIMIT %s
    """, (TOTAL_INSTANCES, INSTANCE_ID, limit))
    
    results = cur.fetchall()
    conn.close()
    return results

def fetch_gbif_with_regions(species_name):
    """Fetch images - global + priority regions"""
    all_images = []
    all_images.extend(fetch_gbif(species_name, None))
    for country in PRIORITY_COUNTRIES:
        all_images.extend(fetch_gbif(species_name, country))
        time.sleep(0.05)
    return all_images[:30]

def fetch_gbif(species_name, country_code=None):
    """Fetch from GBIF with all metadata"""
    url = "https://api.gbif.org/v1/occurrence/search"
    params = {
        'scientificName': species_name,
        'mediaType': 'StillImage',
        'limit': 5,
        'hasCoordinate': 'true'
    }
    if country_code:
        params['country'] = country_code
    
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return []
        
        images = []
        for rec in r.json().get('results', []):
            if not rec.get('media'):
                continue
            
            for m in rec['media']:
                if m.get('type') == 'StillImage' and m.get('identifier'):
                    images.append({
                        'url': m['identifier'],
                        'source': 'GBIF',
                        'license': rec.get('license'),
                        'type': 'observation',
                        'country': rec.get('country'),
                        'country_code': rec.get('countryCode'),
                        'state_province': rec.get('stateProvince'),
                        'locality': rec.get('locality'),
                        'continent': rec.get('continent'),
                        'latitude': rec.get('decimalLatitude'),
                        'longitude': rec.get('decimalLongitude'),
                        'coordinate_uncertainty': rec.get('coordinateUncertaintyInMeters'),
                        'elevation_meters': rec.get('elevation'),
                        'observation_date': rec.get('eventDate'),
                        'year': rec.get('year'),
                        'month': rec.get('month'),
                        'observer_name': rec.get('recordedBy'),
                        'institution_code': rec.get('institutionCode'),
                        'individual_count': rec.get('individualCount'),
                        'sex': rec.get('sex'),
                        'life_stage': rec.get('lifeStage'),
                        'reproductive_condition': rec.get('reproductiveCondition'),
                        'gbif_occurrence_key': str(rec.get('key', '')),
                        'image_rights_holder': m.get('rightsHolder'),
                    })
        return images
    except:
        return []

def save_to_db(img, tax_id):
    """Save to database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Check if URL exists
        cur.execute("SELECT id FROM orchid_images WHERE image_url = %s LIMIT 1", (img['url'],))
        if cur.fetchone():
            conn.close()
            return False
        
        # Parse observation_date - handle invalid formats
        obs_date = img.get('observation_date')
        if obs_date and ('/' in obs_date or len(obs_date) < 10):
            obs_date = None  # Skip invalid dates
        
        cur.execute("""
            INSERT INTO orchid_images (
                taxonomy_id, image_url, image_source, image_license, image_type,
                country, country_code, state_province, locality, continent,
                latitude, longitude, coordinate_uncertainty, elevation_meters,
                observation_date, year_observed, month_observed,
                observer_name, institution_code,
                individual_count, sex, life_stage, reproductive_condition,
                gbif_occurrence_key, image_rights_holder,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                NOW(), NOW()
            )
        """, (
            tax_id, img['url'], img['source'], img.get('license'), img.get('type'),
            img.get('country'), img.get('country_code'), img.get('state_province'), 
            img.get('locality'), img.get('continent'),
            img.get('latitude'), img.get('longitude'), img.get('coordinate_uncertainty'), 
            img.get('elevation_meters'),
            obs_date, img.get('year'), img.get('month'),
            img.get('observer_name'), img.get('institution_code'),
            img.get('individual_count'), img.get('sex'), img.get('life_stage'), 
            img.get('reproductive_condition'),
            img.get('gbif_occurrence_key'), img.get('image_rights_holder')
        ))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def process_species(species_data):
    """Process one species"""
    tax_id, sci_name = species_data
    images = fetch_gbif_with_regions(sci_name)
    if not images:
        return 0
    
    cataloged = 0
    for img in images:
        if save_to_db(img, tax_id):
            stats['cataloged'] += 1
            cataloged += 1
        else:
            stats['failed'] += 1
        time.sleep(0.03)
    
    if cataloged > 0:
        elapsed_min = (time.time() - stats['start_time']) / 60
        rate = stats['cataloged'] / elapsed_min if elapsed_min > 0 else 0
        print(f"[#{INSTANCE_ID}] {sci_name[:45]}: +{cataloged} | Rate: {rate:.1f}/min | Total: {stats['cataloged']}")
    
    return cataloged

print(f"{'=' * 80}")
print(f"🌺 PARALLEL HARVESTER #{INSTANCE_ID} (of {TOTAL_INSTANCES})")
print(f"{'=' * 80}")
print(f"Started: {datetime.now().strftime('%I:%M:%S %p')}\n")

cycle = 0
while True:
    cycle += 1
    species_batch = get_species_batch(40)
    if not species_batch:
        print(f"[#{INSTANCE_ID}] No more species to process")
        break
    
    for species_data in species_batch:
        process_species(species_data)
        time.sleep(0.1)
    
    elapsed = (time.time() - stats['start_time']) / 60
    print(f"[#{INSTANCE_ID}] Cycle {cycle}: {stats['cataloged']} total | {elapsed:.1f} min | {stats['cataloged']/elapsed:.1f}/min")
    time.sleep(1)

print(f"\n[#{INSTANCE_ID}] COMPLETE: {stats['cataloged']} images")
