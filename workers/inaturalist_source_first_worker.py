#!/usr/bin/env python3
"""
INATURALIST SOURCE-FIRST WORKER - High-Performance Orchidaceae Ingestion
=========================================================================
Julius AI Architecture v3 - Source-First Mode

Pulls all Orchidaceae observations from iNaturalist directly.
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

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "inat-src-1"
REQUEST_DELAY = 0.3
BATCH_SIZE = 200
THREAD_COUNT = 6

ORCHIDACEAE_TAXON_ID = 47217

ORCHID_PLACES = [
    6853, 7112, 7124, 6878, 6930, 6793,  # S. America
    6744, 6681, 6903, 6712, 6698, 6682, 6683,  # Asia-Pacific
    7161, 7008, 6756,  # Africa
    1, 6803, 7062, 6970  # Global hotspots
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


def validate_and_match_taxonomy(taxon_data):
    """
    VALIDATION ONLY - Match to existing taxonomy.
    NO DISCOVERY.
    """
    if not taxon_data:
        return None, None
    
    name = taxon_data.get('name')
    if not name:
        return None, None
    
    taxon = lookup_taxon(name)
    if taxon.get('matched'):
        return taxon.get('taxonomy_id'), taxon.get('scientific_name')
    
    ancestors = taxon_data.get('ancestors', [])
    for ancestor in ancestors:
        if ancestor.get('rank') == 'species':
            taxon = lookup_taxon(ancestor.get('name', ''))
            if taxon.get('matched'):
                return taxon.get('taxonomy_id'), taxon.get('scientific_name')
    
    return None, None


def fetch_inaturalist_orchidaceae(place_id=None, page=1, quality='research'):
    """
    Pull Orchidaceae observations directly from iNaturalist.
    """
    time.sleep(REQUEST_DELAY)
    
    params = {
        'taxon_id': ORCHIDACEAE_TAXON_ID,
        'quality_grade': quality,
        'photos': 'true',
        'per_page': BATCH_SIZE,
        'page': page,
        'order': 'desc',
        'order_by': 'created_at'
    }
    
    if place_id:
        params['place_id'] = place_id
    
    try:
        resp = requests.get(
            "https://api.inaturalist.org/v1/observations",
            params=params,
            timeout=30
        )
        
        if resp.status_code == 429:
            time.sleep(60)
            return [], 0
        
        if resp.status_code != 200:
            return [], 0
        
        data = resp.json()
        return data.get('results', []), data.get('total_results', 0)
    except Exception as e:
        print(f"[{WORKER_ID}] iNaturalist fetch error: {e}")
        return [], 0


def process_observation(obs):
    """
    Process a single iNaturalist observation.
    """
    taxon_data = obs.get('taxon')
    if not taxon_data:
        stats['skipped'] += 1
        return 0
    
    ancestry = taxon_data.get('ancestry', '')
    if 'Orchidaceae' not in taxon_data.get('name', '') and '47217' not in str(ancestry):
        iconic = taxon_data.get('iconic_taxon_name', '')
        if iconic != 'Plantae':
            stats['skipped'] += 1
            return 0
    
    taxonomy_id, sci_name = validate_and_match_taxonomy(taxon_data)
    
    if not taxonomy_id:
        stats['skipped'] += 1
        return 0
    
    photos = obs.get('photos', [])
    if not photos:
        return 0
    
    added = 0
    for photo in photos[:3]:
        img_url = photo.get('url')
        if not img_url:
            continue
        
        img_url = img_url.replace('square', 'large').replace('medium', 'large')
        
        with seen_lock:
            if img_url in seen_urls:
                continue
            seen_urls.add(img_url)
            if len(seen_urls) > 100000:
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
        
        rec_data = {
            'scientific_name': sci_name,
            'source': 'iNaturalist',
            'taxonomy_id': taxonomy_id
        }
        
        place_guess = obs.get('place_guess', '')
        
        metadata = {
            'country': place_guess.split(',')[-1].strip() if ',' in place_guess else place_guess,
            'locality': place_guess,
            'latitude': lat,
            'longitude': lon,
            'observation_date': obs.get('observed_on'),
            'year_observed': obs.get('observed_on_details', {}).get('year') if obs.get('observed_on_details') else None,
            'image_type': 'observation',
            'image_license': photo.get('license_code'),
            'occurrence_metadata': json.dumps({
                'inaturalist_id': obs.get('id'),
                'quality_grade': obs.get('quality_grade'),
                'observer': obs.get('user', {}).get('login') if obs.get('user') else None,
                'num_identification_agreements': obs.get('num_identification_agreements', 0),
                'captive': obs.get('captive', False),
                'geoprivacy': obs.get('geoprivacy')
            })
        }
        
        result = attach_record_to_taxonomy(rec_data, img_url, metadata=metadata)
        if result.get('attached'):
            added += 1
    
    if added > 0:
        stats['matched'] += 1
        stats['ingested'] += added
    
    return added


def harvest_place(place_id, max_pages=10):
    """
    Harvest all Orchidaceae from a specific place.
    """
    total_added = 0
    
    for page in range(1, max_pages + 1):
        observations, total = fetch_inaturalist_orchidaceae(place_id=place_id, page=page)
        
        if not observations:
            break
        
        for obs in observations:
            added = process_observation(obs)
            total_added += added
        
        if len(observations) < BATCH_SIZE:
            break
    
    return total_added


def main():
    print(f"INATURALIST SOURCE-FIRST WORKER: {WORKER_ID}")
    print(f"[{WORKER_ID}] Mode: Source-first Orchidaceae ingestion (taxon_id={ORCHIDACEAE_TAXON_ID})")
    print(f"[{WORKER_ID}] Places: {len(ORCHID_PLACES)}")
    print(f"[{WORKER_ID}] Validation only - no taxonomy discovery")
    
    while True:
        try:
            print(f"[{WORKER_ID}] Fetching global research-grade...")
            for page in range(1, 11):
                observations, _ = fetch_inaturalist_orchidaceae(page=page, quality='research')
                for obs in observations:
                    process_observation(obs)
                if len(observations) < BATCH_SIZE:
                    break
            
            with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
                futures = {executor.submit(harvest_place, p): p for p in ORCHID_PLACES}
                
                for future in as_completed(futures):
                    place_id = futures[future]
                    try:
                        added = future.result()
                        if added > 0:
                            print(f"[{WORKER_ID}] Place {place_id}: +{added}")
                    except Exception as e:
                        print(f"[{WORKER_ID}] Place {place_id} error: {e}")
            
            elapsed = time.time() - stats['start']
            rate = stats['ingested'] / (elapsed / 3600) if elapsed > 0 else 0
            print(f"[{WORKER_ID}] === CYCLE COMPLETE ===")
            print(f"[{WORKER_ID}] Ingested: {stats['ingested']:,} | Matched: {stats['matched']:,} | Skipped: {stats['skipped']:,}")
            print(f"[{WORKER_ID}] Rate: {rate:,.0f}/hr")
            
            print(f"[{WORKER_ID}] Sleeping 5 min before next cycle...")
            time.sleep(300)
            
        except Exception as e:
            print(f"[{WORKER_ID}] Error: {e}")
            time.sleep(30)


if __name__ == "__main__":
    main()
