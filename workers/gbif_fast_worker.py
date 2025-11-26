#!/usr/bin/env python3
"""GBIF Fast Worker - Optimized for speed"""
import os, sys, time, requests, psycopg2, json
from psycopg2 import pool

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "gbif-fast-1"
BATCH_SIZE = 2
RECLAIM_MINUTES = 3  # Reclaim faster

GBIF_COUNTRIES = ['AU', 'BR', 'CO', 'EC', 'ID', 'MY', 'PH', 'MG', 'CR', 'PA', 'PE', 'TH', 'VN', 'KE', 'IN', 'ZA']

pool_obj = pool.SimpleConnectionPool(minconn=1, maxconn=3, dsn=os.environ.get('DATABASE_URL'))

def get_conn():
    return pool_obj.getconn()

def put_conn(c):
    pool_obj.putconn(c)

def harvest_gbif(genus, species, country, taxonomy_id):
    """Quick GBIF harvest"""
    time.sleep(0.2)
    params = {
        'scientificName': f"{genus} {species}",
        'mediaType': 'StillImage',
        'limit': 100,
        'hasCoordinate': 'true',
        'country': country
    }
    
    try:
        resp = requests.get("https://api.gbif.org/v1/occurrence/search", params=params, timeout=10)
        if resp.status_code != 200:
            return 0
        
        added = 0
        for record in resp.json().get('results', []):
            for media in record.get('media', []):
                if media.get('type') != 'StillImage':
                    continue
                
                url = media.get('identifier')
                if not url:
                    continue
                
                conn = get_conn()
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM orchid_images WHERE image_url = %s", (url,))
                    if cur.fetchone():
                        cur.close()
                        put_conn(conn)
                        continue
                    
                    cur.execute("""
                        INSERT INTO orchid_images (
                            taxonomy_id, image_url, image_source, country, 
                            latitude, longitude, observer_name, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        taxonomy_id, url, 'GBIF',
                        record.get('country'),
                        record.get('decimalLatitude'),
                        record.get('decimalLongitude'),
                        record.get('recordedBy')
                    ))
                    conn.commit()
                    added += 1
                    cur.close()
                finally:
                    put_conn(conn)
        
        return added
    except:
        return 0

def main():
    print(f"[{WORKER_ID}] Fast GBIF Worker started")
    
    while True:
        conn = get_conn()
        try:
            cur = conn.cursor()
            
            # Get job
            cur.execute("""
                UPDATE harvest_jobs SET status='leased', lease_owner=%s, leased_at=NOW()
                WHERE id IN (
                    SELECT id FROM harvest_jobs WHERE status='pending' 
                    ORDER BY priority DESC LIMIT 1 FOR UPDATE SKIP LOCKED
                )
                RETURNING id, taxonomy_id, scientific_name
            """, (WORKER_ID,))
            
            job = cur.fetchone()
            if not job:
                cur.close()
                put_conn(conn)
                time.sleep(15)
                continue
            
            job_id, taxonomy_id, sci_name = job
            conn.commit()
            cur.close()
            put_conn(conn)
            
            # Process job
            parts = sci_name.split()
            genus, species = parts[0], (parts[1] if len(parts) > 1 else '')
            
            added = 0
            for country in GBIF_COUNTRIES:
                added += harvest_gbif(genus, species, country, taxonomy_id)
            
            # Mark complete
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("UPDATE harvest_jobs SET status='complete' WHERE id=%s", (job_id,))
            conn.commit()
            cur.close()
            put_conn(conn)
            
            if added > 0:
                print(f"[{WORKER_ID}] +{added} images")
        except Exception as e:
            put_conn(conn)
            time.sleep(5)

if __name__ == "__main__":
    main()
