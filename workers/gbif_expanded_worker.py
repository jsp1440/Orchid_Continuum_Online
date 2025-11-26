#!/usr/bin/env python3
"""
GBIF EXPANDED WORKER - Global Coverage (ALL 247 Countries)
===========================================================
Harvests from GBIF with complete country coverage and automatic fallback
Designed for maximum coverage with API resilience
"""
import os, sys, time, requests, psycopg2, json, hashlib
from psycopg2 import pool
from datetime import datetime

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "gbif-expanded-1"

# ALL 247 countries covered by GBIF (ISO 3166-1 alpha-2 codes)
GBIF_COUNTRIES = [
    'AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AO', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AW', 'AX', 'AZ',
    'BA', 'BB', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BL', 'BM', 'BN', 'BO', 'BQ', 'BR', 'BS', 'BT', 'BV', 'BW', 'BY', 'BZ',
    'CA', 'CC', 'CD', 'CF', 'CG', 'CH', 'CI', 'CK', 'CL', 'CM', 'CN', 'CO', 'CR', 'CU', 'CV', 'CW', 'CX', 'CY', 'CZ',
    'DE', 'DJ', 'DK', 'DM', 'DO', 'DZ',
    'EC', 'EE', 'EG', 'EH', 'ER', 'ES', 'ET',
    'FI', 'FJ', 'FK', 'FM', 'FO', 'FR',
    'GA', 'GB', 'GD', 'GE', 'GF', 'GG', 'GH', 'GI', 'GL', 'GM', 'GN', 'GP', 'GQ', 'GR', 'GS', 'GT', 'GU', 'GW', 'GY',
    'HK', 'HM', 'HN', 'HR', 'HT', 'HU',
    'ID', 'IE', 'IL', 'IM', 'IN', 'IO', 'IQ', 'IR', 'IS', 'IT',
    'JE', 'JM', 'JO', 'JP',
    'KE', 'KG', 'KH', 'KI', 'KM', 'KN', 'KP', 'KR', 'KW', 'KY', 'KZ',
    'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 'LS', 'LT', 'LU', 'LV', 'LY',
    'MA', 'MC', 'MD', 'ME', 'MF', 'MG', 'MH', 'MK', 'ML', 'MM', 'MN', 'MO', 'MP', 'MQ', 'MR', 'MS', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ',
    'NA', 'NC', 'NE', 'NF', 'NG', 'NI', 'NL', 'NO', 'NP', 'NR', 'NU', 'NZ',
    'OM',
    'PA', 'PE', 'PF', 'PG', 'PH', 'PK', 'PL', 'PM', 'PN', 'PR', 'PS', 'PT', 'PW', 'PY',
    'QA',
    'RE', 'RO', 'RS', 'RU', 'RW',
    'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SH', 'SI', 'SJ', 'SK', 'SL', 'SM', 'SN', 'SO', 'SR', 'SS', 'ST', 'SV', 'SX', 'SY', 'SZ',
    'TC', 'TD', 'TF', 'TG', 'TH', 'TJ', 'TK', 'TL', 'TM', 'TN', 'TO', 'TR', 'TT', 'TV', 'TW', 'TZ',
    'UA', 'UG', 'UM', 'US', 'UY', 'UZ',
    'VA', 'VC', 'VE', 'VG', 'VI', 'VN', 'VU',
    'WF', 'WS',
    'YE', 'YT',
    'ZA', 'ZM', 'ZW'
]

BATCH_SIZE = 5
RECLAIM_MINUTES = 7
REQUEST_DELAY = 0.3  # 300ms between requests

pool_obj = pool.SimpleConnectionPool(minconn=1, maxconn=5, dsn=os.environ.get('DATABASE_URL'))
stats = {'added': 0, 'start': time.time(), 'errors': 0, 'api_failures': 0}

def get_conn():
    return pool_obj.getconn()

def put_conn(c):
    pool_obj.putconn(c)

def check_api_health():
    """Test if GBIF API is responding"""
    try:
        resp = requests.get("https://api.gbif.org/v1/occurrence/search", 
                          params={'limit': 1}, timeout=5)
        return resp.status_code == 200
    except:
        return False

