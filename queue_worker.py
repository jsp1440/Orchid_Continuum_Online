l://neondb_owner:npg_feOt1Ek0KLrF@ep-snowy-forest-a5d1v3hd.us-east-2.aws.neon.tech/neondb?sslmode=require"

python3 queue_worker.py mac-1 > w1.log 2>&1 &
python3 queue_worker.py mac-2 > w2.log 2>&1 &

tail -f w1.log
[1] 71056
[2] 71057
  File "/Users/jefferyparham/orchid_downloads/queue_worker.py", line 26
    cur.execute("UPDATE harvest_jobs SET status='pending', 
                                                           ^
SyntaxError: EOL while scanning string literal
[2]  + exit 1     python3 queue_worker.py mac-2 > w2.log 2>&1
[1]  + exit 1     python3 queue_worker.py mac-1 > w1.log 2>&1
pkill -f queue_worker
rm queue_worker.py)

stats = {'leased': 0, 'completed': 0, 'images_added': 0, 'failed': 0, 'start': time.time()}

def get_connection():
    """Get connection from pool"""
    return conn_pool.getconn()

def release_connection(conn):
    """Return connection to pool"""
    conn_pool.putconn(conn)

def lease_jobs(count=BATCH_SIZE):
    """Lease jobs using SELECT FOR UPDATE SKIP LOCKED"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Reclaim stuck leases first
        cur.execute("""
            UPDATE harvest_jobs
            SET status = 'pending', lease_owner = NULL, leased_at = NULL
            WHERE status = 'leased' 
              AND leased_at < NOW() - INTERVAL '%s minutes'
        """, (LEASE_TIMEOUT_MINUTES,))
        
        # Lease new jobs (prioritizes by priority score)
        cur.execute("""
            UPDATE harvest_jobs
            SET status = 'leased', 
                lease_owner = %s, 
                leased_at = NOW(),
                updated_at = NOW()
            WHERE id IN (
                SELECT id FROM harvest_jobs
                WHERE status = 'pending'
                ORDER BY priority DESC, id ASC
                LIMIT %s
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id, taxonomy_id, scientific_name, current_image_count
        """, (WORKER_ID, count))
        
        jobs = cur.fetchall()
        conn.commit()
        return jobs
    finally:
        release_connection(conn)

def fetch_gbif(species_name, country_code=None):
    """Fetch images from GBIF"""
    params = {
        'scientificName': species_name,
        'mediaType': 'StillImage',
        'limit': 5,
        'hasCoordinate': 'true'
    }
    if country_code:
        params['country'] = country_code
    
    try:
        r = requests.get("https://api.gbif.org/v1/occurrence/search", 
                        params=params, timeout=12)
        if r.status_code != 200:
            return []
        
        images = []
        for rec in r.json().get('results', []):
            for m in rec.get('media', []):
                if m.get('type') == 'StillImage' and m.get('identifier'):
                    # Handle date parsing - skip invalid formats
                    obs_date = rec.get('eventDate')
                    if obs_date and ('/' in obs_date or len(obs_date) < 10):
                        obs_date = None
                    
                    images.append({
                        'url': m['identifier'],
                        'source': 'GBIF',
                        'license': rec.get('license'),
                        'type': 'observation',
                        'country': rec.get('country'),
                        'country_code': rec.get('countryCode'),
                        'latitude': rec.get('decimalLatitude'),
                        'longitude': rec.get('decimalLongitude'),
                        'observation_date': obs_date,
                        'year': rec.get('year'),
                        'gbif_key': str(rec.get('key', '')),
                    })
        return images
    except:
        return []

def save_image(img, tax_id):
    """Save image to database using pooled connection"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Check if exists
        cur.execute("SELECT 1 FROM orchid_images WHERE image_url = %s", (img['url'],))
        if cur.fetchone():
            return False
        
        # Insert
        cur.execute("""
            INSERT INTO orchid_images (
                taxonomy_id, image_url, image_source, image_license, image_type,
                country, country_code, latitude, longitude,
                observation_date, year_observed, gbif_occurrence_key,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
            )
        """, (
            tax_id, img['url'], img['source'], img.get('license'), img.get('type'),
            img.get('country'), img.get('country_code'),
            img.get('latitude'), img.get('longitude'),
            img.get('observation_date'), img.get('year'), img.get('gbif_key')
        ))
        
        conn.commit()
        return True
    except:
        conn.rollback()
        return False
    finally:
        release_connection(conn)

def process_job(job_data):
    """Process one job - fetch and save images"""
    job_id, tax_id, sci_name, current_count = job_data
    
    try:
        # Fetch images (global + priority regions)
        all_images = []
        all_images.extend(fetch_gbif(sci_name))
        
        for country in PRIORITY_COUNTRIES[:4]:  # Top 4 regions
            all_images.extend(fetch_gbif(sci_name, country))
            time.sleep(0.08)
        
        # Save images
        saved = 0
        for img in all_images[:25]:  # Max 25 per job
            if save_image(img, tax_id):
                stats['images_added'] += 1
                saved += 1
            time.sleep(0.03)
        
        # Mark job complete
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE harvest_jobs
                SET status = 'completed',
                    completed_at = NOW(),
                    current_image_count = current_image_count + %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (saved, job_id))
            conn.commit()
            stats['completed'] += 1
        finally:
            release_connection(conn)
        
        if saved > 0:
            elapsed_min = (time.time() - stats['start']) / 60
            rate = stats['images_added'] / elapsed_min if elapsed_min > 0 else 0
            print(f"[{WORKER_ID}] {sci_name[:45]}: +{saved} | Total: {stats['images_added']} | {rate:.1f}/min")
        
        return saved
        
    except Exception as e:
        # Mark job as failed
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE harvest_jobs
                SET status = 'failed',
                    last_error = %s,
                    attempts = attempts + 1,
                    updated_at = NOW()
                WHERE id = %s
            """, (str(e)[:200], job_id))
            conn.commit()
            stats['failed'] += 1
        finally:
            release_connection(conn)
        return 0

print(f"{'=' * 80}")
print(f"🌺 QUEUE WORKER: {WORKER_ID}")
print(f"{'=' * 80}")
print(f"Batch size: {BATCH_SIZE} | Threads: {THREAD_COUNT}")
print(f"Started: {datetime.now().strftime('%I:%M:%S %p')}\n")

cycle = 0
executor = ThreadPoolExecutor(max_workers=THREAD_COUNT)

while True:
    cycle += 1
    
    # Lease batch of jobs
    jobs = lease_jobs(BATCH_SIZE)
    
    if not jobs:
        print(f"[{WORKER_ID}] No pending jobs. Sleeping 30 seconds...")
        time.sleep(30)
        continue
    
    stats['leased'] += len(jobs)
    print(f"[{WORKER_ID}] Cycle {cycle}: Processing {len(jobs)} jobs...")
    
    # Process jobs in parallel (limited threads)
    futures = [executor.submit(process_job, job) for job in jobs]
    results = [f.result() for f in futures]
    
    elapsed = (time.time() - stats['start']) / 60
    rate = stats['images_added'] / elapsed if elapsed > 0 else 0
    
    print(f"[{WORKER_ID}] Cycle {cycle} done: {sum(results)} images | Overall: {stats['images_added']} total, {rate:.1f}/min\n")
    
    time.sleep(2)
