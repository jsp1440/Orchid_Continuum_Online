#!/usr/bin/env python3
"""
GBIF-ONLY WORKER - Global Biodiversity Information Facility
============================================================
Dedicated worker for GBIF API with careful rate limiting
Run 8 workers: python workers/gbif_worker.py gbif-1 ... gbif-8
"""
import os, sys, time, requests, psycopg2, json
from psycopg2 import pool
from datetime import datetime

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "gbif-1"
BATCH_SIZE = 5
RECLAIM_MINUTES = 7
REQUEST_DELAY = 0.5  # 500ms between requests to avoid rate limiting

pool_obj = pool.SimpleConnectionPool(minconn=1, maxconn=5, dsn=os.environ.get('DATABASE_URL'))
stats = {'added': 0, 'start': time.time(), 'errors': 0}

# Target orchid-rich countries
GBIF_COUNTRIES = ['AU', 'BR', 'CO', 'EC', 'ID', 'MY', 'PH', 'MG', 'CR', 'PA', 'PE', 'TH']

def get_conn():
    return pool_obj.getconn()

def put_conn(c):
    pool_obj.putconn(c)

def lease(n=BATCH_SIZE):
    """Lease jobs from queue"""
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

def fetch_gbif(name, country=None):
    """Fetch from GBIF API with rate limiting"""
    time.sleep(REQUEST_DELAY)  # Critical: prevent rate limiting
    
    p = {'scientificName': name, 'mediaType': 'StillImage', 'limit': 10, 'hasCoordinate': 'true'}
    if country:
        p['country'] = country
    
    try:
        resp = requests.get("https://api.gbif.org/v1/occurrence/search", params=p, timeout=15)
        
        # Handle rate limiting
        if resp.status_code == 429:
            print(f"[{WORKER_ID}] Rate limited! Waiting 60s...")
            time.sleep(60)
            return []
        
        if resp.status_code != 200:
            return []
        
        imgs = []
        for rec in resp.json().get('results', []):
            for m in rec.get('media', []):
                if m.get('type') == 'StillImage' and m.get('identifier'):
                    date = rec.get('eventDate')
                    if date and ('/' in date or len(date) < 10):
                        date = None
                    
                    imgs.append({
                        'url': m['identifier'],
                        'source': 'GBIF',
                        'type': 'observation',
                        'country': rec.get('country'),
                        'lat': rec.get('decimalLatitude'),
                        'lon': rec.get('decimalLongitude'),
                        'date': date,
                        'year': rec.get('year'),
                        'occurrence_metadata': {
                            'gbif_key': str(rec.get('key', '')),
                            'basis_of_record': rec.get('basisOfRecord'),
                            'recorded_by': rec.get('recordedBy'),
                            'institution': rec.get('institutionCode')
                        }
                    })
        
        return imgs
    except Exception as e:
        stats['errors'] += 1
        return []

def save(img_data, tid):
    """Save image to database"""
    c = get_conn()
    try:
        r = c.cursor()
        
        occurrence_meta = json.dumps(img_data.get('occurrence_metadata')) if img_data.get('occurrence_metadata') else None
        gbif_key = img_data.get('occurrence_metadata', {}).get('gbif_key') if img_data.get('occurrence_metadata') else None
        
        sql = """
        INSERT INTO orchid_images (
            taxonomy_id, image_url, image_source, image_type,
            country, latitude, longitude, observation_date, year_observed,
            gbif_occurrence_key, occurrence_metadata, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        ON CONFLICT (image_url) DO NOTHING
        RETURNING id
        """
        
        r.execute(sql, (
            tid, img_data['url'], img_data['source'], img_data['type'],
            img_data.get('country'), img_data.get('lat'), img_data.get('lon'),
            img_data.get('date'), img_data.get('year'), gbif_key, occurrence_meta
        ))
        
        result = r.fetchone()
        c.commit()
        return result is not None
    except Exception as e:
        c.rollback()
        stats['errors'] += 1
        return False
    finally:
        put_conn(c)

def work(job):
    """Process one job - GBIF only"""
    jid, tid, name = job
    try:
        all_imgs = []
        
        # Fetch global GBIF images
        all_imgs.extend(fetch_gbif(name))
        
        # Fetch from top 4 orchid countries
        for country in GBIF_COUNTRIES[:4]:
            all_imgs.extend(fetch_gbif(name, country))
        
        # Save images (max 30 per species)
        saved = 0
        for img in all_imgs[:30]:
            if save(img, tid):
                saved += 1
        
        stats['added'] += saved
        
        # Mark job complete
        c = get_conn()
        try:
            r = c.cursor()
            r.execute("UPDATE harvest_jobs SET status='completed', completed_at=NOW() WHERE id=%s", (jid,))
            c.commit()
            print(f"[{WORKER_ID}] Job #{jid} completed: {name[:40]} → {saved} images")
        finally:
            put_conn(c)
        
        if saved > 0:
            rate = stats['added'] / ((time.time() - stats['start']) / 60)
            print(f"[{WORKER_ID}] {name[:40]}: +{saved} GBIF | Total: {stats['added']} | {rate:.1f}/min | Errors: {stats['errors']}")
        
        return saved
        
    except Exception as e:
        error_msg = str(e)[:200]
        print(f"[{WORKER_ID}] ERROR on job #{jid} ({name}): {error_msg}")
        
        c = get_conn()
        try:
            r = c.cursor()
            r.execute("UPDATE harvest_jobs SET status='failed', last_error=%s WHERE id=%s", (error_msg, jid))
            c.commit()
        except Exception as db_error:
            print(f"[{WORKER_ID}] CRITICAL: Failed to mark job as failed: {db_error}")
        finally:
            put_conn(c)
        
        stats['errors'] += 1
        return 0

# Main loop
print(f"🌍 GBIF WORKER: {WORKER_ID} (delay={REQUEST_DELAY}s)")

while True:
    jobs = lease()
    if not jobs:
        time.sleep(5)
        continue
    
    for job in jobs:
        work(job)
