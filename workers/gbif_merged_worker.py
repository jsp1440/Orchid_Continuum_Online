#!/usr/bin/env python3
"""
GBIF MERGED WORKER - Combines best practices from priority_harvester + expanded coverage
- ALL 247 countries (vs just 12 priority ones)
- Full metadata extraction like priority_harvester
- Validation & deduplication
- Logging like priority_harvester
"""
import os, sys, time, requests, psycopg2, json, logging
from psycopg2 import pool
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "gbif-merged-1"

# ALL 247 countries for global coverage
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

def save_image(taxonomy_id, img_data):
    """Save with full validation (from priority_harvester approach)"""
    conn = pool_obj.getconn()
    try:
        cur = conn.cursor()
        
        # VALIDATE: taxonomy exists
        cur.execute("SELECT id FROM orchid_taxonomy WHERE id = %s", (taxonomy_id,))
        if not cur.fetchone():
            stats['rejected'] += 1
            cur.close()
            return False
        
        # VALIDATE: no duplicate URL
        cur.execute("SELECT id FROM orchid_images WHERE image_url = %s", (img_data['url'],))
        if cur.fetchone():
            cur.close()
            return False
        
        # INSERT with full metadata (like priority_harvester)
        cur.execute("""
            INSERT INTO orchid_images (
                taxonomy_id, image_url, image_source, gbif_occurrence_key,
                country, locality, latitude, longitude, observer_name, image_license,
                occurrence_metadata, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT DO NOTHING
        """, (
            taxonomy_id, img_data['url'], 'GBIF', img_data.get('gbif_key'),
            img_data.get('country'), img_data.get('locality'),
            img_data.get('lat'), img_data.get('lon'),
            img_data.get('observer'), img_data.get('license'),
            img_data.get('occurrence_meta')
        ))
        
        conn.commit()
        stats['added'] += 1
        cur.close()
        return True
    except Exception as e:
        conn.rollback()
        logger.debug(f"Save error: {e}")
        stats['rejected'] += 1
        return False
    finally:
        pool_obj.putconn(conn)

def harvest_gbif(genus, species, country, taxonomy_id):
    """Harvest from GBIF with full metadata (like priority_harvester)"""
    time.sleep(0.3)
    
    params = {
        'scientificName': f"{genus} {species}",
        'mediaType': 'StillImage',
        'limit': 300,  # Match priority_harvester batch size
        'hasCoordinate': 'true',
        'country': country
    }
    
    try:
        resp = requests.get("https://api.gbif.org/v1/occurrence/search", params=params, timeout=15)
        
        if resp.status_code == 429:
            logger.warning(f"Rate limited! Waiting 120s...")
            time.sleep(120)
            return 0
        
        if resp.status_code != 200:
            return 0
        
        added = 0
        for record in resp.json().get('results', []):
            if 'media' not in record:
                continue
            
            for media in record.get('media', []):
                if media.get('type') != 'StillImage':
                    continue
                
                image_url = media.get('identifier')
                if not image_url:
                    continue
                
                # Extract full metadata (like priority_harvester)
                img_data = {
                    'url': image_url,
                    'gbif_key': record.get('key'),
                    'country': record.get('country'),
                    'locality': record.get('locality'),
                    'lat': record.get('decimalLatitude'),
                    'lon': record.get('decimalLongitude'),
                    'observer': record.get('recordedBy'),
                    'license': media.get('license'),
                    'occurrence_meta': json.dumps(record) if record else None
                }
                
                if save_image(taxonomy_id, img_data):
                    added += 1
        
        return added
    except Exception as e:
        logger.error(f"GBIF error: {e}")
        return 0

def main():
    logger.info(f"[{WORKER_ID}] GBIF Merged Worker - 247 Countries, Full Metadata, Validation Locked")
    
    while True:
        conn = pool_obj.getconn()
        try:
            cur = conn.cursor()
            
            # Get job from queue
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
            
            added_total = 0
            for country in GBIF_COUNTRIES:
                added = harvest_gbif(genus, species, country, taxonomy_id)
                added_total += added
                if added > 0:
                    logger.info(f"[{WORKER_ID}] {genus} {species} ({country}): +{added} images")
            
            # Mark complete
            cur.execute("UPDATE harvest_jobs SET status='complete' WHERE id=%s", (job_id,))
            conn.commit()
            
            logger.info(f"[{WORKER_ID}] Job complete: +{added_total} images for {sci_name}")
        finally:
            pool_obj.putconn(conn)

if __name__ == "__main__":
    main()
