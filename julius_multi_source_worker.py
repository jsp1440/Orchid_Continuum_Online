#!/usr/bin/env python3
"""
MULTI-SOURCE ORCHID HARVESTER for Julius AI
============================================
Fetches orchid images from GBIF, EOL, Tropicos, and BHL
Uses O(1) taxonomy lookup via taxonomy_mapper
Automatically adds new metadata fields to JSONB columns
"""
import os
import sys
import time
import requests
import psycopg2
import json
from psycopg2 import pool
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from taxonomy_mapper import lookup_taxon, lookup_taxon_by_id

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "julius-multi-1"
BATCH_SIZE = 8
THREAD_COUNT = 12
RECLAIM_MINUTES = 7

pool_obj = pool.SimpleConnectionPool(minconn=1, maxconn=15, dsn=os.environ.get('DATABASE_URL'))
stats = {'added': 0, 'start': time.time(), 'by_source': {}, 'errors': 0}

GBIF_COUNTRIES = [
    'AU', 'PG', 'ID', 'MY', 'PH', 'TH', 'VN', 'CN', 'NZ',
    'BR', 'CO', 'EC', 'PE', 'CR', 'PA',
    'MG', 'ZA', 'TZ', 'KE', 'CM', 'CD', 'RE'
]

TROPICOS_API_KEY = os.environ.get('TROPICOS_API_KEY', '')
BHL_API_KEY = os.environ.get('BHL_API_KEY', '')
ALA_API_KEY = os.environ.get('ALA_API_KEY', '')


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


def fetch_gbif(name, country=None):
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
    except Exception:
        return []


def fetch_eol(name):
    try:
        search_url = "https://eol.org/api/search/1.0.json"
        params = {'q': name, 'page': 1, 'exact': True}
        resp = requests.get(search_url, params=params, timeout=10)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        if not data.get('results') or len(data['results']) == 0:
            return []
        
        page_id = data['results'][0].get('id')
        if not page_id:
            return []
        
        page_url = f"https://eol.org/api/pages/1.0/{page_id}.json"
        params = {'images': 5, 'videos': 0, 'details': True}
        resp = requests.get(page_url, params=params, timeout=15)
        if resp.status_code != 200:
            return []
        
        page_data = resp.json()
        imgs = []
        
        for obj in page_data.get('dataObjects', []):
            if obj.get('dataType') == 'http://purl.org/dc/dcmitype/StillImage':
                url = obj.get('mediaURL', '')
                if url:
                    imgs.append({
                        'url': url,
                        'source': 'EOL',
                        'type': 'observation',
                        'eol_metadata': {
                            'page_id': str(page_id),
                            'data_object_id': obj.get('dataObjectVersionID'),
                            'license': obj.get('license', ''),
                            'rights_holder': obj.get('rightsHolder', ''),
                            'description': obj.get('description', '')[:500] if obj.get('description') else ''
                        }
                    })
        
        return imgs
    except Exception:
        return []


def fetch_tropicos(name):
    if not TROPICOS_API_KEY:
        return []
    
    try:
        search_url = "http://services.tropicos.org/Name/Search"
        params = {'apikey': TROPICOS_API_KEY, 'name': name, 'type': 'wildcard', 'format': 'json'}
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
        params = {'apikey': TROPICOS_API_KEY, 'format': 'json', 'pagesize': 5}
        resp = requests.get(images_url, params=params, timeout=15)
        if resp.status_code != 200:
            return []
        
        images_data = resp.json()
        imgs = []
        
        if isinstance(images_data, list):
            for img in images_data:
                url = img.get('Url', '')
                if url:
                    imgs.append({
                        'url': url,
                        'source': 'Tropicos',
                        'type': 'herbarium',
                        'tropicos_metadata': {
                            'name_id': str(name_id),
                            'specimen_id': img.get('SpecimenId'),
                            'detail_url': img.get('DetailUrl'),
                            'copyright': img.get('CopyrightOwner', '')
                        }
                    })
        
        return imgs
    except Exception:
        return []


