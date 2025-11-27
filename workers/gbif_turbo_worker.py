#!/usr/bin/env python3
"""
GBIF TURBO WORKER - High-Performance Optimized Harvester
=========================================================
Optimizations:
1. Batch database inserts (50 records at once)
2. Async-style parallel fetching
3. Connection pooling with larger pool
4. Reduced delays with smart rate limiting
5. Larger result pages from API
6. In-memory deduplication cache
"""
import os, sys, time, requests, psycopg2, hashlib, threading
from psycopg2 import pool, extras
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "turbo-1"

# Larger connection pool
pool_obj = None
stats = {'added': 0, 'fetched': 0, 'start': time.time(), 'batches': 0}

# In-memory cache of recently seen URLs to avoid DB lookups
seen_urls = set()
seen_lock = threading.Lock()
MAX_CACHE_SIZE = 50000

# Batch insert buffer
insert_buffer = []
buffer_lock = threading.Lock()
BATCH_SIZE = 50

def init_pool():
    global pool_obj
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print(f"[{WORKER_ID}] ERROR: No DATABASE_URL")
        sys.exit(1)
    pool_obj = pool.ThreadedConnectionPool(minconn=2, maxconn=10, dsn=db_url)
    return True

def get_conn():
    return pool_obj.getconn()

def put_conn(c):
    if pool_obj and c:
        pool_obj.putconn(c)

def get_pending_jobs(limit=20):
    """Get multiple jobs at once for parallel processing"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE harvester_jobs 
            SET status = 'processing', 
                started_at = NOW(),
                worker_id = %s
            WHERE id IN (
                SELECT id FROM harvester_jobs 
                WHERE status = 'pending' 
                   OR (status = 'processing' AND started_at < NOW() - INTERVAL '5 minutes')
                ORDER BY priority DESC, id
                LIMIT %s
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id, species_name, genus
        """, (WORKER_ID, limit))
        jobs = cur.fetchall()
        conn.commit()
        return jobs
    except Exception as e:
        conn.rollback()
        return []
    finally:
        cur.close()
        put_conn(conn)

def fetch_gbif_page(name, offset=0, limit=100):
    """Fetch a single page from GBIF API"""
    params = {
        'scientificName': name,
        'mediaType': 'StillImage',
        'limit': limit,
        'offset': offset,
        'hasCoordinate': 'true'
    }
    
    try:
        resp = requests.get(
            "https://api.gbif.org/v1/occurrence/search",
            params=params,
            timeout=20
        )
        
        if resp.status_code == 429:
            time.sleep(30)
            return None
        
        if resp.status_code != 200:
            return None
            
        return resp.json()
    except:
        return None

def extract_images(data, species_name):
    """Extract image records from GBIF response"""
    images = []
    
    for result in data.get('results', []):
        media_list = result.get('media', [])
        
        for media in media_list:
            if media.get('type') != 'StillImage':
                continue
                
            url = media.get('identifier', '')
            if not url or len(url) < 10:
                continue
            
            # Skip if in cache
            with seen_lock:
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                # Limit cache size
                if len(seen_urls) > MAX_CACHE_SIZE:
                    seen_urls.clear()
            
            images.append({
                'url': url,
                'species': result.get('species', species_name),
                'genus': result.get('genus', ''),
                'country': result.get('country', ''),
                'lat': result.get('decimalLatitude'),
                'lon': result.get('decimalLongitude'),
                'observer': result.get('recordedBy', ''),
                'license': media.get('license', ''),
                'gbif_key': str(result.get('key', ''))
            })
    
    return images

def flush_buffer():
    """Insert buffered records to database in one batch"""
    global insert_buffer
    
    with buffer_lock:
        if not insert_buffer:
            return 0
        batch = insert_buffer.copy()
        insert_buffer = []
    
    if not batch:
        return 0
    
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Batch insert with ON CONFLICT
        values = []
        for img in batch:
            # Get taxonomy_id
            cur.execute(
                "SELECT id FROM orchid_taxonomy WHERE genus = %s AND (species = %s OR species IS NULL) LIMIT 1",
                (img['genus'], img['species'])
            )
            result = cur.fetchone()
            taxonomy_id = result[0] if result else None
            
            if taxonomy_id:
                values.append((
                    taxonomy_id,
                    img['url'],
                    'GBIF',
                    img['country'] or None,
                    img['lat'],
                    img['lon'],
                    img['observer'] or None,
                    img['license'] or None,
                    img['gbif_key'] or None
                ))
        
        if values:
            extras.execute_batch(cur, """
                INSERT INTO orchid_images 
                (taxonomy_id, image_url, image_source, country, latitude, longitude, observer_name, image_license, gbif_occurrence_key)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (image_url) DO NOTHING
            """, values)
            
            conn.commit()
            stats['added'] += cur.rowcount
            stats['batches'] += 1
            return cur.rowcount
        
        return 0
    except Exception as e:
        conn.rollback()
        return 0
    finally:
        cur.close()
        put_conn(conn)

def process_species(job_id, species_name, genus):
    """Process a single species - fetch and queue images"""
    total_images = 0
    
    # Fetch first page
    data = fetch_gbif_page(species_name, offset=0, limit=100)
    if not data:
        return 0
    
    images = extract_images(data, species_name)
    
    with buffer_lock:
        insert_buffer.extend(images)
    
    total_images += len(images)
    stats['fetched'] += len(images)
    
    # Fetch more pages if available (up to 500 images per species)
    total_available = data.get('count', 0)
    if total_available > 100:
        for offset in range(100, min(total_available, 500), 100):
            time.sleep(0.1)  # Small delay between pages
            data = fetch_gbif_page(species_name, offset=offset, limit=100)
            if data:
                images = extract_images(data, species_name)
                with buffer_lock:
                    insert_buffer.extend(images)
                total_images += len(images)
                stats['fetched'] += len(images)
    
    # Mark job complete
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE harvester_jobs SET status = 'completed', completed_at = NOW() WHERE id = %s",
            (job_id,)
        )
        conn.commit()
    except:
        conn.rollback()
    finally:
        cur.close()
        put_conn(conn)
    
    return total_images

def main():
    print(f"[{WORKER_ID}] TURBO WORKER starting...")
    init_pool()
    
    # Flush buffer periodically in background
    def buffer_flusher():
        while True:
            time.sleep(5)
            if len(insert_buffer) >= BATCH_SIZE // 2:
                flush_buffer()
    
    flush_thread = threading.Thread(target=buffer_flusher, daemon=True)
    flush_thread.start()
    
    while True:
        try:
            # Get batch of jobs
            jobs = get_pending_jobs(limit=10)
            
            if not jobs:
                print(f"[{WORKER_ID}] No jobs, waiting...")
                flush_buffer()  # Flush remaining
                time.sleep(30)
                continue
            
            # Process jobs in parallel using thread pool
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(process_species, job[0], job[1], job[2]): job
                    for job in jobs
                }
                
                for future in as_completed(futures):
                    job = futures[future]
                    try:
                        count = future.result()
                    except Exception as e:
                        pass
            
            # Flush buffer after each batch
            flush_buffer()
            
            # Stats
            elapsed = time.time() - stats['start']
            rate = stats['added'] / (elapsed / 3600) if elapsed > 0 else 0
            print(f"[{WORKER_ID}] Added: {stats['added']:,} | Rate: {rate:,.0f}/hr | Batches: {stats['batches']}")
            
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            print(f"[{WORKER_ID}] Shutting down...")
            flush_buffer()
            break
        except Exception as e:
            print(f"[{WORKER_ID}] Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
