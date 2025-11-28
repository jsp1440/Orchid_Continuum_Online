#!/usr/bin/env python3
"""
INATURALIST TURBO WORKER - High-Performance Community Observations
===================================================================
Optimized for maximum throughput with parallel fetching
- Research-grade observations only
- Multiple quality tiers (research, needs_id)
- Geographic diversity fetching
- Up to 200 results per species
Uses O(1) taxonomy lookup via taxonomy_mapper
ALL database operations through centralized attach_record_to_taxonomy
"""
import os
import sys
import time
import requests
import psycopg2
import json
import threading
from psycopg2 import pool
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taxonomy_mapper import lookup_taxon, lookup_taxon_by_id, attach_record_to_taxonomy

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "inat-turbo-1"
BATCH_SIZE = 10
RECLAIM_MINUTES = 8
REQUEST_DELAY = 0.25
THREAD_COUNT = 6

ORCHID_HOTSPOT_PLACES = [
    '6853',   # Ecuador
    '7112',   # Colombia  
    '7124',   # Peru
    '6878',   # Brazil
    '6793',   # Costa Rica
    '6930',   # Mexico
    '6744',   # Australia
    '6681',   # Indonesia
    '6903',   # Malaysia
    '6712',   # Philippines
    '6698',   # Thailand
    '7161',   # Madagascar
    '7008',   # South Africa
    '6754',   # Papua New Guinea
    '6682',   # India
    '7321',   # Vietnam
    '6683',   # China
    '7062',   # Taiwan
    '6803',   # Japan
    '6970',   # New Zealand
]

pool_obj = None
stats = {'added': 0, 'start': time.time(), 'fetched': 0, 'errors': 0}
seen_urls = set()
seen_lock = threading.Lock()


def get_database_url():
    if os.environ.get('PGHOST'):
        return f"postgresql://{os.environ.get('PGUSER')}:{os.environ.get('PGPASSWORD')}@{os.environ.get('PGHOST')}:{os.environ.get('PGPORT')}/{os.environ.get('PGDATABASE')}?sslmode=require"
    return os.environ.get('DATABASE_URL', '')


def init_pool():
    global pool_obj
    pool_obj = pool.ThreadedConnectionPool(minconn=2, maxconn=10, dsn=get_database_url())


def get_conn():
    global pool_obj
    if pool_obj is None:
        init_pool()
    return pool_obj.getconn()


def put_conn(c):
    if pool_obj and c:
        try:
            pool_obj.putconn(c)
        except Exception:
            pass


def lease(n=BATCH_SIZE):
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


def fetch_inaturalist(name, place_id=None, quality='research'):
    time.sleep(REQUEST_DELAY)
    simple_name = simplify_name(name)
    
    try:
        params = {
            'taxon_name': simple_name,
            'quality_grade': quality,
            'photos': 'true',
            'per_page': 50,
            'order': 'desc',
            'order_by': 'votes'
        }
        if place_id:
            params['place_id'] = place_id
        
        resp = requests.get("https://api.inaturalist.org/v1/observations", params=params, timeout=15)
        if resp.status_code == 429:
            time.sleep(30)
            return []
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        imgs = []
        
        for obs in data.get('results', []):
            photos = obs.get('photos', [])
            if not photos:
                continue
            
            for photo in photos[:2]:
                img_url = photo.get('url')
                if img_url:
                    img_url = img_url.replace('square', 'large').replace('medium', 'large')
                
                if not img_url:
                    continue
                
                with seen_lock:
                    if img_url in seen_urls:
                        continue
                    seen_urls.add(img_url)
                    if len(seen_urls) > 50000:
                        seen_urls.clear()
                
                location = obs.get('location')
                lat, lon = None, None
                if location and ',' in str(location):
                    try:
                        parts = str(location).split(',')
                        lat = float(parts[0].strip())
                        lon = float(parts[1].strip())
                    except:
                        pass
                
                place_guess = obs.get('place_guess', '')
                
                imgs.append({
                    'url': img_url,
                    'source': 'iNaturalist',
                    'type': 'observation',
                    'country': place_guess.split(',')[-1].strip() if ',' in place_guess else place_guess,
                    'locality': place_guess,
                    'lat': lat,
                    'lon': lon,
                    'date': obs.get('observed_on'),
                    'year': obs.get('observed_on_details', {}).get('year') if obs.get('observed_on_details') else None,
                    'inaturalist_id': str(obs.get('id', '')),
                    'quality_grade': obs.get('quality_grade'),
                    'observer': obs.get('user', {}).get('login') if obs.get('user') else None,
                    'num_agreements': obs.get('num_identification_agreements', 0),
                    'license': photo.get('license_code')
                })
        
        stats['fetched'] += len(imgs)
        return imgs
    except Exception as e:
        stats['errors'] += 1
        return []


