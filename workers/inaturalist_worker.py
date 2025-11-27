#!/usr/bin/env python3
"""
INATURALIST-ONLY WORKER - Community Observations
=================================================
Dedicated worker for iNaturalist API (NO API KEY NEEDED)
Uses O(1) taxonomy lookup via taxonomy_mapper
ALL database operations through centralized attach_record_to_taxonomy
Run 3 workers: python workers/inaturalist_worker.py inat-1 ... inat-3
"""
import os
import sys
import time
import requests
import psycopg2
import json
from psycopg2 import pool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taxonomy_mapper import lookup_taxon, lookup_taxon_by_id, attach_record_to_taxonomy

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "inat-1"
BATCH_SIZE = 8
RECLAIM_MINUTES = 7
REQUEST_DELAY = 0.3

pool_obj = pool.SimpleConnectionPool(minconn=1, maxconn=5, dsn=os.environ.get('DATABASE_URL'))
stats = {'added': 0, 'start': time.time(), 'errors': 0}


def get_conn():
    return pool_obj.getconn()


def put_conn(c):
    pool_obj.putconn(c)


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


def fetch_inaturalist(name):
    time.sleep(REQUEST_DELAY)
    
    simple_name = simplify_name(name)
    
    try:
        search_url = "https://api.inaturalist.org/v1/observations"
        params = {
            'taxon_name': simple_name,
            'quality_grade': 'research',
            'photos': 'true',
            'per_page': 30
        }
        
        resp = requests.get(search_url, params=params, timeout=15)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        imgs = []
        
        for obs in data.get('results', []):
            photos = obs.get('photos', [])
            if not photos:
                continue
            
            photo = photos[0]
            img_url = photo.get('url')
            
            if img_url:
                img_url = img_url.replace('square', 'large')
            
            if img_url:
                location = obs.get('location')
                lat = None
                lon = None
                if location and ',' in location:
                    parts = location.split(',')
                    try:
                        lat = float(parts[0])
                        lon = float(parts[1])
                    except (ValueError, IndexError):
                        pass
                
                imgs.append({
                    'url': img_url,
                    'source': 'iNaturalist',
                    'type': 'observation',
                    'country': obs.get('place_guess', '').split(',')[-1].strip() if obs.get('place_guess') else None,
                    'lat': lat,
                    'lon': lon,
                    'date': obs.get('observed_on'),
                    'year': obs.get('observed_on_details', {}).get('year'),
                    'inaturalist_id': str(obs.get('id', '')),
                    'quality_grade': obs.get('quality_grade'),
                    'observer': obs.get('user', {}).get('login'),
                    'num_agreements': obs.get('num_identification_agreements', 0)
                })
        
        return imgs[:20]
    except Exception:
        stats['errors'] += 1
        return []


def save_via_mapper(img_data, taxonomy_id, sci_name):
    """Save using centralized attach_record_to_taxonomy"""
    record = {
        'scientific_name': sci_name,
        'source': img_data['source'],
        'taxonomy_id': taxonomy_id
    }
    
    result = attach_record_to_taxonomy(record, img_data['url'], metadata={
        'country': img_data.get('country'),
        'latitude': img_data.get('lat'),
        'longitude': img_data.get('lon'),
        'observation_date': img_data.get('date'),
        'year_observed': img_data.get('year'),
        'image_type': img_data.get('type', 'observation'),
        'occurrence_metadata': json.dumps({
            'inaturalist_id': img_data.get('inaturalist_id'),
            'quality_grade': img_data.get('quality_grade'),
            'observer': img_data.get('observer'),
            'num_identification_agreements': img_data.get('num_agreements', 0)
        })
    })
    
    return result.get('attached', False)


def complete_job(job_id):
    c = get_conn()
    try:
        r = c.cursor()
        r.execute("UPDATE harvest_jobs SET status='completed', completed_at=NOW() WHERE id=%s", (job_id,))
        c.commit()
    finally:
        put_conn(c)


def fail_job(job_id, error_msg):
    c = get_conn()
    try:
        r = c.cursor()
        r.execute("UPDATE harvest_jobs SET status='failed', last_error=%s WHERE id=%s", (error_msg[:200], job_id))
        c.commit()
    finally:
        put_conn(c)


def work(job):
    jid, tid, name = job
    try:
        taxon = lookup_taxon_by_id(tid)
        if not taxon.get('matched'):
            print(f"[{WORKER_ID}] Invalid taxonomy_id {tid}, skipping")
            fail_job(jid, 'Invalid taxonomy_id')
            return 0
        
        imgs = fetch_inaturalist(name)
        
        saved = 0
        for img in imgs:
            if save_via_mapper(img, tid, name):
                saved += 1
        
        stats['added'] += saved
        complete_job(jid)
        
        if saved > 0:
            rate = stats['added'] / ((time.time() - stats['start']) / 60)
            print(f"[{WORKER_ID}] {name[:40]}: +{saved} iNat | Total: {stats['added']} | {rate:.1f}/min")
        
        return saved
        
    except Exception as e:
        fail_job(jid, str(e))
        stats['errors'] += 1
        return 0


print(f"INATURALIST WORKER: {WORKER_ID} (O(1) taxonomy + centralized attach)")

while True:
    jobs = lease()
    if not jobs:
        time.sleep(5)
        continue
    
    for job in jobs:
        work(job)
