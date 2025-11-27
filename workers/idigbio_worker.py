#!/usr/bin/env python3
"""
IDIGBIO-ONLY WORKER - Digitized Herbarium Specimens
====================================================
Dedicated worker for iDigBio API (NO API KEY NEEDED)
Uses O(1) taxonomy lookup via taxonomy_mapper
Run 2 workers: python workers/idigbio_worker.py idigbio-1 ... idigbio-2
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

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "idigbio-1"
BATCH_SIZE = 5
RECLAIM_MINUTES = 7
REQUEST_DELAY = 0.4

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


def fetch_idigbio(name):
    time.sleep(REQUEST_DELAY)
    
    simple_name = simplify_name(name)
    
    try:
        search_url = "https://search.idigbio.org/v2/search/records"
        
        query = {
            'rq': {
                'scientificname': simple_name,
                'hasImage': True
            },
            'limit': 15,
            'fields': [
                'uuid', 'scientificname', 'institutioncode', 
                'catalognumber', 'country', 'geopoint', 
                'datecollected', 'collector'
            ]
        }
        
        resp = requests.post(search_url, json=query, headers={'Content-Type': 'application/json'}, timeout=20)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        imgs = []
        
        for item in data.get('items', []):
            index_terms = item.get('indexTerms', {})
            
            media_records = index_terms.get('mediarecords', [])
            if not media_records:
                continue
            
            media_id = media_records[0]
            
            media_url = f"https://search.idigbio.org/v2/view/media/{media_id}"
            media_resp = requests.get(media_url, timeout=10)
            
            if media_resp.status_code == 200:
                media_data = media_resp.json()
                
                img_url = media_data.get('indexTerms', {}).get('accessuri')
                if not img_url:
                    img_url = media_data.get('data', {}).get('ac:accessURI')
                
                if img_url:
                    geopoint = index_terms.get('geopoint', {})
                    uuid = item.get('uuid')
                    
                    imgs.append({
                        'url': img_url,
                        'source': 'iDigBio',
                        'type': 'herbarium',
                        'country': index_terms.get('country'),
                        'lat': geopoint.get('lat') if isinstance(geopoint, dict) else None,
                        'lon': geopoint.get('lon') if isinstance(geopoint, dict) else None,
                        'occurrence_metadata': {
                            'idigbio_uuid': uuid,
                            'media_id': media_id,
                            'institution': index_terms.get('institutioncode'),
                            'catalog_number': index_terms.get('catalognumber'),
                            'collector': index_terms.get('collector'),
                            'collection_date': index_terms.get('datecollected')
                        }
                    })
            
            time.sleep(0.2)
            
            if len(imgs) >= 10:
                break
        
        return imgs
    except Exception:
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
            country, latitude, longitude, occurrence_metadata, 
            created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        ON CONFLICT (image_url) DO NOTHING
        RETURNING id
        """
        
        r.execute(sql, (
            tid, img_data['url'], img_data['source'], img_data['type'],
            img_data.get('country'), img_data.get('lat'), img_data.get('lon'),
            occurrence_meta
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
        
        imgs = fetch_idigbio(name)
        
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
            print(f"[{WORKER_ID}] {name[:40]}: +{saved} iDigBio | Total: {stats['added']} | {rate:.1f}/min")
        
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


print(f"IDIGBIO WORKER: {WORKER_ID} (O(1) taxonomy lookup)")

while True:
    jobs = lease()
    if not jobs:
        time.sleep(5)
        continue
    
    for job in jobs:
        work(job)
