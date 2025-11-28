#!/usr/bin/env python3
"""
EOL TRAITBANK WORKER - Phenotypic Data & Images
=================================================
Julius AI Architecture v3 - Source-First Mode

Pulls Orchidaceae data from Encyclopedia of Life including:
- Images with proper attribution
- TraitBank phenotypic data
- Morphological traits

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

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "eol-trait-1"
REQUEST_DELAY = 0.5
THREAD_COUNT = 4

EOL_ORCHIDACEAE_PAGE = 8156

pool_obj = None
stats = {'ingested': 0, 'matched': 0, 'traits_harvested': 0, 'skipped': 0, 'start': time.time()}
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


def search_eol_orchidaceae(page=1, per_page=50):
    """
    Search EOL for Orchidaceae pages.
    """
    time.sleep(REQUEST_DELAY)
    
    try:
        resp = requests.get(
            "https://eol.org/api/search/1.0.json",
            params={
                'q': 'Orchidaceae',
                'page': page,
                'exact': False,
                'filter_by_taxon_concept_id': '',
                'filter_by_hierarchy_entry_id': '',
                'filter_by_string': ''
            },
            timeout=20
        )
        
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        return data.get('results', [])
    except Exception as e:
        print(f"[{WORKER_ID}] EOL search error: {e}")
        return []


def get_eol_page_details(page_id):
    """
    Get detailed page info including images and traits.
    """
    time.sleep(REQUEST_DELAY)
    
    try:
        resp = requests.get(
            f"https://eol.org/api/pages/1.0/{page_id}.json",
            params={
                'images_per_page': 10,
                'videos_per_page': 0,
                'sounds_per_page': 0,
                'maps_per_page': 0,
                'texts_per_page': 0,
                'details': True,
                'common_names': False,
                'synonyms': False,
                'references': False,
                'taxonomy': True
            },
            timeout=20
        )
        
        if resp.status_code != 200:
            return None
        
        return resp.json()
    except Exception as e:
        return None


def get_eol_traits(page_id):
    """
    Get TraitBank data for a page.
    """
    time.sleep(REQUEST_DELAY)
    
    try:
        resp = requests.get(
            f"https://eol.org/api/traits/{page_id}",
            timeout=20
        )
        
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        return data.get('data', [])
    except Exception as e:
        return []


def validate_and_match_taxonomy(page_data):
    """
    VALIDATION ONLY - Match EOL page to existing taxonomy.
    """
    if not page_data:
        return None, None
    
    sci_name = page_data.get('scientificName')
    if not sci_name:
        taxon_concepts = page_data.get('taxonConcepts', [])
        if taxon_concepts:
            sci_name = taxon_concepts[0].get('scientificName')
    
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


def process_eol_page(page_data):
    """
    Process an EOL page: extract images and traits.
    """
    if not page_data:
        stats['skipped'] += 1
        return 0
    
    taxonomy_id, sci_name = validate_and_match_taxonomy(page_data)
    
    if not taxonomy_id:
        stats['skipped'] += 1
        return 0
    
    page_id = page_data.get('identifier')
    
    traits = get_eol_traits(page_id)
    if traits:
        stats['traits_harvested'] += len(traits)
    
    data_objects = page_data.get('dataObjects', [])
    if not data_objects:
        return 0
    
    added = 0
    for obj in data_objects:
        if obj.get('dataType') != 'http://purl.org/dc/dcmitype/StillImage':
            continue
        
        img_url = obj.get('eolMediaURL') or obj.get('mediaURL')
        if not img_url:
            continue
        
        with seen_lock:
            if img_url in seen_urls:
                continue
            seen_urls.add(img_url)
            if len(seen_urls) > 50000:
                seen_urls.clear()
        
        rec_data = {
            'scientific_name': sci_name,
            'source': 'EOL',
            'taxonomy_id': taxonomy_id
        }
        
        trait_summary = {}
        for trait in traits[:10]:
            predicate = trait.get('predicate', {}).get('name', '')
            value = trait.get('object', {}).get('name', '') or trait.get('literal', '')
            if predicate and value:
                trait_summary[predicate] = value
        
        metadata = {
            'image_type': 'reference',
            'image_license': obj.get('license'),
            'image_rights_holder': obj.get('rightsHolder'),
            'image_description': obj.get('description', '')[:500] if obj.get('description') else None,
            'eol_page_id': page_id,
            'eol_data_object_id': obj.get('identifier'),
            'eol_metadata': json.dumps({
                'page_id': page_id,
                'data_object_id': obj.get('identifier'),
                'license': obj.get('license'),
                'rights_holder': obj.get('rightsHolder'),
                'source': obj.get('source'),
                'agents': [a.get('full_name') for a in obj.get('agents', [])[:3]],
                'traits': trait_summary
            })
        }
        
        result = attach_record_to_taxonomy(rec_data, img_url, metadata=metadata)
        if result.get('attached'):
            added += 1
    
    if added > 0:
        stats['matched'] += 1
        stats['ingested'] += added
    
    return added


def harvest_eol_search_results():
    """
    Search EOL for Orchidaceae and process results.
    """
    total_added = 0
    
    for page in range(1, 21):
        results = search_eol_orchidaceae(page=page)
        
        if not results:
            break
        
        for result in results:
            page_id = result.get('id')
            if not page_id:
                continue
            
            page_data = get_eol_page_details(page_id)
            if page_data:
                added = process_eol_page(page_data)
                total_added += added
        
        print(f"[{WORKER_ID}] EOL search page {page}: processed {len(results)} results")
    
    return total_added


def main():
    print(f"EOL TRAITBANK WORKER: {WORKER_ID}")
    print(f"[{WORKER_ID}] Mode: Source-first Orchidaceae + TraitBank phenotypic data")
    print(f"[{WORKER_ID}] Validation only - no taxonomy discovery")
    
    while True:
        try:
            harvest_eol_search_results()
            
            elapsed = time.time() - stats['start']
            rate = stats['ingested'] / (elapsed / 3600) if elapsed > 0 else 0
            print(f"[{WORKER_ID}] === CYCLE COMPLETE ===")
            print(f"[{WORKER_ID}] Images: {stats['ingested']:,} | Traits: {stats['traits_harvested']:,} | Matched: {stats['matched']:,}")
            print(f"[{WORKER_ID}] Rate: {rate:,.0f}/hr")
            
            print(f"[{WORKER_ID}] Sleeping 10 min before next cycle...")
            time.sleep(600)
            
        except Exception as e:
            print(f"[{WORKER_ID}] Error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
