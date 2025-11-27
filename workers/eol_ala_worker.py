#!/usr/bin/env python3
"""
EOL+ALA COMBO WORKER - Encyclopedia of Life + Atlas of Living Australia
========================================================================
Dedicated worker for EOL and ALA APIs (NO API KEY NEEDED)
Uses O(1) taxonomy lookup via taxonomy_mapper
Run 1 worker: python workers/eol_ala_worker.py eol-ala-1
"""
import os
import sys
import time
import requests
import psycopg2
import json
from psycopg2 import pool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taxonomy_mapper import lookup_taxon, lookup_taxon_by_id

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "eol-ala-1"
BATCH_SIZE = 6
RECLAIM_MINUTES = 7
REQUEST_DELAY = 0.5

pool_obj = pool.SimpleConnectionPool(minconn=1, maxconn=5, dsn=os.environ.get('DATABASE_URL'))
stats = {'added': 0, 'start': time.time(), 'by_source': {}, 'errors': 0}


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
    parts = full_name.split()
    if len(parts) < 2:
        return full_name
    
    genus = parts[0]
    
    if parts[1] == 'x' and len(parts) >= 3:
        return f"{genus} {parts[2]}"
    
    if len(parts) >= 3 and parts[2] in ('ssp.', 'subsp.', 'var.', 'f.', 'forma'):
        return f"{genus} {parts[1]}"
    
    return f"{genus} {parts[1]}"


def fetch_eol(name):
    return []


def fetch_ala(name):
    time.sleep(REQUEST_DELAY)
    
    simple_name = simplify_name(name)
    
    try:
        search_url = "https://biocache.ala.org.au/ws/occurrences/search"
        params = {
            'q': f'scientificName:"{simple_name}"',
            'fq': 'multimedia:Image',
            'pageSize': 15
        }
        
        resp = requests.get(search_url, params=params, timeout=15)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        imgs = []
        
        for occ in data.get('occurrences', []):
            img_url = occ.get('image')
            if not img_url:
                images = occ.get('images', [])
                if images and len(images) > 0:
                    img_url = images[0]
            
            if img_url:
                if not img_url.startswith('http'):
                    img_url = f"https://images.ala.org.au/image/details?imageId={img_url}"
                
                imgs.append({
                    'url': img_url,
                    'source': 'ALA',
                    'type': 'observation',
                    'country': 'AU',
                    'lat': occ.get('decimalLatitude'),
                    'lon': occ.get('decimalLongitude'),
                    'year': occ.get('year'),
                    'occurrence_metadata': {
                        'ala_uuid': occ.get('uuid', ''),
                        'basis_of_record': occ.get('basisOfRecord'),
                        'collector': occ.get('recordedBy'),
                        'state': occ.get('stateProvince')
                    }
                })
        
        return imgs
    except Exception:
        stats['errors'] += 1
        return []


def save(img_data, tid):
    c = get_conn()
    try:
        r = c.cursor()
        
        eol_meta = json.dumps(img_data.get('eol_metadata')) if img_data.get('eol_metadata') else None
        occurrence_meta = json.dumps(img_data.get('occurrence_metadata')) if img_data.get('occurrence_metadata') else None
        
        sql = """
        INSERT INTO orchid_images (
            taxonomy_id, image_url, image_source, image_type,
            country, latitude, longitude, year_observed,
            occurrence_metadata, eol_metadata, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        ON CONFLICT (image_url) DO NOTHING
        RETURNING id
        """
        
        r.execute(sql, (
            tid, img_data['url'], img_data['source'], img_data['type'],
            img_data.get('country'), img_data.get('lat'), img_data.get('lon'),
            img_data.get('year'), occurrence_meta, eol_meta
        ))
        
        result = r.fetchone()
        c.commit()
        return result is not None
    except Exception:
        c.rollback()
        stats['errors'] += 1
        return False
    finally:
        put_conn(c)


def work(job):
    jid, tid, name = job
    try:
        taxon = lookup_taxon_by_id(tid)
        if not taxon.get('matched'):
            print(f"[{WORKER_ID}] Invalid taxonomy_id {tid}, skipping")
            c = get_conn()
            try:
                r = c.cursor()
                r.execute("UPDATE harvest_jobs SET status='failed', last_error='Invalid taxonomy_id' WHERE id=%s", (jid,))
                c.commit()
            finally:
                put_conn(c)
            return 0
        
        all_imgs = []
        
        all_imgs.extend(fetch_eol(name))
        all_imgs.extend(fetch_ala(name))
        
        saved = 0
        for img in all_imgs:
            if save(img, tid):
                saved += 1
                source = img['source']
                stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
        
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
            sources_str = ', '.join([f"{k}:{v}" for k, v in stats['by_source'].items()])
            print(f"[{WORKER_ID}] {name[:40]}: +{saved} | Total: {stats['added']} ({sources_str}) | {rate:.1f}/min")
        
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


print(f"EOL+ALA WORKER: {WORKER_ID} (O(1) taxonomy lookup)")

while True:
    jobs = lease()
    if not jobs:
        time.sleep(5)
        continue
    
    for job in jobs:
        work(job)
