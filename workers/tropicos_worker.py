#!/usr/bin/env python3
"""
TROPICOS-ONLY WORKER - Missouri Botanical Garden
=================================================
Dedicated worker for Tropicos API (REQUIRES API KEY)
Run 2 workers: python workers/tropicos_worker.py tropicos-1 ... tropicos-2
"""
import os, sys, time, requests, psycopg2, json
from psycopg2 import pool

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "tropicos-1"
BATCH_SIZE = 6
RECLAIM_MINUTES = 7
REQUEST_DELAY = 0.6
TROPICOS_API_KEY = os.environ.get('TROPICOS_API_KEY', '')

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

def simplify_name(full_name):
    """Extract binomial name (Genus species) handling hybrids, subspecies, and authors"""
    parts = full_name.split()
    if len(parts) < 2:
        return full_name
    
    genus = parts[0]
    
    # Handle hybrid marker
    if parts[1] == 'x' and len(parts) >= 3:
        return f"{genus} {parts[2]}"
    
    # Handle subspecies/variety markers
    if len(parts) >= 3 and parts[2] in ('ssp.', 'subsp.', 'var.', 'f.', 'forma'):
        return f"{genus} {parts[1]}"
    
    # Normal case - just genus and species
    return f"{genus} {parts[1]}"

def fetch_tropicos(name):
    """Fetch from Tropicos"""
    if not TROPICOS_API_KEY:
        return []
    
    time.sleep(REQUEST_DELAY)
    
    # Strip author names - Tropicos prefers binomial (Genus species)
    simple_name = simplify_name(name)
    
    try:
        search_url = "http://services.tropicos.org/Name/Search"
        params = {'apikey': TROPICOS_API_KEY, 'name': simple_name, 'type': 'wildcard', 'format': 'json'}
        resp = requests.get(search_url, params=params, timeout=15)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        if not isinstance(data, list) or len(data) == 0:
            return []
        
        name_id = data[0].get('NameId')
        if not name_id:
            return []
        
        images_url = f"http://services.tropicos.org/Name/{name_id}/Images"
        params = {'apikey': TROPICOS_API_KEY, 'format': 'json', 'pagesize': 10}
        resp = requests.get(images_url, params=params, timeout=15)
        if resp.status_code != 200:
            return []
        
        images_data = resp.json()
        imgs = []
        
        if isinstance(images_data, list):
            for img in images_data:
                # Use DetailJpgUrl for full resolution or ThumbnailUrl as fallback
                url = img.get('DetailJpgUrl') or img.get('ThumbnailUrl', '')
                if url:
                    imgs.append({
                        'url': url,
                        'source': 'Tropicos - Missouri Botanical Garden',
                        'type': 'herbarium',
                        'tropicos_metadata': {
                            'name_id': str(name_id),
                            'image_id': str(img.get('ImageId', '')),
                            'specimen_id': str(img.get('SpecimenId', '')),
                            'detail_url': img.get('DetailUrl'),
                            'license': img.get('LicenseName', ''),
                            'copyright': img.get('Copyright', ''),
                            'photographer': img.get('Photographer', '')
                        }
                    })
        
        return imgs
    except Exception as e:
        stats['errors'] += 1
        return []

def save(img_data, tid):
    c = get_conn()
    try:
        r = c.cursor()
        
        tropicos_meta = json.dumps(img_data.get('tropicos_metadata')) if img_data.get('tropicos_metadata') else None
        
        sql = """
        INSERT INTO orchid_images (
            taxonomy_id, image_url, image_source, image_type,
            tropicos_metadata, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, NOW(), NOW()
        )
        ON CONFLICT (image_url) DO NOTHING
        RETURNING id
        """
        
        r.execute(sql, (
            tid, img_data['url'], img_data['source'], img_data['type'],
            tropicos_meta
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
        imgs = fetch_tropicos(name)
        
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
            print(f"[{WORKER_ID}] {name[:40]}: +{saved} Tropicos | Total: {stats['added']} | {rate:.1f}/min")
        
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

if not TROPICOS_API_KEY:
    print(f"⚠️ TROPICOS_API_KEY not set! Worker will not start.")
    sys.exit(1)

print(f"🌿 TROPICOS WORKER: {WORKER_ID}")

while True:
    jobs = lease()
    if not jobs:
        time.sleep(5)
        continue
    
    for job in jobs:
        work(job)
