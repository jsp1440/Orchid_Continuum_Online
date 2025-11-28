#!/usr/bin/env python3
"""
ALA SOURCE-FIRST WORKER - Australian Orchid Ingestion
=======================================================
Julius AI Architecture v3 - Source-First Mode

Pulls all Orchidaceae observations from Atlas of Living Australia.
Australia is a major orchid hotspot with unique genera.
Validates against existing taxonomy, never discovers new taxa.
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
from taxonomy_mapper import lookup_taxon, attach_record_to_taxonomy

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "ala-src-1"
REQUEST_DELAY = 0.4
BATCH_SIZE = 100
THREAD_COUNT = 4

AUSTRALIAN_STATES = [
    'Queensland', 'New South Wales', 'Victoria', 
    'Western Australia', 'South Australia', 'Tasmania',
    'Northern Territory', 'Australian Capital Territory'
]

pool_obj = None
stats = {'ingested': 0, 'matched': 0, 'skipped': 0, 'start': time.time()}
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


def validate_and_match_taxonomy(occurrence):
    """
    VALIDATION ONLY - Match to existing taxonomy.
    """
    sci_name = occurrence.get('scientificName') or occurrence.get('species')
    if not sci_name:
        return None, None
    
    taxon = lookup_taxon(sci_name)
    if taxon.get('matched'):
        return taxon.get('taxonomy_id'), taxon.get('scientific_name')
    
    parts = sci_name.split()
    if len(parts) >= 2:
        simple_name = f"{parts[0]} {parts[1]}"
        taxon = lookup_taxon(simple_name)
        if taxon.get('matched'):
            return taxon.get('taxonomy_id'), taxon.get('scientific_name')
    
    return None, None


def fetch_ala_orchidaceae(start_index=0, state=None):
    """
    Pull Orchidaceae occurrences from ALA.
    """
    time.sleep(REQUEST_DELAY)
    
    q = 'family:Orchidaceae'
    if state:
        q += f' AND stateProvince:"{state}"'
    
    params = {
        'q': q,
        'fq': 'multimedia:Image',
        'pageSize': BATCH_SIZE,
        'startIndex': start_index,
        'sort': 'year',
        'dir': 'desc'
    }
    
    try:
        resp = requests.get(
            "https://biocache.ala.org.au/ws/occurrences/search",
            params=params,
            timeout=30
        )
        
        if resp.status_code != 200:
            return [], 0
        
        data = resp.json()
        return data.get('occurrences', []), data.get('totalRecords', 0)
    except Exception as e:
        print(f"[{WORKER_ID}] ALA fetch error: {e}")
        return [], 0


def process_occurrence(occ):
    """
    Process a single ALA occurrence.
    """
    family = occ.get('family', '').lower()
    if family != 'orchidaceae':
        stats['skipped'] += 1
        return 0
    
    taxonomy_id, sci_name = validate_and_match_taxonomy(occ)
    
    if not taxonomy_id:
        stats['skipped'] += 1
        return 0
    
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
        return 0
    
    if not img_url.startswith('http'):
        img_url = f"https://images.ala.org.au/image/proxyImageThumbnailLarge?imageId={img_url}"
    
    with seen_lock:
        if img_url in seen_urls:
            return 0
        seen_urls.add(img_url)
        if len(seen_urls) > 50000:
            seen_urls.clear()
    
    rec_data = {
        'scientific_name': sci_name,
        'source': 'ALA - Atlas of Living Australia',
        'taxonomy_id': taxonomy_id
    }
    
    metadata = {
        'country': 'Australia',
        'state_province': occ.get('stateProvince'),
        'locality': occ.get('locality'),
        'latitude': occ.get('decimalLatitude'),
        'longitude': occ.get('decimalLongitude'),
        'observation_date': occ.get('eventDate'),
        'year_observed': occ.get('year'),
        'image_type': 'observation',
        'institution_code': occ.get('institutionCode'),
        'observer_name': occ.get('collector'),
        'occurrence_metadata': json.dumps({
            'ala_uuid': occ.get('uuid'),
            'basis_of_record': occ.get('basisOfRecord'),
            'collector': occ.get('collector'),
            'data_resource': occ.get('dataResourceName'),
            'state': occ.get('stateProvince'),
            'coordinate_uncertainty': occ.get('coordinateUncertaintyInMeters')
        })
    }
    
    result = attach_record_to_taxonomy(rec_data, img_url, metadata=metadata)
    if result.get('attached'):
        stats['matched'] += 1
        stats['ingested'] += 1
        return 1
    
    return 0


def harvest_state(state, max_pages=15):
    """
    Harvest all Orchidaceae from a specific Australian state.
    """
    total_added = 0
    start_index = 0
    
    for page in range(max_pages):
        occurrences, total = fetch_ala_orchidaceae(start_index=start_index, state=state)
        
        if not occurrences:
            break
        
        for occ in occurrences:
            added = process_occurrence(occ)
            total_added += added
        
        start_index += BATCH_SIZE
        if start_index >= total:
            break
    
    return total_added


def main():
    print(f"ALA SOURCE-FIRST WORKER: {WORKER_ID}")
    print(f"[{WORKER_ID}] Mode: Source-first Australian Orchidaceae")
    print(f"[{WORKER_ID}] States: {len(AUSTRALIAN_STATES)}")
    print(f"[{WORKER_ID}] Validation only - no taxonomy discovery")
    
    while True:
        try:
            print(f"[{WORKER_ID}] Fetching all Australian Orchidaceae...")
            start_index = 0
            for page in range(30):
                occurrences, total = fetch_ala_orchidaceae(start_index=start_index)
                if not occurrences:
                    break
                for occ in occurrences:
                    process_occurrence(occ)
                start_index += BATCH_SIZE
                if start_index >= total:
                    break
                print(f"[{WORKER_ID}] Global page {page+1}: {start_index}/{total}")
            
            with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
                futures = {executor.submit(harvest_state, state): state for state in AUSTRALIAN_STATES}
                
                for future in as_completed(futures):
                    state = futures[future]
                    try:
                        added = future.result()
                        if added > 0:
                            print(f"[{WORKER_ID}] {state}: +{added}")
                    except Exception as e:
                        print(f"[{WORKER_ID}] {state} error: {e}")
            
            elapsed = time.time() - stats['start']
            rate = stats['ingested'] / (elapsed / 3600) if elapsed > 0 else 0
            print(f"[{WORKER_ID}] === CYCLE COMPLETE ===")
            print(f"[{WORKER_ID}] Ingested: {stats['ingested']:,} | Matched: {stats['matched']:,} | Skipped: {stats['skipped']:,}")
            print(f"[{WORKER_ID}] Rate: {rate:,.0f}/hr")
            
            print(f"[{WORKER_ID}] Sleeping 10 min before next cycle...")
            time.sleep(600)
            
        except Exception as e:
            print(f"[{WORKER_ID}] Error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
