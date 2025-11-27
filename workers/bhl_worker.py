#!/usr/bin/env python3
"""
BHL-ONLY WORKER - Biodiversity Heritage Library
===============================================
Dedicated worker for BHL API - Botanical Plates (REQUIRES API KEY)
Uses O(1) taxonomy lookup via taxonomy_mapper
Run 1 worker: python workers/bhl_worker.py bhl-1
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

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "bhl-1"
BATCH_SIZE = 4
RECLAIM_MINUTES = 7
REQUEST_DELAY = 0.8
BHL_API_KEY = os.environ.get('BHL_API_KEY', '')

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
    parts = full_name.split()
    if len(parts) < 2:
        return full_name
    
    genus = parts[0]
    
    if parts[1] == 'x' and len(parts) >= 3:
        return f"{genus} {parts[2]}"
    
    if len(parts) >= 3 and parts[2] in ('ssp.', 'subsp.', 'var.', 'f.', 'forma'):
        return f"{genus} {parts[1]}"
    
    return f"{genus} {parts[1]}"


def fetch_bhl(name):
    if not BHL_API_KEY:
        return []
    
    time.sleep(REQUEST_DELAY)
    
    simple_name = simplify_name(name)
    
    try:
        search_url = "https://www.biodiversitylibrary.org/api3"
        params = {'op': 'NameSearch', 'name': simple_name, 'apikey': BHL_API_KEY, 'format': 'json'}
        resp = requests.get(search_url, params=params, timeout=15)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        results = data.get('Result', [])
        if not results:
            return []
        
        imgs = []
        for name_result in results[:3]:
            name_confirmed = name_result.get('NameConfirmed', '')
            
            page_params = {'op': 'NameGetPages', 'name': name_confirmed, 'apikey': BHL_API_KEY, 'format': 'json'}
            page_resp = requests.get(search_url, params=page_params, timeout=10)
            
            if page_resp.status_code == 200:
                page_data = page_resp.json()
                pages = page_data.get('Result', [])
                
                for page in pages[:3]:
                    page_id = page.get('PageID')
                    if page_id:
                        page_url = f"https://www.biodiversitylibrary.org/page/{page_id}"
                        
                        imgs.append({
                            'url': page_url,
                            'source': 'BHL - Biodiversity Heritage Library',
                            'type': 'illustration',
                            'media_metadata': {
                                'page_id': str(page_id),
                                'item_id': page.get('ItemID'),
                                'volume': page.get('Volume', ''),
                                'year': page.get('Year', '')
                            }
                        })
                        
                        if len(imgs) >= 5:
                            break
            
            time.sleep(0.4)
            
            if len(imgs) >= 5:
                break
        
        return imgs
    except Exception:
        stats['errors'] += 1
        return []


def save(img_data, tid):
    c = get_conn()
    try:
        r = c.cursor()
        
        media_meta = json.dumps(img_data.get('media_metadata')) if img_data.get('media_metadata') else None
        
        sql = """
        INSERT INTO orchid_images (
            taxonomy_id, image_url, image_source, image_type,
            media_metadata, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, NOW(), NOW()
        )
        ON CONFLICT (image_url) DO NOTHING
        RETURNING id
        """
        
        r.execute(sql, (
            tid, img_data['url'], img_data['source'], img_data['type'],
            media_meta
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
        
        imgs = fetch_bhl(name)
        
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
            print(f"[{WORKER_ID}] {name[:40]}: +{saved} BHL | Total: {stats['added']} | {rate:.1f}/min")
        
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


if not BHL_API_KEY:
    print(f"BHL_API_KEY not set! Worker will not start.")
    sys.exit(1)

print(f"BHL WORKER: {WORKER_ID} (O(1) taxonomy lookup)")

while True:
    jobs = lease()
    if not jobs:
        time.sleep(5)
        continue
    
    for job in jobs:
        work(job)
