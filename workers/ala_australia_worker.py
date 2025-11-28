#!/usr/bin/env python3
"""
ALA AUSTRALIA WORKER - Atlas of Living Australia Specialist
============================================================
Optimized for Australian orchid observations and specimens
- Australian native orchids (Pterostylis, Caladenia, Thelymitra, Diuris, etc.)
- State-based queries for comprehensive coverage
- High-quality curated images
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

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "ala-aus-1"
BATCH_SIZE = 8
RECLAIM_MINUTES = 8
REQUEST_DELAY = 0.35
THREAD_COUNT = 4

AUSTRALIAN_STATES = [
    'Queensland',
    'New South Wales',
    'Victoria',
    'Western Australia',
    'South Australia',
    'Tasmania',
    'Northern Territory'
]

AUSTRALIAN_ORCHID_GENERA = [
    'Pterostylis', 'Caladenia', 'Thelymitra', 'Diuris', 'Prasophyllum',
    'Dendrobium', 'Bulbophyllum', 'Sarcochilus', 'Liparis', 'Oberonia',
    'Cryptostylis', 'Acianthus', 'Corybas', 'Chiloglottis', 'Caleana',
    'Drakaea', 'Rhizanthella', 'Gastrodia', 'Dipodium', 'Cymbidium'
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
    pool_obj = pool.ThreadedConnectionPool(minconn=2, maxconn=8, dsn=get_database_url())


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


def fetch_ala(name, state=None):
    time.sleep(REQUEST_DELAY)
    simple_name = simplify_name(name)
    
    try:
        q = f'scientificName:"{simple_name}" AND family:Orchidaceae'
        if state:
            q += f' AND stateProvince:"{state}"'
        
        params = {
            'q': q,
            'fq': 'multimedia:Image',
            'pageSize': 50,
            'sort': 'year',
            'dir': 'desc'
        }
        
        resp = requests.get(
            "https://biocache.ala.org.au/ws/occurrences/search",
            params=params,
            timeout=20
        )
        
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        imgs = []
        
        for occ in data.get('occurrences', []):
            img_url = occ.get('largeImageUrl') or occ.get('smallImageUrl') or occ.get('thumbnailUrl')
            
            if not img_url:
                images = occ.get('images', [])
                if images:
                    img_url = images[0] if isinstance(images[0], str) else images[0].get('url')
            
            if not img_url:
                image_id = occ.get('image')
                if image_id:
                    img_url = f"https://images.ala.org.au/image/proxyImageThumbnailLarge?imageId={image_id}"
            
            if not img_url:
                continue
            
            if not img_url.startswith('http'):
                img_url = f"https://images.ala.org.au/image/proxyImageThumbnailLarge?imageId={img_url}"
            
            with seen_lock:
                if img_url in seen_urls:
                    continue
                seen_urls.add(img_url)
                if len(seen_urls) > 30000:
                    seen_urls.clear()
            
            imgs.append({
                'url': img_url,
                'source': 'ALA - Atlas of Living Australia',
                'type': 'observation',
                'country': 'Australia',
                'state': occ.get('stateProvince'),
                'locality': occ.get('locality'),
                'lat': occ.get('decimalLatitude'),
                'lon': occ.get('decimalLongitude'),
                'date': occ.get('eventDate'),
                'year': occ.get('year'),
                'ala_uuid': occ.get('uuid'),
                'basis_of_record': occ.get('basisOfRecord'),
                'collector': occ.get('collector'),
                'institution': occ.get('institutionCode'),
                'data_resource': occ.get('dataResourceName')
            })
        
        stats['fetched'] += len(imgs)
        return imgs
    except Exception as e:
        stats['errors'] += 1
        return []


def save_via_mapper(img_data, taxonomy_id, sci_name):
    record = {
        'scientific_name': sci_name,
        'source': 'ALA - Atlas of Living Australia',
        'taxonomy_id': taxonomy_id
    }
    
    metadata = {
        'country': 'Australia',
        'state_province': img_data.get('state'),
        'locality': img_data.get('locality'),
        'latitude': img_data.get('lat'),
        'longitude': img_data.get('lon'),
        'observation_date': img_data.get('date'),
        'year_observed': img_data.get('year'),
        'image_type': img_data.get('type', 'observation'),
        'institution_code': img_data.get('institution'),
        'observer_name': img_data.get('collector'),
        'occurrence_metadata': json.dumps({
            'ala_uuid': img_data.get('ala_uuid'),
            'basis_of_record': img_data.get('basis_of_record'),
            'collector': img_data.get('collector'),
            'data_resource': img_data.get('data_resource'),
            'state': img_data.get('state')
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
    
    global_imgs = fetch_ala(simple_name)
    all_images.extend(global_imgs)
    
    def fetch_state(state):
        return fetch_ala(simple_name, state=state)
    
    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        futures = {executor.submit(fetch_state, s): s for s in AUSTRALIAN_STATES}
        for future in as_completed(futures):
            try:
                imgs = future.result()
                all_images.extend(imgs)
            except Exception:
                pass
    
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
    print(f"ALA AUSTRALIA WORKER: {WORKER_ID}")
    print(f"[{WORKER_ID}] Querying all {len(AUSTRALIAN_STATES)} Australian states")
    
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
            print(f"[{WORKER_ID}] Total: {stats['added']:,} | Rate: {rate:,.0f}/hr")
            
        except Exception as e:
            print(f"[{WORKER_ID}] Error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
