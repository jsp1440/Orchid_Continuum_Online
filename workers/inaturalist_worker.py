#!/usr/bin/env python3
"""
INATURALIST-ONLY WORKER - Community Observations
=================================================
Dedicated worker for iNaturalist API (NO API KEY NEEDED)
Run 3 workers: python workers/inaturalist_worker.py inat-1 ... inat-3
"""
import os, sys, time, requests, psycopg2, json
from psycopg2 import pool

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "inat-1"
BATCH_SIZE = 8
RECLAIM_MINUTES = 7
REQUEST_DELAY = 0.3

pool_obj = pool.SimpleConnectionPool(minconn=1, maxconn=5, dsn=os.environ.get('DATABASE_URL'))
stats = {'added': 0, 'start': time.time(), 'errors': 0}

def get_conn():
    return pool_obj.getconn()

def put_conn(c):
    pool_obj.putconn(c)

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

def fetch_inaturalist(name):
    """Fetch from iNaturalist"""
    time.sleep(REQUEST_DELAY)
    
    # Strip author names - iNaturalist only wants binomial (Genus species)
    name_parts = name.split()
    if len(name_parts) >= 2:
        simple_name = f"{name_parts[0]} {name_parts[1]}"
    else:
        simple_name = name
    
    try:
        search_url = "https://api.inaturalist.org/v1/observations"
        params = {
            'taxon_name': simple_name,
            'quality_grade': 'research',
            'photos': 'true',
            'per_page': 30
        }
        
        resp = requests.get(search_url, params=params, timeout=15)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        imgs = []
        
        for obs in data.get('results', []):
            photos = obs.get('photos', [])
            if not photos:
                continue
            
            photo = photos[0]
            img_url = photo.get('url')
            
            if img_url:
                img_url = img_url.replace('square', 'large')
            
            if img_url:
                imgs.append({
                    'url': img_url,
                    'source': 'iNaturalist',
                    'type': 'observation',
                    'country': obs.get('place_guess', '').split(',')[-1].strip() if obs.get('place_guess') else None,
                    'lat': obs.get('location') and float(obs['location'].split(',')[0]),
                    'lon': obs.get('location') and float(obs['location'].split(',')[1]) if obs.get('location') and ',' in obs['location'] else None,
                    'date': obs.get('observed_on'),
                    'year': obs.get('observed_on_details', {}).get('year'),
                    'occurrence_metadata': {
                        'inaturalist_id': str(obs.get('id', '')),
                        'quality_grade': obs.get('quality_grade'),
                        'observer': obs.get('user', {}).get('login'),
                        'num_identification_agreements': obs.get('num_identification_agreements', 0)
                    }
                })
        
        return imgs[:20]
    except Exception as e:
        stats['errors'] += 1
        return []

def save(img_data, tid):
    c = get_conn()
    try:
        r = c.cursor()
        
        occurrence_meta = json.dumps(img_data.get('occurrence_metadata')) if img_data.get('occurrence_metadata') else None
        
        sql = """
        INSERT INTO orchid_images (
            taxonomy_id, image_url, image_source, image_type,
            country, latitude, longitude, observation_date, year_observed,
            occurrence_metadata, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        ON CONFLICT (image_url) DO NOTHING
        RETURNING id
        """
        
        r.execute(sql, (
            tid, img_data['url'], img_data['source'], img_data['type'],
            img_data.get('country'), img_data.get('lat'), img_data.get('lon'),
            img_data.get('date'), img_data.get('year'), occurrence_meta
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
    jid, tid, name = job
    try:
        imgs = fetch_inaturalist(name)
        
        saved = 0
        for img in imgs:
            if save(img, tid):
                saved += 1
        
        stats['added'] += saved
        
        c = get_conn()
        try:
            r = c.cursor()
            r.execute("UPDATE harvest_jobs SET status='completed', completed_at=NOW() WHERE id=%s", (jid,))
            c.commit()
        finally:
            put_conn(c)
        
        if saved > 0:
            rate = stats['added'] / ((time.time() - stats['start']) / 60)
            print(f"[{WORKER_ID}] {name[:40]}: +{saved} iNat | Total: {stats['added']} | {rate:.1f}/min")
        
        return saved
        
    except Exception as e:
        c = get_conn()
        try:
            r = c.cursor()
            r.execute("UPDATE harvest_jobs SET status='failed', last_error=%s WHERE id=%s", (str(e)[:200], jid))
            c.commit()
        finally:
            put_conn(c)
        stats['errors'] += 1
        return 0

print(f"🦋 INATURALIST WORKER: {WORKER_ID}")

while True:
    jobs = lease()
    if not jobs:
        time.sleep(5)
        continue
    
    for job in jobs:
        work(job)
