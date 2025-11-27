#!/usr/bin/env python3
"""
GBIF OPTIMIZED WORKER - High-Performance Version
=================================================
Key Optimizations:
1. Batch database inserts (10+ records at once)
2. Larger API result pages (100 vs 50)
3. Parallel country fetching with ThreadPoolExecutor
4. In-memory URL deduplication cache
5. Reduced delays (0.15s vs 0.3s)
6. Connection pooling with larger pool
7. O(1) taxonomy lookup via taxonomy_mapper
"""
import os
import sys
import time
import requests
import psycopg2
import json
import threading
from psycopg2 import pool, extras
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taxonomy_mapper import lookup_taxon, lookup_taxon_by_id

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "opt-1"

TOP_COUNTRIES = [
    'EC', 'CO', 'PE', 'BR', 'MX', 'VE', 'CR', 'PA', 'BO', 'GT',
    'MY', 'ID', 'PH', 'TH', 'VN', 'IN', 'CN', 'MM', 'NP', 'LK',
    'MG', 'TZ', 'KE', 'ZA', 'CD', 'CM', 'NG', 'GH', 'ET', 'UG',
    'AU', 'NZ', 'PG', 'NC', 'FJ', 'SB',
    'US', 'JP', 'TW', 'GB', 'ES', 'FR', 'IT', 'DE', 'GR', 'TR',
    'CU', 'JM', 'HT', 'DO', 'PR'
]

BATCH_SIZE = 8
REQUEST_DELAY = 0.15
API_LIMIT = 100

pool_obj = None
stats = {'added': 0, 'start': time.time(), 'fetched': 0, 'batches': 0}

seen_urls = set()
seen_lock = threading.Lock()

insert_buffer = []
buffer_lock = threading.Lock()


def init_pool():
    global pool_obj
    db_url = os.environ.get('DATABASE_URL')
    pool_obj = pool.ThreadedConnectionPool(minconn=2, maxconn=8, dsn=db_url)


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


def fetch_gbif(name, country=None):
    time.sleep(REQUEST_DELAY)
    
    params = {
        'scientificName': name, 
        'mediaType': 'StillImage', 
        'limit': API_LIMIT,
        'hasCoordinate': 'true'
    }
    if country:
        params['country'] = country
    
    try:
        resp = requests.get(
            "https://api.gbif.org/v1/occurrence/search",
            params=params,
            timeout=20
        )
        
        if resp.status_code == 429:
            time.sleep(60)
            return []
        
        if resp.status_code != 200:
            return []
        
        images = []
        for rec in resp.json().get('results', []):
            for m in rec.get('media', []):
                if m.get('type') == 'StillImage' and m.get('identifier'):
                    url = m['identifier']
                    
                    with seen_lock:
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)
                        if len(seen_urls) > 100000:
                            seen_urls.clear()
                    
                    images.append({
                        'url': url,
                        'country': rec.get('country'),
                        'locality': rec.get('locality'),
                        'lat': rec.get('decimalLatitude'),
                        'lon': rec.get('decimalLongitude'),
                        'observer': rec.get('recordedBy'),
                        'license': m.get('license'),
                        'gbif_key': rec.get('key')
                    })
        
        stats['fetched'] += len(images)
        return images
    except Exception:
        return []


def flush_buffer(taxonomy_id):
    global insert_buffer
    
    with buffer_lock:
        if not insert_buffer:
            return 0
        batch = insert_buffer.copy()
        insert_buffer = []
    
    if not batch:
        return 0
    
    c = None
    try:
        c = get_conn()
        cur = c.cursor()
        
        values = [(
            taxonomy_id,
            img['url'],
            'GBIF',
            img.get('gbif_key'),
            img.get('country'),
            img.get('locality'),
            img.get('lat'),
            img.get('lon'),
            img.get('observer'),
            img.get('license')
        ) for img in batch]
        
        extras.execute_batch(cur, """
            INSERT INTO orchid_images (
                taxonomy_id, image_url, image_source, gbif_occurrence_key,
                country, locality, latitude, longitude, observer_name, image_license
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (image_url) DO NOTHING
        """, values, page_size=50)
        
        c.commit()
        added = cur.rowcount
        stats['added'] += added
        stats['batches'] += 1
        put_conn(c)
        return added
    except Exception:
        if c:
            try:
                c.rollback()
            except Exception:
                pass
            put_conn(c)
        return 0