def save_via_mapper(img_data, taxonomy_id, sci_name):
    record = {
        'scientific_name': sci_name,
        'source': 'iNaturalist',
        'taxonomy_id': taxonomy_id
    }
    
    metadata = {
        'country': img_data.get('country'),
        'locality': img_data.get('locality'),
        'latitude': img_data.get('lat'),
        'longitude': img_data.get('lon'),
        'observation_date': img_data.get('date'),
        'year_observed': img_data.get('year'),
        'image_type': 'observation',
        'image_license': img_data.get('license'),
        'occurrence_metadata': json.dumps({
            'inaturalist_id': img_data.get('inaturalist_id'),
            'quality_grade': img_data.get('quality_grade'),
            'observer': img_data.get('observer'),
            'num_identification_agreements': img_data.get('num_agreements', 0)
        })
    }
    
    result = attach_record_to_taxonomy(record, img_data['url'], metadata=metadata)
    return result.get('attached', False)


def harvest_species(job_id, taxonomy_id, sci_name):
    taxon = lookup_taxon_by_id(taxonomy_id)
    if not taxon.get('matched'):
        fail_job(job_id, 'Invalid taxonomy_id')
        return 0, False
    
    all_images = []
    simple_name = simplify_name(sci_name) if sci_name else 'Unknown'
    
    global_imgs = fetch_inaturalist(simple_name)
    all_images.extend(global_imgs)
    
    def fetch_place(place_id):
        return fetch_inaturalist(simple_name, place_id=place_id)
    
    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        futures = {executor.submit(fetch_place, p): p for p in ORCHID_HOTSPOT_PLACES[:12]}
        for future in as_completed(futures):
            try:
                imgs = future.result()
                all_images.extend(imgs)
            except Exception:
                pass
    
    needs_id = fetch_inaturalist(simple_name, quality='needs_id')
    all_images.extend(needs_id[:10])
    
    added = 0
    for img in all_images:
        if save_via_mapper(img, taxonomy_id, sci_name):
            added += 1
    
    stats['added'] += added
    return added, True


def complete_job(job_id):
    c = get_conn()
    try:
        r = c.cursor()
        r.execute("UPDATE harvest_jobs SET status='completed', completed_at=NOW() WHERE id=%s", (job_id,))
        c.commit()
    finally:
        put_conn(c)


def fail_job(job_id, error):
    c = get_conn()
    try:
        r = c.cursor()
        r.execute("UPDATE harvest_jobs SET status='failed', last_error=%s WHERE id=%s", (str(error)[:200], job_id))
        c.commit()
    finally:
        put_conn(c)


def main():
    print(f"INATURALIST TURBO WORKER: {WORKER_ID}")
    print(f"[{WORKER_ID}] Fetching from {len(ORCHID_HOTSPOT_PLACES)} orchid hotspot regions")
    
    while True:
        try:
            jobs = lease()
            if not jobs:
                print(f"[{WORKER_ID}] No jobs, waiting 30s...")
                time.sleep(30)
                continue
            
            for job in jobs:
                job_id, taxonomy_id, sci_name = job
                try:
                    added, success = harvest_species(job_id, taxonomy_id, sci_name)
                    if success:
                        complete_job(job_id)
                        if added > 0:
                            print(f"[{WORKER_ID}] {sci_name}: +{added}")
                except Exception as e:
                    fail_job(job_id, str(e))
            
            elapsed = time.time() - stats['start']
            rate = stats['added'] / (elapsed / 3600) if elapsed > 0 else 0
            print(f"[{WORKER_ID}] Total: {stats['added']:,} | Rate: {rate:,.0f}/hr | Fetched: {stats['fetched']:,}")
            
        except Exception as e:
            print(f"[{WORKER_ID}] Error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
