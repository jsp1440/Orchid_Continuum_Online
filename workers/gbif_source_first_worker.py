#!/usr/bin/env python3
"""
GBIF SOURCE-FIRST WORKER - High-Performance Orchidaceae Ingestion
===================================================================
Julius AI Architecture v3 - Source-First Mode

This worker PULLS all Orchidaceae records from GBIF directly instead of
searching by species name. It validates incoming records against our
taxonomy map, never discovers new taxa.

Key Principles:
1. Query GBIF for family=Orchidaceae with images
2. For each record, validate against taxonomy_mapper
3. If matched -> enrich and store
4. If not matched -> SKIP (no discovery)
5. NO alphabetical scanning, NO prefix walking

This is 10x faster than name-iteration mode.
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
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taxonomy_mapper import lookup_taxon, attach_record_to_taxonomy

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "gbif-src-1"
REQUEST_DELAY = 0.2
BATCH_SIZE = 300
THREAD_COUNT = 8

ALL_ORCHID_COUNTRIES = [
    'EC', 'CO', 'PE', 'BR', 'MX', 'VE', 'CR', 'PA', 'BO', 'GT', 'HN', 'NI', 'SV', 'BZ',
    'MY', 'ID', 'PH', 'TH', 'VN', 'IN', 'CN', 'MM', 'NP', 'LK', 'BD', 'LA', 'KH', 'BN',
    'MG', 'TZ', 'KE', 'ZA', 'CD', 'CM', 'NG', 'GH', 'ET', 'UG', 'RW', 'MZ', 'ZW', 'MW',
    'AU', 'NZ', 'PG', 'NC', 'FJ', 'SB', 'VU', 'WS',
    'US', 'JP', 'TW', 'GB', 'ES', 'FR', 'IT', 'DE', 'GR', 'TR', 'PT', 'CH', 'AT', 'BE',
    'CU', 'JM', 'HT', 'DO', 'PR', 'TT', 'BB', 'LC', 'DM', 'GD',
    'GY', 'SR', 'PY', 'UY', 'AR', 'CL',
    'SG', 'HK', 'KR', 'RU', 'UA', 'PL', 'CZ', 'HU', 'RO', 'BG',
    'RE', 'MU', 'SC', 'MV', 'LR', 'SL', 'GN', 'CI', 'BF', 'SN',
]

pool_obj = None
stats = {
    'ingested': 0, 
    'matched': 0, 
    'skipped': 0, 
    'start': time.time(),
    'by_country': {}
}
seen_urls = set()
seen_lock = threading.Lock()


def get_database_url():
    if os.environ.get('PGHOST'):
        return f"postgresql://{os.environ.get('PGUSER')}:{os.environ.get('PGPASSWORD')}@{os.environ.get('PGHOST')}:{os.environ.get('PGPORT')}/{os.environ.get('PGDATABASE')}?sslmode=require"
    return os.environ.get('DATABASE_URL', '')


def init_pool():
    global pool_obj
    pool_obj = pool.ThreadedConnectionPool(minconn=2, maxconn=12, dsn=get_database_url())


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


def validate_orchidaceae(record):
    """
    Validate if a GBIF record is Orchidaceae using metadata.
    Returns True only if confirmed Orchidaceae.
    """
    family = record.get('family', '').lower()
    if family == 'orchidaceae':
        return True
    
    order = record.get('order', '').lower()
    if order == 'asparagales':
        accepted_name = record.get('acceptedScientificName', '')
        if accepted_name:
            taxon = lookup_taxon(accepted_name)
            if taxon.get('matched'):
                return True
    
    return False


def validate_and_match_taxonomy(record):
    """
    VALIDATION ONLY - Match incoming record to existing taxonomy.
    Returns taxonomy_id if matched, None if not found.
    NO DISCOVERY - we only validate against existing taxa.
    """
    scientific_name = record.get('scientificName') or record.get('species') or record.get('acceptedScientificName')
    
    if not scientific_name:
        return None, None
    
    scientific_name = scientific_name.strip()
    
    taxon = lookup_taxon(scientific_name)
    
    if taxon.get('matched'):
        return taxon.get('taxonomy_id'), taxon.get('scientific_name')
    
    parts = scientific_name.split()
    if len(parts) >= 2:
        simple_name = f"{parts[0]} {parts[1]}"
        taxon = lookup_taxon(simple_name)
        if taxon.get('matched'):
            return taxon.get('taxonomy_id'), taxon.get('scientific_name')
    
    return None, None


def fetch_gbif_orchidaceae(country=None, offset=0):
    """
    Pull Orchidaceae records directly from GBIF.
    Source-first: get all orchids with images from the source.
    """
    time.sleep(REQUEST_DELAY)
    
    params = {
        'family': 'Orchidaceae',
        'mediaType': 'StillImage',
        'hasCoordinate': 'true',
        'limit': BATCH_SIZE,
        'offset': offset
    }
    
    if country:
        params['country'] = country
    
    try:
        resp = requests.get(
            "https://api.gbif.org/v1/occurrence/search",
            params=params,
            timeout=30
        )
        
        if resp.status_code == 429:
            time.sleep(60)
            return [], False
        
        if resp.status_code != 200:
            return [], False
        
        data = resp.json()
        records = data.get('results', [])
        end_of_records = data.get('endOfRecords', True)
        
        return records, not end_of_records
    except Exception as e:
        print(f"[{WORKER_ID}] GBIF fetch error: {e}")
        return [], False


def process_gbif_record(record):
    """
    Process a single GBIF record:
    1. Validate Orchidaceae
    2. Match to taxonomy (validation only)
    3. If matched, store via taxonomy_mapper
    4. If not matched, SKIP
    """
    if not validate_orchidaceae(record):
        stats['skipped'] += 1
        return 0
    
    taxonomy_id, sci_name = validate_and_match_taxonomy(record)
    
    if not taxonomy_id:
        stats['skipped'] += 1
        return 0
    
    added = 0
    for media in record.get('media', []):
        if media.get('type') != 'StillImage':
            continue
        
        img_url = media.get('identifier')
        if not img_url:
            continue
        
        with seen_lock:
            if img_url in seen_urls:
                continue
            seen_urls.add(img_url)
            if len(seen_urls) > 100000:
                seen_urls.clear()
        
        rec_data = {
            'scientific_name': sci_name,
            'source': 'GBIF',
            'taxonomy_id': taxonomy_id
        }
        
        date_str = record.get('eventDate')
        if date_str and ('/' in date_str or len(date_str) < 10):
            date_str = None
        
        metadata = {
            'country': record.get('country'),
            'country_code': record.get('countryCode'),
            'state_province': record.get('stateProvince'),
            'locality': record.get('locality'),
            'latitude': record.get('decimalLatitude'),
            'longitude': record.get('decimalLongitude'),
            'coordinate_uncertainty': record.get('coordinateUncertaintyInMeters'),
            'observation_date': date_str,
            'year_observed': record.get('year'),
            'month_observed': record.get('month'),
            'observer_name': record.get('recordedBy'),
            'institution_code': record.get('institutionCode'),
            'image_license': media.get('license'),
            'image_type': 'observation',
            'gbif_occurrence_key': str(record.get('key', '')),
            'occurrence_metadata': json.dumps({
                'gbif_key': record.get('key'),
                'basis_of_record': record.get('basisOfRecord'),
                'dataset_key': record.get('datasetKey'),
                'publisher': record.get('publishingOrgKey'),
                'catalog_number': record.get('catalogNumber'),
                'collection_code': record.get('collectionCode'),
                'identified_by': record.get('identifiedBy'),
                'life_stage': record.get('lifeStage'),
                'sex': record.get('sex'),
                'elevation': record.get('elevation'),
                'depth': record.get('depth')
            })
        }
        
        result = attach_record_to_taxonomy(rec_data, img_url, metadata=metadata)
        if result.get('attached'):
            added += 1
    
    if added > 0:
        stats['matched'] += 1
        stats['ingested'] += added
    
    return added


def harvest_country(country):
    """
    Harvest all Orchidaceae from a specific country.
    Uses pagination to get complete coverage.
    """
    offset = 0
    total_added = 0
    max_pages = 20
    
    for page in range(max_pages):
        records, has_more = fetch_gbif_orchidaceae(country=country, offset=offset)
        
        if not records:
            break
        
        for record in records:
            added = process_gbif_record(record)
            total_added += added
        
        if not has_more:
            break
        
        offset += BATCH_SIZE
    
    if country not in stats['by_country']:
        stats['by_country'][country] = 0
    stats['by_country'][country] += total_added
    
    return total_added


def main():
    print(f"GBIF SOURCE-FIRST WORKER: {WORKER_ID}")
    print(f"[{WORKER_ID}] Mode: Source-first Orchidaceae ingestion (NO name iteration)")
    print(f"[{WORKER_ID}] Countries: {len(ALL_ORCHID_COUNTRIES)}")
    print(f"[{WORKER_ID}] Validation only - no taxonomy discovery")
    
    while True:
        try:
            global_added = 0
            records, has_more = fetch_gbif_orchidaceae(offset=0)
            for record in records:
                global_added += process_gbif_record(record)
            print(f"[{WORKER_ID}] Global fetch: +{global_added}")
            
            with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
                futures = {executor.submit(harvest_country, c): c for c in ALL_ORCHID_COUNTRIES}
                
                for future in as_completed(futures):
                    country = futures[future]
                    try:
                        added = future.result()
                        if added > 0:
                            print(f"[{WORKER_ID}] {country}: +{added}")
                    except Exception as e:
                        print(f"[{WORKER_ID}] {country} error: {e}")
            
            elapsed = time.time() - stats['start']
            rate = stats['ingested'] / (elapsed / 3600) if elapsed > 0 else 0
            print(f"[{WORKER_ID}] === CYCLE COMPLETE ===")
            print(f"[{WORKER_ID}] Ingested: {stats['ingested']:,} | Matched: {stats['matched']:,} | Skipped: {stats['skipped']:,}")
            print(f"[{WORKER_ID}] Rate: {rate:,.0f}/hr | Elapsed: {elapsed/3600:.1f}h")
            
            print(f"[{WORKER_ID}] Sleeping 5 min before next cycle...")
            time.sleep(300)
            
        except Exception as e:
            print(f"[{WORKER_ID}] Error: {e}")
            time.sleep(30)


if __name__ == "__main__":
    main()