def fetch_gbif(name, country=None):
    """Fetch from GBIF with error handling"""
    time.sleep(REQUEST_DELAY)
    
    p = {
        'scientificName': name, 
        'mediaType': 'StillImage', 
        'limit': 50,  # Increased batch size
        'hasCoordinate': 'true'
    }
    if country:
        p['country'] = country
    
    try:
        resp = requests.get("https://api.gbif.org/v1/occurrence/search", 
                          params=p, timeout=15)
        
        if resp.status_code == 429:
            print(f"[{WORKER_ID}] Rate limited! Waiting 120s...")
            stats['api_failures'] += 1
            time.sleep(120)
            return []
        
        if resp.status_code != 200:
            stats['api_failures'] += 1
            return []
        
        imgs = []
        for rec in resp.json().get('results', []):
            for m in rec.get('media', []):
                if m.get('type') == 'StillImage' and m.get('identifier'):
                    imgs.append({
                        'url': m['identifier'],
                        'source': 'GBIF',
                        'country': rec.get('country'),
                        'locality': rec.get('locality'),
                        'lat': rec.get('decimalLatitude'),
                        'lon': rec.get('decimalLongitude'),
                        'date': rec.get('eventDate'),
                        'year': rec.get('year'),
                        'observer': rec.get('recordedBy'),
                        'license': m.get('license'),
                        'gbif_key': rec.get('key'),
                        'occurrence_meta': json.dumps(rec) if rec else None
                    })
        return imgs
    except Exception as e:
        stats['errors'] += 1
        return []

def save_image(taxonomy_id, img_data):
    """Save image with deduplication"""
    try:
        c = get_conn()
        r = c.cursor()
        
        # Check duplicate by URL
        r.execute("SELECT id FROM orchid_images WHERE image_url = %s", (img_data['url'],))
        if r.fetchone():
            put_conn(c)
            return False
        
        # Insert
        r.execute("""
            INSERT INTO orchid_images (
                taxonomy_id, image_url, image_source, gbif_occurrence_key,
                country, locality, latitude, longitude, observer_name, image_license,
                occurrence_metadata, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT DO NOTHING
        """, (
            taxonomy_id, img_data['url'], img_data['source'], img_data.get('gbif_key'),
            img_data['country'], img_data['locality'], img_data['lat'], img_data['lon'],
            img_data['observer'], img_data['license'], img_data.get('occurrence_meta')
        ))
        
        c.commit()
        put_conn(c)
        return True
    except Exception as e:
        c.rollback()
        put_conn(c)
        return False

def harvest_by_country(genus, species, country, taxonomy_id):
    """Target specific country"""
    imgs = fetch_gbif(f"{genus} {species}", country)
    added = 0
    for img in imgs:
        if save_image(taxonomy_id, img):
            added += 1
    return added

def lease_jobs(n=BATCH_SIZE):
    """Get pending jobs from queue"""
    c = get_conn()
    try:
        r = c.cursor()
        r.execute(f"UPDATE harvest_jobs SET status='pending', lease_owner=NULL WHERE status='leased' AND leased_at < NOW() - INTERVAL '{RECLAIM_MINUTES} minutes'")
        sql = "UPDATE harvest_jobs SET status='leased', lease_owner=%s, leased_at=NOW() WHERE id IN (SELECT id FROM harvest_jobs WHERE status='pending' ORDER BY priority DESC LIMIT %s FOR UPDATE SKIP LOCKED) RETURNING id, taxonomy_id, scientific_name"
        r.execute(sql, (WORKER_ID, n))
        jobs = r.fetchall()
        c.commit()
        return jobs
    finally:
        put_conn(c)

def main():
    print(f"[{WORKER_ID}] GBIF Expanded Worker - ALL {len(GBIF_COUNTRIES)} Countries")
    print(f"[{WORKER_ID}] API Health: {'✅' if check_api_health() else '❌'}")
    
    while True:
        jobs = lease_jobs()
        if not jobs:
            print(f"[{WORKER_ID}] No jobs, waiting...")
            time.sleep(30)
            continue
        
        for job_id, taxonomy_id, sci_name in jobs:
            genus, species = sci_name.split()[:2] if ' ' in sci_name else [sci_name, '']
            
            added_total = 0
            for country in GBIF_COUNTRIES:
                added = harvest_by_country(genus, species, country, taxonomy_id)
                added_total += added
                if added > 0:
                    print(f"[{WORKER_ID}] {genus} {species}: +{added} ({country})")
            
            # Mark job complete
            c = get_conn()
            try:
                r = c.cursor()
                r.execute("UPDATE harvest_jobs SET status='complete' WHERE id=%s", (job_id,))
                c.commit()
                stats['added'] += added_total
                print(f"[{WORKER_ID}] Job {job_id} complete: +{added_total} images")
            finally:
                put_conn(c)

if __name__ == "__main__":
    main()
