#!/usr/bin/env python3
"""
GBIF-ONLY WORKER - Global Biodiversity Information Facility
============================================================
Dedicated worker for GBIF API with careful rate limiting
Uses centralized taxonomy_mapper for all database operations
Run 8 workers: python workers/gbif_worker.py gbif-1 ... gbif-8
"""
import os
import sys
import time
import requests
import psycopg2
import json
from psycopg2 import pool
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taxonomy_mapper import lookup_taxon, lookup_taxon_by_id, attach_record_to_taxonomy

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "gbif-1"
BATCH_SIZE = 5
RECLAIM_MINUTES = 7
REQUEST_DELAY = 0.5

GBIF_COUNTRIES = [
    'EC', 'CO', 'PE', 'BR', 'MX', 'VE', 'CR', 'PA', 'BO', 'GT',
    'MY', 'ID', 'PH', 'TH', 'VN', 'IN', 'CN', 'MM', 'NP', 'LK',
    'MG', 'TZ', 'KE', 'ZA', 'CD', 'CM', 'AU', 'NZ', 'PG', 'NC'
]

pool_obj = None
stats = {'added': 0, 'start': time.time(), 'errors': 0}


def get_database_url():
    if os.environ.get('PGHOST'):
        return f"postgresql://{os.environ.get('PGUSER')}:{os.environ.get('PGPASSWORD')}@{os.environ.get('PGHOST')}:{os.environ.get('PGPORT')}/{os.environ.get('PGDATABASE')}?sslmode=require"
    return os.environ.get('DATABASE_URL', '')


def init_pool():
    global pool_obj
    pool_obj = pool.SimpleConnectionPool(minconn=1, maxconn=5, dsn=get_database_url())


def get_conn():
    global pool_obj
    if pool_obj is None:
        init_pool()
    return pool_obj.getconn()


def put_conn(c):
    if pool_obj and c:
        try:
            pool_obj.putconn(c)
        except:
            pass


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


def complete_job(job_id):
    c = get_conn()
    try:
        r = c.cursor()
        r.execute("UPDATE harvest_jobs SET status='completed', completed_at=NOW() WHERE id=%s", (job_id,))
        c.commit()
    finally:
        put_conn(c)


def fail_job(job_id, error):
    c = get_conn()
    try:
        r = c.cursor()
        r.execute("UPDATE harvest_jobs SET status='failed', last_error=%s WHERE id=%s", (str(error)[:200], job_id))
        c.commit()
    finally:
        put_conn(c)


def fetch_gbif(name, country=None):
    time.sleep(REQUEST_DELAY)
    
    p = {'scientificName': name, 'mediaType': 'StillImage', 'limit': 20, 'hasCoordinate': 'true'}
    if country:
        p['country'] = country
    
    try:
        resp = requests.get("https://api.gbif.org/v1/occurrence/search", params=p, timeout=15)
        
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
                    date_str = rec.get('eventDate')
                    if date_str and ('/' in date_str or len(date_str) < 10):
                        date_str = None
                    
                    imgs.append({
                        'url': m['identifier'],
                        'source': 'GBIF',
                        'type': 'observation',
                        'country': rec.get('country'),
                        'country_code': rec.get('countryCode'),
                        'state_province': rec.get('stateProvince'),
                        'locality': rec.get('locality'),
                        'lat': rec.get('decimalLatitude'),
                        'lon': rec.get('decimalLongitude'),
                        'date': date_str,
                        'year': rec.get('year'),
                        'month': rec.get('month'),
                        'gbif_key': str(rec.get('key', '')),
                        'basis_of_record': rec.get('basisOfRecord'),
                        'recorded_by': rec.get('recordedBy'),
                        'institution': rec.get('institutionCode'),
                        'license': m.get('license'),
                        'elevation': rec.get('elevation'),
                        'coordinate_uncertainty': rec.get('coordinateUncertaintyInMeters')
                    })
        
        return imgs
    except Exception as e:
        stats['errors'] += 1
        return []


def save_via_mapper(img_data, taxonomy_id, sci_name):
    """Save using centralized taxonomy_mapper"""
    record = {
        'scientific_name': sci_name,
        'source': 'GBIF',
        'taxonomy_id': taxonomy_id
    }
    
    metadata = {
        'country': img_data.get('country'),
        'country_code': img_data.get('country_code'),
        'state_province': img_data.get('state_province'),
        'locality': img_data.get('locality'),
        'latitude': img_data.get('lat'),
        'longitude': img_data.get('lon'),
        'coordinate_uncertainty': img_data.get('coordinate_uncertainty'),
        'observation_date': img_data.get('date'),
        'year_observed': img_data.get('year'),
        'month_observed': img_data.get('month'),
        'observer_name': img_data.get('recorded_by'),
        'institution_code': img_data.get('institution'),
        'image_license': img_data.get('license'),
        'image_type': img_data.get('type', 'observation'),
        'gbif_occurrence_key': img_data.get('gbif_key'),
        'occurrence_metadata': json.dumps({
            'gbif_key': img_data.get('gbif_key'),
            'basis_of_record': img_data.get('basis_of_record'),
            'recorded_by': img_data.get('recorded_by'),
            'institution': img_data.get('institution'),
            'elevation': img_data.get('elevation'),
            'coordinate_uncertainty': img_data.get('coordinate_uncertainty')
        })
    }
    
    result = attach_record_to_taxonomy(record, img_data['url'], metadata=metadata)
    return result.get('attached', False)


def work(job):
    jid, tid, name = job
    try:
        taxon = lookup_taxon_by_id(tid)
        if not taxon.get('matched'):
            fail_job(jid, 'Invalid taxonomy_id')
            return 0
        
        sci_name = taxon.get('scientific_name', name)
        
        parts = name.split() if name else ['Unknown']
        simple_name = f"{parts[0]} {parts[1]}" if len(parts) > 1 else parts[0]
        
        all_imgs = []
        
        all_imgs.extend(fetch_gbif(simple_name))
        
        for country in GBIF_COUNTRIES[:6]:
            all_imgs.extend(fetch_gbif(simple_name, country))
        
        saved = 0
        for img in all_imgs[:40]:
            if save_via_mapper(img, tid, sci_name):
                saved += 1
        
        stats['added'] += saved
        complete_job(jid)
        
        if saved > 0:
            rate = stats['added'] / ((time.time() - stats['start']) / 60)
            print(f"[{WORKER_ID}] {simple_name[:35]}: +{saved} | Total: {stats['added']} | {rate:.1f}/min")
        
        return saved
        
    except Exception as e:
        fail_job(jid, str(e))
        stats['errors'] += 1
        return 0


def main():
    print(f"GBIF WORKER: {WORKER_ID} (Using centralized taxonomy_mapper)")
    print(f"[{WORKER_ID}] Countries: {len(GBIF_COUNTRIES)}")
    
    while True:
        try:
            jobs = lease()
            if not jobs:
                print(f"[{WORKER_ID}] No jobs, waiting 30s...")
                time.sleep(30)
                continue
            
            for job in jobs:
                work(job)
            
        except Exception as e:
            print(f"[{WORKER_ID}] Error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
