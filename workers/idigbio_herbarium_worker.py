#!/usr/bin/env python3
"""
IDIGBIO HERBARIUM WORKER - High-Performance Specimen Harvester
===============================================================
Optimized for digitized herbarium specimen images
- Multiple institution queries
- Type specimen prioritization
- Batch media fetching
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

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "idigbio-herb-1"
BATCH_SIZE = 6
RECLAIM_MINUTES = 8
REQUEST_DELAY = 0.3
THREAD_COUNT = 4

MAJOR_HERBARIA = [
    'K',      # Kew
    'MO',     # Missouri Botanical Garden
    'NY',     # New York Botanical Garden
    'US',     # Smithsonian
    'P',      # Paris
    'L',      # Leiden
    'AMES',   # Harvard Orchid
    'SEL',    # Selby Gardens
    'FLAS',   # Florida
    'MEL',    # Melbourne
    'NSW',    # Sydney
    'BRI',    # Brisbane
    'SING',   # Singapore
    'BO',     # Bogor
    'PNH',    # Philippines
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


def fetch_idigbio_media(uuid):
    try:
        media_url = f"https://search.idigbio.org/v2/view/records/{uuid}"
        resp = requests.get(media_url, timeout=10)
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        
        if data.get('data', {}).get('ac:accessURI'):
            return data['data']['ac:accessURI']
        
        if data.get('mediarecords'):
            for media in data['mediarecords']:
                if media.get('accessuri'):
                    return media['accessuri']
        
        return None
    except:
        return None


def fetch_idigbio(name, institution=None, type_specimen=False):
    time.sleep(REQUEST_DELAY)
    simple_name = simplify_name(name)
    
    try:
        rq = {
            'scientificname': simple_name,
            'hasImage': True,
            'family': 'Orchidaceae'
        }
        
        if institution:
            rq['institutioncode'] = institution
        
        if type_specimen:
            rq['typestatus'] = {'type': 'exists'}
        
        query = {
            'rq': rq,
            'limit': 30,
            'fields': [
                'uuid', 'scientificname', 'institutioncode',
                'catalognumber', 'country', 'geopoint',
                'datecollected', 'collector', 'typestatus',
                'mediarecords'
            ]
        }
        
        resp = requests.post(
            "https://search.idigbio.org/v2/search/records",
            json=query,
            headers={'Content-Type': 'application/json'},
            timeout=20
        )
        
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        imgs = []
        
        for item in data.get('items', []):
            index_terms = item.get('indexTerms', {})
            uuid = index_terms.get('uuid')
            
            if not uuid:
                continue
            
            media_records = index_terms.get('mediarecords', [])
            if not media_records:
                continue
            
            img_url = fetch_idigbio_media(uuid)
            if not img_url:
                continue
            
            with seen_lock:
                if img_url in seen_urls:
                    continue
                seen_urls.add(img_url)
                if len(seen_urls) > 30000:
                    seen_urls.clear()
            
            geopoint = index_terms.get('geopoint', {})
            lat = geopoint.get('lat') if isinstance(geopoint, dict) else None
            lon = geopoint.get('lon') if isinstance(geopoint, dict) else None
            
            imgs.append({
                'url': img_url,
                'source': 'iDigBio',
                'type': 'herbarium',
                'country': index_terms.get('country'),
                'lat': lat,
                'lon': lon,
                'idigbio_uuid': uuid,
                'institution': index_terms.get('institutioncode'),
                'catalog_number': index_terms.get('catalognumber'),
                'collector': index_terms.get('collector'),
                'collection_date': index_terms.get('datecollected'),
                'type_status': index_terms.get('typestatus')
            })
        
        stats['fetched'] += len(imgs)
        return imgs
    except Exception as e:
        stats['errors'] += 1
        return []


def save_via_mapper(img_data, taxonomy_id, sci_name):
    record = {
        'scientific_name': sci_name,
        'source': 'iDigBio',
        'taxonomy_id': taxonomy_id
    }
    
    metadata = {
        'country': img_data.get('country'),
        'latitude': img_data.get('lat'),
        'longitude': img_data.get('lon'),
        'image_type': 'herbarium',
        'institution_code': img_data.get('institution'),
        'herbarium_catalog_number': img_data.get('catalog_number'),
        'observer_name': img_data.get('collector'),
        'observation_date': img_data.get('collection_date'),
        'occurrence_metadata': json.dumps({
            'idigbio_uuid': img_data.get('idigbio_uuid'),
            'institution': img_data.get('institution'),
            'catalog_number': img_data.get('catalog_number'),
            'collector': img_data.get('collector'),
            'collection_date': img_data.get('collection_date'),
            'type_status': img_data.get('type_status')
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
    
    global_imgs = fetch_idigbio(simple_name)
    all_images.extend(global_imgs)
    
    type_imgs = fetch_idigbio(simple_name, type_specimen=True)
    all_images.extend(type_imgs)
    
    def fetch_herbarium(inst):
        return fetch_idigbio(simple_name, institution=inst)
    
    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        futures = {executor.submit(fetch_herbarium, h): h for h in MAJOR_HERBARIA[:8]}
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
    print(f"IDIGBIO HERBARIUM WORKER: {WORKER_ID}")
    print(f"[{WORKER_ID}] Querying {len(MAJOR_HERBARIA)} major herbaria + type specimens")
    
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
                            print(f"[{WORKER_ID}] {sci_name}: +{added} specimens")
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
