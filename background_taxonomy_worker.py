#!/usr/bin/env python3
"""
Background Taxonomy Worker - Gradually fetch missing EOL taxonomy
Runs continuously, saves progress, handles failures gracefully
"""
import os
import time
import json
import requests
import psycopg2
from datetime import datetime
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROGRESS_FILE = 'taxonomy_worker_progress.json'
BATCH_SIZE = 50  # Process 50 species per batch
DELAY_BETWEEN_REQUESTS = 0.5  # seconds
DELAY_BETWEEN_BATCHES = 5  # seconds

def load_progress():
    """Load progress from file"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'processed': [], 'failed': [], 'last_run': None}

def save_progress(progress):
    """Save progress to file"""
    progress['last_run'] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def get_missing_eol_ids():
    """Get list of EOL page IDs that need taxonomy"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Get existing EOL IDs in taxonomy table
    cur.execute("SELECT eol_page_id FROM orchid_taxonomy WHERE eol_page_id IS NOT NULL")
    existing = set(str(row[0]) for row in cur.fetchall())
    
    # Load all orchid EOL IDs
    all_ids = set()
    with open('orchid_eol_page_ids.txt', 'r') as f:
        for line in f:
            page_id = line.strip()
            if page_id:
                all_ids.add(page_id)
    
    cur.close()
    conn.close()
    
    return sorted(list(all_ids - existing))

def fetch_taxonomy_from_tropicos(scientific_name):
    """Try to get taxonomy from Tropicos (Missouri Botanical Garden)"""
    try:
        # Tropicos search doesn't require API key for basic search
        url = f"http://legacy.tropicos.org/Name/Search?name={scientific_name}"
        # This is just a fallback - we'll focus on EOL
        return None
    except:
        return None

def fetch_taxonomy_eol_simple(page_id):
    """
    Fetch taxonomy using simple strategy:
    1. Get the page HTML
    2. Extract scientific name from meta tags or title
    3. Parse genus/species from scientific name
    """
    try:
        session = requests.Session()
        session.headers.update({'User-Agent': 'OrchidContinuum/1.0'})
        
        url = f"https://eol.org/pages/{page_id}"
        response = session.get(url, timeout=15, verify=False)
        
        if response.status_code != 200:
            return None
        
        html = response.text
        
        # Extract scientific name from various possible locations
        scientific_name = None
        
        # Try meta tag first
        if '<meta property="og:title" content="' in html:
            start = html.find('<meta property="og:title" content="') + 35
            end = html.find('"', start)
            scientific_name = html[start:end].strip()
        
        # Try page title
        if not scientific_name and '<title>' in html:
            start = html.find('<title>') + 7
            end = html.find('</title>', start)
            title = html[start:end].strip()
            # Remove " - Encyclopedia of Life" suffix
            scientific_name = title.replace(' - Encyclopedia of Life', '').strip()
        
        if not scientific_name:
            return None
        
        # Parse genus and species
        parts = scientific_name.split()
        if len(parts) < 1:
            return None
        
        genus = parts[0]
        species_part = ' '.join(parts[1:]) if len(parts) > 1 else ''
        
        return {
            'scientific_name': scientific_name,
            'genus': genus,
            'species': species_part,
            'family': 'Orchidaceae'  # Default for all orchids
        }
        
    except Exception as e:
        return None

def insert_taxonomy(page_id, taxonomy_data):
    """Insert taxonomy into database"""
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO orchid_taxonomy (
                eol_page_id, genus, species, family, scientific_name, created_at
            ) VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (eol_page_id) DO UPDATE 
            SET genus = EXCLUDED.genus,
                species = EXCLUDED.species,
                family = EXCLUDED.family,
                scientific_name = EXCLUDED.scientific_name
        """, (
            page_id,
            taxonomy_data['genus'],
            taxonomy_data['species'],
            taxonomy_data['family'],
            taxonomy_data['scientific_name']
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"   ⚠️  DB Error: {e}")
        return False

def run_worker(max_batches=None):
    """
    Run the background worker
    max_batches: if None, runs forever; otherwise runs N batches
    """
    print("🌺 BACKGROUND TAXONOMY WORKER")
    print("=" * 70)
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Request delay: {DELAY_BETWEEN_REQUESTS}s")
    print()
    
    # Load progress
    progress = load_progress()
    processed_ids = set(progress['processed'])
    failed_ids = set(progress['failed'])
    
    # Get missing IDs
    missing_ids = get_missing_eol_ids()
    remaining = [pid for pid in missing_ids if pid not in processed_ids]
    
    print(f"📊 Status:")
    print(f"   Total missing: {len(missing_ids):,}")
    print(f"   Already processed: {len(processed_ids):,}")
    print(f"   Failed previously: {len(failed_ids):,}")
    print(f"   Remaining: {len(remaining):,}")
    print()
    
    if not remaining:
        print("✅ All taxonomy data fetched!")
        return
    
    # Process in batches
    batch_num = 0
    total_fetched = 0
    total_failed = 0
    
    while remaining and (max_batches is None or batch_num < max_batches):
        batch_num += 1
        batch = remaining[:BATCH_SIZE]
        remaining = remaining[BATCH_SIZE:]
        
        print(f"📦 Batch {batch_num} ({len(batch)} species)")
        print("-" * 70)
        
        batch_success = 0
        batch_fail = 0
        
        for i, page_id in enumerate(batch, 1):
            # Fetch taxonomy
            taxonomy = fetch_taxonomy_eol_simple(page_id)
            
            if taxonomy:
                # Insert into database
                if insert_taxonomy(page_id, taxonomy):
                    processed_ids.add(page_id)
                    batch_success += 1
                    total_fetched += 1
                    print(f"   [{i:2}/{len(batch)}] EOL {page_id}: ✅ {taxonomy['scientific_name']}")
                else:
                    failed_ids.add(page_id)
                    batch_fail += 1
                    total_failed += 1
            else:
                failed_ids.add(page_id)
                batch_fail += 1
                total_failed += 1
                print(f"   [{i:2}/{len(batch)}] EOL {page_id}: ❌ Failed to fetch")
            
            # Rate limit
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        print(f"   Batch result: ✅ {batch_success} | ❌ {batch_fail}")
        print()
        
        # Save progress after each batch
        progress['processed'] = list(processed_ids)
        progress['failed'] = list(failed_ids)
        save_progress(progress)
        
        # Delay between batches
        if remaining:
            print(f"⏸️  Waiting {DELAY_BETWEEN_BATCHES}s before next batch...")
            time.sleep(DELAY_BETWEEN_BATCHES)
    
    print("=" * 70)
    print(f"✅ Session complete!")
    print(f"   Fetched: {total_fetched}")
    print(f"   Failed: {total_failed}")
    print(f"   Remaining: {len(remaining):,}")
    print()
    print(f"Progress saved to: {PROGRESS_FILE}")

if __name__ == "__main__":
    import sys
    
    # Get max batches from command line (default: 10 batches for testing)
    max_batches = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    print(f"Running {max_batches} batch(es)...\n")
    run_worker(max_batches=max_batches)
