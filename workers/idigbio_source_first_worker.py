#!/usr/bin/env python3
"""
IDIGBIO SOURCE-FIRST WORKER - Herbarium Specimen Ingestion
============================================================
Julius AI Architecture v3 - Source-First Mode

Pulls all Orchidaceae specimens from iDigBio directly.
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

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "idigbio-src-1"
REQUEST_DELAY = 0.4
BATCH_SIZE = 100
THREAD_COUNT = 4

MAJOR_INSTITUTIONS = [
    'K', 'MO', 'NY', 'US', 'P', 'L', 'AMES', 'SEL', 'FLAS',
    'MEL', 'NSW', 'BRI', 'SING', 'BO', 'PNH', 'E', 'BM', 'G',
    'S', 'UPS', 'W', 'M', 'B', 'PR', 'MICH', 'F', 'GH', 'UC'
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


def validate_and_match_taxonomy(index_terms):
    """
    VALIDATION ONLY - Match to existing taxonomy.
    """
    sci_name = index_terms.get('scientificname')
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


def fetch_media_url(uuid):
    """
    Fetch actual image URL from iDigBio media record.
    """
    try:
        resp = requests.get(
            f"https://search.idigbio.org/v2/view/records/{uuid}",
            timeout=10
        )
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


def fetch_idigbio_orchidaceae(offset=0, institution=None):
    """
    Pull Orchidaceae specimens from iDigBio.
    """
    time.sleep(REQUEST_DELAY)
    
    rq = {
        'family': 'Orchidaceae',
        'hasImage': True
    }
    
    if institution:
        rq['institutioncode'] = institution
    
    query = {
        'rq': rq,
        'limit': BATCH_SIZE,
        'offset': offset,
        'fields': [
            'uuid', 'scientificname', 'institutioncode',
            'catalognumber', 'country', 'geopoint',
            'datecollected', 'collector', 'typestatus',
            'stateprovince', 'locality', 'genus', 'specificepithet'
        ]
    }
    
    try:
        resp = requests.post(
            "https://search.idigbio.org/v2/search/records",
            json=query,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if resp.status_code != 200:
            return [], 0
        
        data = resp.json()
        return data.get('items', []), data.get('itemCount', 0)
    except Exception as e:
        print(f"[{WORKER_ID}] iDigBio fetch error: {e}")
        return [], 0


def process_specimen(item):
    """
    Process a single iDigBio specimen record.
    """
    index_terms = item.get('indexTerms', {})
    
    family = index_terms.get('family', '').lower()
    if family != 'orchidaceae':
        stats['skipped'] += 1
        return 0
    
    taxonomy_id, sci_name = validate_and_match_taxonomy(index_terms)
    
    if not taxonomy_id:
        stats['skipped'] += 1
        return 0
    
    uuid = index_terms.get('uuid')
    if not uuid:
        return 0
    
    img_url = fetch_media_url(uuid)
    if not img_url:
        return 0
    
    with seen_lock:
        if img_url in seen_urls:
            return 0
        seen_urls.add(img_url)
        if len(seen_urls) > 50000:
            seen_urls.clear()
    
    geopoint = index_terms.get('geopoint', {})
    lat = geopoint.get('lat') if isinstance(geopoint, dict) else None
    lon = geopoint.get('lon') if isinstance(geopoint, dict) else None
    
    rec_data = {
        'scientific_name': sci_name,
        'source': 'iDigBio',
        'taxonomy_id': taxonomy_id
    }
    
    metadata = {
        'country': index_terms.get('country'),
        'state_province': index_terms.get('stateprovince'),
        'locality': index_terms.get('locality'),
        'latitude': lat,
        'longitude': lon,
        'image_type': 'herbarium',
        'institution_code': index_terms.get('institutioncode'),
        'herbarium_catalog_number': index_terms.get('catalognumber'),
        'observer_name': index_terms.get('collector'),
        'observation_date': index_terms.get('datecollected'),
        'occurrence_metadata': json.dumps({
            'idigbio_uuid': uuid,
            'institution': index_terms.get('institutioncode'),
            'catalog_number': index_terms.get('catalognumber'),
            'collector': index_terms.get('collector'),
            'type_status': index_terms.get('typestatus'),
            'collection_date': index_terms.get('datecollected')
        })
    }
    
    result = attach_record_to_taxonomy(rec_data, img_url, metadata=metadata)
    if result.get('attached'):
        stats['matched'] += 1
        stats['ingested'] += 1
        return 1
    
    return 0


def harvest_institution(institution, max_pages=10):
    """
    Harvest all Orchidaceae from a specific institution.
    """
    total_added = 0
    offset = 0
    
    for page in range(max_pages):
        items, total = fetch_idigbio_orchidaceae(offset=offset, institution=institution)
        
        if not items:
            break
        
        for item in items:
            added = process_specimen(item)
            total_added += added
        
        offset += BATCH_SIZE
        if offset >= total:
            break
    
    return total_added


def main():
    print(f"IDIGBIO SOURCE-FIRST WORKER: {WORKER_ID}")
    print(f"[{WORKER_ID}] Mode: Source-first Orchidaceae herbarium specimens")
    print(f"[{WORKER_ID}] Institutions: {len(MAJOR_INSTITUTIONS)}")
    print(f"[{WORKER_ID}] Validation only - no taxonomy discovery")
    
    while True:
        try:
            print(f"[{WORKER_ID}] Fetching global Orchidaceae specimens...")
            offset = 0
            for page in range(20):
                items, total = fetch_idigbio_orchidaceae(offset=offset)
                if not items:
                    break
                for item in items:
                    process_specimen(item)
                offset += BATCH_SIZE
                if offset >= total:
                    break
            
            with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
                futures = {executor.submit(harvest_institution, inst): inst for inst in MAJOR_INSTITUTIONS}
                
                for future in as_completed(futures):
                    inst = futures[future]
                    try:
                        added = future.result()
                        if added > 0:
                            print(f"[{WORKER_ID}] {inst}: +{added} specimens")
                    except Exception as e:
                        print(f"[{WORKER_ID}] {inst} error: {e}")
            
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