def fetch_bhl(name):
    if not BHL_API_KEY:
        return []
    
    try:
        search_url = "https://www.biodiversitylibrary.org/api3"
        params = {'op': 'NameSearch', 'name': name, 'apikey': BHL_API_KEY, 'format': 'json'}
        resp = requests.get(search_url, params=params, timeout=15)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        if not data.get('Result') or len(data['Result']) == 0:
            return []
        
        imgs = []
        for result in data['Result'][:3]:
            page_id = result.get('PageID')
            if not page_id:
                continue
            
            page_url = "https://www.biodiversitylibrary.org/api3"
            page_params = {'op': 'GetPageMetadata', 'pageid': page_id, 'apikey': BHL_API_KEY, 'format': 'json'}
            page_resp = requests.get(page_url, params=page_params, timeout=10)
            
            if page_resp.status_code == 200:
                page_data = page_resp.json()
                if page_data.get('Result'):
                    img_url = page_data['Result'][0].get('PageUrl')
                    if img_url:
                        imgs.append({
                            'url': img_url,
                            'source': 'BHL',
                            'type': 'botanical_plate',
                            'media_metadata': {
                                'page_id': str(page_id),
                                'title_id': result.get('TitleID'),
                                'item_id': result.get('ItemID')
                            }
                        })
            
            time.sleep(0.3)
            
            if len(imgs) >= 3:
                break
        
        return imgs
    except Exception:
        return []