def harvest_species(taxonomy_id, sci_name):
    taxon = lookup_taxon_by_id(taxonomy_id)
    if not taxon.get('matched'):
        print(f"[{WORKER_ID}] Invalid taxonomy_id {taxonomy_id}, skipping")
        return 0
    
    parts = sci_name.split() if sci_name else ['Unknown']
    genus = parts[0]
    species = parts[1] if len(parts) > 1 else ''
    name = f"{genus} {species}".strip()
    
    global_images = fetch_gbif(name)
    with buffer_lock:
        insert_buffer.extend(global_images)
    
    def fetch_country(country):
        return fetch_gbif(name, country)
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_country, c): c for c in TOP_COUNTRIES[:20]}
        
        for future in as_completed(futures):
            try:
                images = future.result()
                with buffer_lock:
                    insert_buffer.extend(images)
            except Exception:
                pass
    
    added = flush_buffer(taxonomy_id)
    return added


def lease_jobs(n=BATCH_SIZE):
    c = None
    try:
        c = get_conn()
        cur = c.cursor()
        
        cur.execute("""
            UPDATE harvest_jobs 
            SET status='pending', lease_owner=NULL 
            WHERE status='leased' AND leased_at < NOW() - INTERVAL '5 minutes'
        """)
        
        cur.execute("""
            UPDATE harvest_jobs 
            SET status='leased', lease_owner=%s, leased_at=NOW() 
            WHERE id IN (
                SELECT id FROM harvest_jobs 
                WHERE status='pending' 
                ORDER BY priority DESC 
                LIMIT %s 
                FOR UPDATE SKIP LOCKED
            ) 
            RETURNING id, taxonomy_id, scientific_name
        """, (WORKER_ID, n))
        
        jobs = cur.fetchall()
        c.commit()
        put_conn(c)
        return jobs
    except Exception:
        if c:
            try:
                c.rollback()
            except Exception:
                pass
            put_conn(c)
        return []


def complete_job(job_id):
    c = None
    try:
        c = get_conn()
        cur = c.cursor()
        cur.execute("UPDATE harvest_jobs SET status='completed' WHERE id=%s", (job_id,))
        c.commit()
        put_conn(c)
    except Exception:
        if c:
            try:
                c.rollback()
            except Exception:
                pass
            put_conn(c)


def main():
    print(f"[{WORKER_ID}] OPTIMIZED WORKER starting with O(1) taxonomy lookup...")
    init_pool()
    
    while True:
        try:
            jobs = lease_jobs()
            
            if not jobs:
                print(f"[{WORKER_ID}] No jobs, waiting 30s...")
                time.sleep(30)
                continue
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(harvest_species, job[1], job[2]): job
                    for job in jobs
                }
                
                for future in as_completed(futures):
                    job = futures[future]
                    try:
                        added = future.result()
                        complete_job(job[0])
                        if added > 0:
                            print(f"[{WORKER_ID}] {job[2]}: +{added}")
                    except Exception:
                        pass
            
            elapsed = time.time() - stats['start']
            rate = stats['added'] / (elapsed / 3600) if elapsed > 0 else 0
            print(f"[{WORKER_ID}] Total: {stats['added']:,} | Rate: {rate:,.0f}/hr | Batches: {stats['batches']}")
            
        except KeyboardInterrupt:
            print(f"[{WORKER_ID}] Shutdown")
            break
        except Exception as e:
            print(f"[{WORKER_ID}] Error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
