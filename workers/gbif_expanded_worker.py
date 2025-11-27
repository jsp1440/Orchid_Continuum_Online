#!/usr/bin/env python3
"""
GBIF EXPANDED WORKER - Global Coverage (ALL 247 Countries)
===========================================================
Harvests from GBIF with complete country coverage and automatic fallback
Designed for maximum coverage with API resilience
Uses O(1) taxonomy lookup via taxonomy_mapper

BULLETPROOF VERSION: Auto-recovers from ALL crashes
"""
import os
import sys
import time
import requests
import psycopg2
import json
import traceback
from psycopg2 import pool
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taxonomy_mapper import lookup_taxon, lookup_taxon_by_id

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "gbif-expanded-1"

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
REQUEST_DELAY = 0.3

pool_obj = None
stats = {'added': 0, 'start': time.time(), 'errors': 0, 'api_failures': 0, 'restarts': 0}


def init_pool():
    global pool_obj
    try:
        pool_obj = pool.SimpleConnectionPool(minconn=1, maxconn=5, dsn=os.environ.get('DATABASE_URL'))
        return True
    except Exception as e:
        print(f"[{WORKER_ID}] Pool init failed: {e}")
        return False


def get_conn():
    global pool_obj
    if pool_obj is None:
        init_pool()
    return pool_obj.getconn()


def put_conn(c):
    global pool_obj
    if pool_obj and c:
        try:
            pool_obj.putconn(c)
        except Exception:
            pass


def check_api_health():
    try:
        resp = requests.get("https://api.gbif.org/v1/occurrence/search", 
                          params={'limit': 1}, timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def simplify_name(full_name):
    parts = full_name.split()
    if len(parts) < 2:
        return full_name
    
    genus = parts[0]
    
    if parts[1] == 'x' and len(parts) >= 3:
        return f"{genus} {parts[2]}"
    
    if len(parts) >= 3 and parts[2] in ('ssp.', 'subsp.', 'var.', 'f.', 'forma'):
        return f"{genus} {parts[1]}"
    
    return f"{genus} {parts[1]}"


def fetch_gbif(name, country=None):
    time.sleep(REQUEST_DELAY)
    
    p = {
        'scientificName': name, 
        'mediaType': 'StillImage', 
        'limit': 50,
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
    except Exception:
        stats['errors'] += 1
        return []


def save_image(taxonomy_id, img_data):
    c = None
    try:
        c = get_conn()
        r = c.cursor()
        
        r.execute("SELECT id FROM orchid_images WHERE image_url = %s", (img_data['url'],))
        if r.fetchone():
            put_conn(c)
            return False
        
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
    except Exception:
        if c:
            try:
                c.rollback()
            except Exception:
                pass
            put_conn(c)
        return False


def harvest_by_country(genus, species, country, taxonomy_id):
    imgs = fetch_gbif(f"{genus} {species}", country)
    added = 0
    for img in imgs:
        if save_image(taxonomy_id, img):
            added += 1
    return added


def lease_jobs(n=BATCH_SIZE):
    c = None
    try:
        c = get_conn()
        r = c.cursor()
        r.execute(f"UPDATE harvest_jobs SET status='pending', lease_owner=NULL WHERE status='leased' AND leased_at < NOW() - INTERVAL '{RECLAIM_MINUTES} minutes'")
        sql = "UPDATE harvest_jobs SET status='leased', lease_owner=%s, leased_at=NOW() WHERE id IN (SELECT id FROM harvest_jobs WHERE status='pending' ORDER BY priority DESC LIMIT %s FOR UPDATE SKIP LOCKED) RETURNING id, taxonomy_id, scientific_name"
        r.execute(sql, (WORKER_ID, n))
        jobs = r.fetchall()
        c.commit()
        put_conn(c)
        return jobs
    except Exception as e:
        print(f"[{WORKER_ID}] lease_jobs error: {e}")
        if c:
            try:
                c.rollback()
            except Exception:
                pass
            put_conn(c)
        return []


def process_jobs():
    jobs = lease_jobs()
    if not jobs:
        print(f"[{WORKER_ID}] No jobs, waiting...")
        time.sleep(30)
        return
    
    for job_id, taxonomy_id, sci_name in jobs:
        try:
            taxon = lookup_taxon_by_id(taxonomy_id)
            if not taxon.get('matched'):
                print(f"[{WORKER_ID}] Invalid taxonomy_id {taxonomy_id}, skipping job {job_id}")
                continue
            
            simple_name = simplify_name(sci_name) if sci_name else 'Unknown'
            parts = simple_name.split()
            genus = parts[0] if parts else 'Unknown'
            species = parts[1] if len(parts) > 1 else ''
            
            added_total = 0
            for country in GBIF_COUNTRIES:
                try:
                    added = harvest_by_country(genus, species, country, taxonomy_id)
                    added_total += added
                    if added > 0:
                        print(f"[{WORKER_ID}] {genus} {species}: +{added} ({country})")
                except Exception as e:
                    print(f"[{WORKER_ID}] Country {country} error: {e}")
                    continue
            
            c = None
            try:
                c = get_conn()
                r = c.cursor()
                r.execute("UPDATE harvest_jobs SET status='complete' WHERE id=%s", (job_id,))
                c.commit()
                stats['added'] += added_total
                print(f"[{WORKER_ID}] Job {job_id} complete: +{added_total} images")
            except Exception as e:
                print(f"[{WORKER_ID}] Job complete error: {e}")
            finally:
                if c:
                    put_conn(c)
        except Exception as e:
            print(f"[{WORKER_ID}] Job {job_id} failed: {e}")
            continue


def main():
    print(f"[{WORKER_ID}] GBIF Expanded Worker - ALL {len(GBIF_COUNTRIES)} Countries")
    print(f"[{WORKER_ID}] Using O(1) taxonomy lookup")
    print(f"[{WORKER_ID}] API Health: {'OK' if check_api_health() else 'FAILED'}")
    
    while True:
        try:
            process_jobs()
        except Exception as e:
            print(f"[{WORKER_ID}] Loop error: {e}")
            time.sleep(10)
            continue


def run_forever():
    while True:
        try:
            print(f"[{WORKER_ID}] Starting worker (restart #{stats['restarts']})...")
            init_pool()
            main()
        except KeyboardInterrupt:
            print(f"[{WORKER_ID}] Shutdown requested")
            break
        except Exception as e:
            stats['restarts'] += 1
            print(f"[{WORKER_ID}] CRASH RECOVERED: {e}")
            print(f"[{WORKER_ID}] Traceback: {traceback.format_exc()}")
            print(f"[{WORKER_ID}] Restarting in 30 seconds...")
            time.sleep(30)
            continue


if __name__ == "__main__":
    run_forever()
