# 🤖 JULIUS - START HARVESTING IMMEDIATELY

## Database Connection
```
DATABASE_URL="postgresql://neondb_owner:npg_feOt1Ek0KLrF@ep-snowy-firefly-afvebui7.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require"
```

## Complete Worker Code (Copy & Run)

Save this as `julius_worker.py` and run it:

```python
#!/usr/bin/env python3
import os, sys, time, requests, psycopg2
from psycopg2 import pool
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "julius-1"
BATCH_SIZE = 5
THREAD_COUNT = 2
COUNTRIES = ['AU', 'PG', 'ID', 'MY', 'PH', 'TH', 'VN', 'CR', 'PA']
pool_obj = pool.SimpleConnectionPool(minconn=1, maxconn=5, dsn=os.environ.get('DATABASE_URL'))
stats = {'added': 0, 'start': time.time()}

def get_conn():
    return pool_obj.getconn()

def put_conn(c):
    pool_obj.putconn(c)

def lease(n=BATCH_SIZE):
    c = get_conn()
    try:
        r = c.cursor()
        r.execute("UPDATE harvest_jobs SET status='pending', lease_owner=NULL WHERE status='leased' AND leased_at < NOW() - INTERVAL '10 minutes'")
        sql = "UPDATE harvest_jobs SET status='leased', lease_owner=%s, leased_at=NOW() WHERE id IN (SELECT id FROM harvest_jobs WHERE status='pending' ORDER BY priority DESC LIMIT %s FOR UPDATE SKIP LOCKED) RETURNING id, taxonomy_id, scientific_name"
        r.execute(sql, (WORKER_ID, n))
        jobs = r.fetchall()
        c.commit()
        return jobs
    finally:
        put_conn(c)

def fetch(name, country=None):
    p = {'scientificName': name, 'mediaType': 'StillImage', 'limit': 5, 'hasCoordinate': 'true'}
    if country:
        p['country'] = country
    try:
        resp = requests.get("https://api.gbif.org/v1/occurrence/search", params=p, timeout=12)
        if resp.status_code != 200:
            return []
        imgs = []
        for rec in resp.json().get('results', []):
            for m in rec.get('media', []):
                if m.get('type') == 'StillImage' and m.get('identifier'):
                    date = rec.get('eventDate')
                    if date and ('/' in date or len(date) < 10):
                        date = None
                    imgs.append({'url': m['identifier'], 'country': rec.get('country'), 'lat': rec.get('decimalLatitude'), 'lon': rec.get('decimalLongitude'), 'date': date, 'year': rec.get('year'), 'key': str(rec.get('key', ''))})
        return imgs
    except:
        return []

def save(img, tid):
    c = get_conn()
    try:
        r = c.cursor()
        r.execute("SELECT 1 FROM orchid_images WHERE image_url=%s", (img['url'],))
        if r.fetchone():
            return False
        sql = "INSERT INTO orchid_images (taxonomy_id, image_url, image_source, image_type, country, latitude, longitude, observation_date, year_observed, gbif_occurrence_key, created_at, updated_at) VALUES (%s, %s, 'GBIF', 'observation', %s, %s, %s, %s, %s, %s, NOW(), NOW())"
        r.execute(sql, (tid, img['url'], img.get('country'), img.get('lat'), img.get('lon'), img.get('date'), img.get('year'), img.get('key')))
        c.commit()
        return True
    except:
        c.rollback()
        return False
    finally:
        put_conn(c)

def work(job):
    jid, tid, name = job
    try:
        imgs = fetch(name)
        for ctry in COUNTRIES[:4]:
            imgs.extend(fetch(name, ctry))
            time.sleep(0.08)
        saved = sum(1 for i in imgs[:25] if save(i, tid))
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
            print(f"[{WORKER_ID}] {name[:45]}: +{saved} | Total: {stats['added']} | {rate:.1f}/min")
        return saved
    except Exception as e:
        c = get_conn()
        try:
            r = c.cursor()
            r.execute("UPDATE harvest_jobs SET status='failed', last_error=%s WHERE id=%s", (str(e)[:200], jid))
            c.commit()
        finally:
            put_conn(c)
        return 0

print(f"🌺 WORKER: {WORKER_ID} | Started: {datetime.now().strftime('%I:%M:%S %p')}")
ex = ThreadPoolExecutor(max_workers=THREAD_COUNT)
cycle = 0
while True:
    cycle += 1
    jobs = lease(BATCH_SIZE)
    if not jobs:
        print(f"[{WORKER_ID}] No jobs, sleeping...")
        time.sleep(30)
        continue
    print(f"[{WORKER_ID}] Cycle {cycle}: Processing {len(jobs)} jobs...")
    results = [ex.submit(work, j).result() for j in jobs]
    print(f"[{WORKER_ID}] Cycle {cycle} done: {sum(results)} images\n")
    time.sleep(2)
```

## How to Run

```bash
# Install dependencies
pip install psycopg2-binary requests

# Set database connection
export DATABASE_URL="postgresql://neondb_owner:npg_feOt1Ek0KLrF@ep-snowy-firefly-afvebui7.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require"

# Run 4 workers
python3 julius_worker.py julius-1 > j1.log 2>&1 &
python3 julius_worker.py julius-2 > j2.log 2>&1 &
python3 julius_worker.py julius-3 > j3.log 2>&1 &
python3 julius_worker.py julius-4 > j4.log 2>&1 &

# Monitor
tail -f j1.log
```

## Expected Output
```
🌺 WORKER: julius-1 | Started: 01:05:30 AM
[julius-1] Cycle 1: Processing 5 jobs...
[julius-1] Apostasia latifolia: +2 | Total: 2 | 15.3/min
[julius-1] Cycle 1 done: 2 images
```

## Performance Target
- Per worker: 10-30 images/min
- 4 workers: 40-120 images/min
- Overnight: 19,200-57,600 images

## Current Status
- Queue: 34,213 species need images
- Goal: 30+ images per species
- Total target: ~1,000,000 images

## The System
Queue-based job leasing prevents conflicts. Each worker gets unique species automatically. No coordination needed between workers.
