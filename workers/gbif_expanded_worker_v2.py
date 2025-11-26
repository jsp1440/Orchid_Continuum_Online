#!/usr/bin/env python3
"""
GBIF EXPANDED WORKER V2 - DATA INTEGRITY VERSION
=================================================
Same as V1 but with strict data validation enforced
"""
import os, sys, time, requests, psycopg2, json
from psycopg2 import pool
from datetime import datetime

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "gbif-exp-v2-1"

GBIF_COUNTRIES = [
    'AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AO', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AW', 'AX', 'AZ',
    'BA', 'BB', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BL', 'BM', 'BN', 'BO', 'BQ', 'BR', 'BS', 'BT', 'BV', 'BW', 'BY', 'BZ',
    'CA', 'CC', 'CD', 'CF', 'CG', 'CH', 'CI', 'CK', 'CL', 'CM', 'CN', 'CO', 'CR', 'CU', 'CV', 'CW', 'CX', 'CY', 'CZ',
    'DE', 'DJ', 'DK', 'DM', 'DO', 'DZ', 'EC', 'EE', 'EG', 'EH', 'ER', 'ES', 'ET',
    'FI', 'FJ', 'FK', 'FM', 'FO', 'FR', 'GA', 'GB', 'GD', 'GE', 'GF', 'GG', 'GH', 'GI', 'GL', 'GM', 'GN', 'GP', 'GQ', 'GR', 'GS', 'GT', 'GU', 'GW', 'GY',
    'HK', 'HM', 'HN', 'HR', 'HT', 'HU', 'ID', 'IE', 'IL', 'IM', 'IN', 'IO', 'IQ', 'IR', 'IS', 'IT',
    'JE', 'JM', 'JO', 'JP', 'KE', 'KG', 'KH', 'KI', 'KM', 'KN', 'KP', 'KR', 'KW', 'KY', 'KZ',
    'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 'LS', 'LT', 'LU', 'LV', 'LY', 'MA', 'MC', 'MD', 'ME', 'MF', 'MG', 'MH', 'MK', 'ML', 'MM', 'MN', 'MO', 'MP', 'MQ', 'MR', 'MS', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ',
    'NA', 'NC', 'NE', 'NF', 'NG', 'NI', 'NL', 'NO', 'NP', 'NR', 'NU', 'NZ', 'OM',
    'PA', 'PE', 'PF', 'PG', 'PH', 'PK', 'PL', 'PM', 'PN', 'PR', 'PS', 'PT', 'PW', 'PY',
    'QA', 'RE', 'RO', 'RS', 'RU', 'RW', 'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SH', 'SI', 'SJ', 'SK', 'SL', 'SM', 'SN', 'SO', 'SR', 'SS', 'ST', 'SV', 'SX', 'SY', 'SZ',
    'TC', 'TD', 'TF', 'TG', 'TH', 'TJ', 'TK', 'TL', 'TM', 'TN', 'TO', 'TR', 'TT', 'TV', 'TW', 'TZ',
    'UA', 'UG', 'UM', 'US', 'UY', 'UZ', 'VA', 'VC', 'VE', 'VG', 'VI', 'VN', 'VU',
    'WF', 'WS', 'YE', 'YT', 'ZA', 'ZM', 'ZW'
]

pool_obj = pool.SimpleConnectionPool(minconn=1, maxconn=5, dsn=os.environ.get('DATABASE_URL'))
stats = {'added': 0, 'rejected': 0, 'start': time.time()}

def save_image_validated(taxonomy_id, img_data):
    """Save with strict validation"""
    conn = pool_obj.getconn()
    try:
        cur = conn.cursor()
        
        # VALIDATE: taxonomy_id exists
        cur.execute("SELECT id FROM orchid_taxonomy WHERE id = %s", (taxonomy_id,))
        if not cur.fetchone():
            stats['rejected'] += 1
            return False
        
        # VALIDATE: no duplicate URL
        cur.execute("SELECT id FROM orchid_images WHERE image_url = %s", (img_data['url'],))
        if cur.fetchone():
            return False
        
        # INSERT with all required fields
        cur.execute("""
            INSERT INTO orchid_images (
                taxonomy_id, image_url, image_source, country, locality,
                latitude, longitude, observer_name, image_license,
                gbif_occurrence_key, occurrence_metadata, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            taxonomy_id, img_data['url'], img_data['source'],
            img_data.get('country'), img_data.get('locality'),
            img_data.get('lat'), img_data.get('lon'),
            img_data.get('observer'), img_data.get('license'),
            img_data.get('gbif_key'), img_data.get('occurrence_meta')
        ))
        
        conn.commit()
        stats['added'] += 1
        return True
    except:
        conn.rollback()
        stats['rejected'] += 1
        return False
    finally:
        pool_obj.putconn(conn)

def fetch_gbif(genus, species, country):
    """Fetch from GBIF"""
    time.sleep(0.3)
    params = {
        'scientificName': f"{genus} {species}",
        'mediaType': 'StillImage',
        'limit': 50,
        'hasCoordinate': 'true',
        'country': country
    }
    try:
        resp = requests.get("https://api.gbif.org/v1/occurrence/search", params=params, timeout=15)
        if resp.status_code != 200:
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
                        'observer': rec.get('recordedBy'),
                        'license': m.get('license'),
                        'gbif_key': rec.get('key'),
                        'occurrence_meta': json.dumps(rec) if rec else None
                    })
        return imgs
    except:
        return []

def main():
    print(f"[{WORKER_ID}] GBIF V2 - Data Integrity Enforced")
    while True:
        conn = pool_obj.getconn()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, taxonomy_id, scientific_name FROM harvest_jobs
                WHERE status='pending' LIMIT 1 FOR UPDATE SKIP LOCKED
            """)
            job = cur.fetchone()
            
            if not job:
                pool_obj.putconn(conn)
                time.sleep(30)
                continue
            
            job_id, taxonomy_id, sci_name = job
            parts = sci_name.split()
            genus, species = parts[0], parts[1] if len(parts) > 1 else ''
            
            added = 0
            for country in GBIF_COUNTRIES:
                for img in fetch_gbif(genus, species, country):
                    if save_image_validated(taxonomy_id, img):
                        added += 1
            
            cur.execute("UPDATE harvest_jobs SET status='complete' WHERE id=%s", (job_id,))
            conn.commit()
            
            print(f"[{WORKER_ID}] +{added} images for {sci_name}")
        finally:
            pool_obj.putconn(conn)

if __name__ == "__main__":
    main()