def fetch_ala(name):
    try:
        search_url = "https://biocache.ala.org.au/ws/occurrences/search"
        params = {
            'q': f'scientificName:"{name}"',
            'fq': 'multimedia:Image',
            'pageSize': 10
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
        return []


def fetch_inaturalist(name):
    try:
        search_url = "https://api.inaturalist.org/v1/observations"
        params = {
            'taxon_name': name,
            'quality_grade': 'research',
            'photos': 'true',
            'per_page': 20
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
                location = obs.get('location')
                lat = None
                lon = None
                if location and ',' in location:
                    parts = location.split(',')
                    try:
                        lat = float(parts[0])
                        lon = float(parts[1])
                    except (ValueError, IndexError):
                        pass
                
                imgs.append({
                    'url': img_url,
                    'source': 'iNaturalist',
                    'type': 'observation',
                    'country': obs.get('place_guess', '').split(',')[-1].strip() if obs.get('place_guess') else None,
                    'lat': lat,
                    'lon': lon,
                    'date': obs.get('observed_on'),
                    'year': obs.get('observed_on_details', {}).get('year'),
                    'occurrence_metadata': {
                        'inaturalist_id': str(obs.get('id', '')),
                        'quality_grade': obs.get('quality_grade'),
                        'observer': obs.get('user', {}).get('login'),
                        'num_identification_agreements': obs.get('num_identification_agreements', 0)
                    }
                })
        
        return imgs[:10]
    except Exception:
        return []


def fetch_idigbio(name):
    try:
        search_url = "https://search.idigbio.org/v2/search/records"
        
        query = {
            'rq': {
                'scientificname': name,
                'hasImage': True
            },
            'limit': 10,
            'fields': [
                'uuid', 'scientificname', 'institutioncode', 
                'catalognumber', 'country', 'geopoint', 
                'datecollected', 'collector'
            ]
        }
        
        resp = requests.post(search_url, json=query, headers={'Content-Type': 'application/json'}, timeout=15)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        imgs = []
        
        for item in data.get('items', []):
            uuid = item.get('uuid')
            if not uuid:
                continue
            
            media_url = f"https://search.idigbio.org/v2/view/records/{uuid}"
            media_resp = requests.get(media_url, timeout=10)
            
            if media_resp.status_code == 200:
                media_data = media_resp.json()
                
                img_url = None
                if media_data.get('data', {}).get('ac:accessURI'):
                    img_url = media_data['data']['ac:accessURI']
                elif media_data.get('mediarecords'):
                    for media in media_data['mediarecords']:
                        if media.get('accessuri'):
                            img_url = media['accessuri']
                            break
                
                if img_url:
                    index_terms = item.get('indexTerms', {})
                    geopoint = index_terms.get('geopoint', {})
                    
                    imgs.append({
                        'url': img_url,
                        'source': 'iDigBio',
                        'type': 'herbarium',
                        'country': index_terms.get('country'),
                        'lat': geopoint.get('lat') if isinstance(geopoint, dict) else None,
                        'lon': geopoint.get('lon') if isinstance(geopoint, dict) else None,
                        'occurrence_metadata': {
                            'idigbio_uuid': uuid,
                            'institution': index_terms.get('institutioncode'),
                            'catalog_number': index_terms.get('catalognumber'),
                            'collector': index_terms.get('collector'),
                            'collection_date': index_terms.get('datecollected')
                        }
                    })
            
            time.sleep(0.2)
            
            if len(imgs) >= 5:
                break
        
        return imgs
    except Exception:
        return []


def save(img_data, tid):
    c = get_conn()
    try:
        r = c.cursor()
        
        sql = """
        INSERT INTO orchid_images (
            taxonomy_id, image_url, image_source, image_type,
            country, latitude, longitude, observation_date, year_observed,
            gbif_occurrence_key, occurrence_metadata, eol_metadata, tropicos_metadata,
            created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        ON CONFLICT (image_url) DO NOTHING
        RETURNING id
        """
        
        occurrence_meta = json.dumps(img_data.get('occurrence_metadata')) if img_data.get('occurrence_metadata') else None
        eol_meta = json.dumps(img_data.get('eol_metadata')) if img_data.get('eol_metadata') else None
        tropicos_meta = json.dumps(img_data.get('tropicos_metadata')) if img_data.get('tropicos_metadata') else None
        
        gbif_key = img_data.get('occurrence_metadata', {}).get('gbif_key') if img_data.get('occurrence_metadata') else None
        
        r.execute(sql, (
            tid,
            img_data['url'],
            img_data['source'],
            img_data['type'],
            img_data.get('country'),
            img_data.get('lat'),
            img_data.get('lon'),
            img_data.get('date'),
            img_data.get('year'),
            gbif_key,
            occurrence_meta,
            eol_meta,
            tropicos_meta
        ))
        
        result = r.fetchone()
        c.commit()
        return result is not None
    except Exception:
        c.rollback()
        return False
    finally:
        put_conn(c)


def work(job):
    jid, tid, name = job
    try:
        taxon = lookup_taxon_by_id(tid)
        if not taxon.get('matched'):
            print(f"[{WORKER_ID}] Invalid taxonomy_id {tid}, skipping job {jid}")
            c = get_conn()
            try:
                r = c.cursor()
                r.execute("UPDATE harvest_jobs SET status='failed', last_error='Invalid taxonomy_id' WHERE id=%s", (jid,))
                c.commit()
            finally:
                put_conn(c)
            return 0
        
        simple_name = simplify_name(name) if name else 'Unknown'
        all_imgs = []
        
        all_imgs.extend(fetch_gbif(simple_name))
        for country in GBIF_COUNTRIES[:6]:
            all_imgs.extend(fetch_gbif(simple_name, country))
            time.sleep(0.08)
        
        all_imgs.extend(fetch_eol(simple_name))
        time.sleep(0.5)
        
        all_imgs.extend(fetch_ala(simple_name))
        time.sleep(0.5)
        
        all_imgs.extend(fetch_inaturalist(simple_name))
        time.sleep(0.5)
        
        all_imgs.extend(fetch_idigbio(simple_name))
        time.sleep(0.5)
        
        if TROPICOS_API_KEY:
            all_imgs.extend(fetch_tropicos(simple_name))
            time.sleep(0.5)
        
        if BHL_API_KEY:
            all_imgs.extend(fetch_bhl(simple_name))
            time.sleep(0.5)
        
        saved = 0
        for img in all_imgs[:40]:
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
        return 0


print(f"MULTI-SOURCE WORKER: {WORKER_ID} (O(1) taxonomy lookup)")
sources_status = []
sources_status.append("GBIF (22 countries)")
sources_status.append("EOL")
sources_status.append("ALA (Australia)")
sources_status.append("iNaturalist")
sources_status.append("iDigBio (herbarium)")
if TROPICOS_API_KEY:
    sources_status.append("Tropicos")
if BHL_API_KEY:
    sources_status.append("BHL")
print(f"[{WORKER_ID}] Sources: {', '.join(sources_status)}")

while True:
    jobs = lease()
    if not jobs:
        time.sleep(5)
        continue
    
    for job in jobs:
        work(job)
