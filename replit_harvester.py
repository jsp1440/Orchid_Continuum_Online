#!/usr/bin/env python3
"""
Simple GBIF harvester - Database only, no Google Drive
Runs continuously on Replit
"""
import os
import time
import requests
import psycopg2
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import signal
import sys

DATABASE_URL = os.environ.get('DATABASE_URL')
stats = {'cataloged': 0, 'failed': 0, 'start_time': time.time()}
running = True

def signal_handler(sig, frame):
    global running
    print('\n\n🛑 Stopping harvester...')
    running = False

signal.signal(signal.SIGINT, signal_handler)

def get_species_batch(limit=100):
    """Get species needing images"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT ot.id, ot.scientific_name, ot.genus, ot.species
        FROM orchid_taxonomy ot
        LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
        GROUP BY ot.id, ot.scientific_name, ot.genus, ot.species
        HAVING COUNT(oi.id) < 30
        ORDER BY COUNT(oi.id) ASC, ot.scientific_name
        LIMIT %s
    """, (limit,))
    results = cur.fetchall()
    conn.close()
    return results

def fetch_gbif_images(species_name, limit=40):
    """Fetch images from GBIF"""
    url = "https://api.gbif.org/v1/occurrence/search"
    params = {
        'scientificName': species_name,
        'mediaType': 'StillImage',
        'limit': limit,
        'hasCoordinate': 'true'
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            return []
        data = response.json()
        images = []
        for record in data.get('results', []):
            if not record.get('media'):
                continue
            for media in record['media']:
                if media.get('type') == 'StillImage' and media.get('identifier'):
                    images.append({
                        'url': media.get('identifier'),
                        'source': 'GBIF',
                        'license': record.get('license', 'Unknown'),
                        'country': record.get('country'),
                        'latitude': record.get('decimalLatitude'),
                        'longitude': record.get('decimalLongitude'),
                        'observation_date': record.get('eventDate'),
                        'observer_name': record.get('recordedBy'),
                        'gbif_occurrence_key': str(record.get('key', ''))
                    })
        return images
    except:
        return []

def save_to_database(img_data, tax_id):
    """Save to database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO orchid_images (
                taxonomy_id, image_url, image_source, image_license,
                country, latitude, longitude, observation_date, 
                observer_name, gbif_occurrence_key,
                created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (image_url) DO NOTHING
        """, (
            tax_id, img_data['url'], img_data['source'], img_data['license'],
            img_data.get('country'), img_data.get('latitude'), 
            img_data.get('longitude'), img_data.get('observation_date'),
            img_data.get('observer_name'), img_data.get('gbif_occurrence_key')
        ))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def process_species(species_data):
    """Process one species"""
    tax_id, sci_name, genus, sp = species_data
    images = fetch_gbif_images(sci_name, limit=40)
    if not images:
        return 0
    
    cataloged = 0
    for img in images[:30]:
        if save_to_database(img, tax_id):
            stats['cataloged'] += 1
            cataloged += 1
        else:
            stats['failed'] += 1
        time.sleep(0.05)
    
    elapsed_min = (time.time() - stats['start_time']) / 60
    rate = stats['cataloged'] / elapsed_min if elapsed_min > 0 else 0
    
    if cataloged > 0:
        print(f"[✅] {sci_name}: {cataloged} images | RATE: {rate:.1f}/min | TOTAL: {stats['cataloged']}")
    
    return cataloged

print("=" * 70)
print("🌺 REPLIT ORCHID HARVESTER - CONTINUOUS MODE")
print("=" * 70)
print("Database only (no Drive upload)")
print("Press Ctrl+C to stop\n")

cycle = 0
while running:
    cycle += 1
    print(f"\n{'─' * 70}")
    print(f"CYCLE #{cycle}")
    print(f"{'─' * 70}")
    
    species_batch = get_species_batch(100)
    if not species_batch:
        print("✅ All species have 30+ images! Job complete.")
        break
    
    print(f"Processing {len(species_batch)} species...\n")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_species, species_batch))
    
    elapsed = (time.time() - stats['start_time']) / 60
    print(f"\n📊 CYCLE COMPLETE | Total: {stats['cataloged']} | Failed: {stats['failed']}")
    print(f"    Runtime: {elapsed:.1f} min | Rate: {stats['cataloged']/elapsed:.1f}/min")
    
    if not running:
        break
    
    time.sleep(5)

print(f"\n{'=' * 70}")
print(f"🎉 HARVESTER STOPPED")
print(f"   Total cataloged: {stats['cataloged']}")
print(f"   Failed: {stats['failed']}")
print(f"   Runtime: {(time.time() - stats['start_time'])/60:.1f} minutes")
print(f"{'=' * 70}\n")
