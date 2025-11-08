#!/usr/bin/env python3
"""
MULTI-SOURCE ORCHID HARVESTER for Julius AI
============================================
Fetches orchid images from GBIF, EOL, Tropicos, and BHL
Automatically adds new metadata fields to JSONB columns
"""
import os, sys, time, requests, psycopg2, json
from psycopg2 import pool
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "julius-multi-1"
BATCH_SIZE = 8  # JULIUS OPTIMIZATION v2: 8 reduces lock contention with many workers
THREAD_COUNT = 12  # JULIUS OPTIMIZATION v2: 12 threads optimal for I/O-bound tasks
RECLAIM_MINUTES = 7  # JULIUS OPTIMIZATION v2: 7 min reduces lease churn
pool_obj = pool.SimpleConnectionPool(minconn=1, maxconn=15, dsn=os.environ.get('DATABASE_URL'))  # More connections for threads
stats = {'added': 0, 'start': time.time(), 'by_source': {}, 'errors': 0}

# Regional targeting for each source - GLOBAL ORCHID HOTSPOTS
# Asia-Pacific: AU, PG, ID, MY, PH, TH, VN, CN, NZ
# Americas: BR, CO, EC, PE, CR, PA (orchid megadiversity!)
# Africa: MG (Madagascar!), ZA, TZ, KE, CM, CD, RE
GBIF_COUNTRIES = [
    'AU', 'PG', 'ID', 'MY', 'PH', 'TH', 'VN', 'CN', 'NZ',  # Asia-Pacific (9)
    'BR', 'CO', 'EC', 'PE', 'CR', 'PA',                     # Americas (6) - added Peru!
    'MG', 'ZA', 'TZ', 'KE', 'CM', 'CD', 'RE'               # Africa (7) - 22 total
]
TROPICOS_API_KEY = os.environ.get('TROPICOS_API_KEY', '')
BHL_API_KEY = os.environ.get('BHL_API_KEY', '')
ALA_API_KEY = os.environ.get('ALA_API_KEY', '')  # Optional - ALA works without key

def get_conn():
    return pool_obj.getconn()

def put_conn(c):
    pool_obj.putconn(c)

def lease(n=BATCH_SIZE):
    """Lease jobs from queue"""
    c = get_conn()
    try:
        r = c.cursor()
        # JULIUS OPTIMIZATION v2: Use RECLAIM_MINUTES variable
        r.execute(f"UPDATE harvest_jobs SET status='pending', lease_owner=NULL WHERE status='leased' AND leased_at < NOW() - INTERVAL '{RECLAIM_MINUTES} minutes'")
        sql = "UPDATE harvest_jobs SET status='leased', lease_owner=%s, leased_at=NOW() WHERE id IN (SELECT id FROM harvest_jobs WHERE status='pending' ORDER BY priority DESC LIMIT %s FOR UPDATE SKIP LOCKED) RETURNING id, taxonomy_id, scientific_name"
        r.execute(sql, (WORKER_ID, n))
        jobs = r.fetchall()
        c.commit()
        return jobs
    finally:
        put_conn(c)

# ============================================================================
# GBIF ADAPTER
# ============================================================================
def fetch_gbif(name, country=None):
    """Fetch from GBIF API"""
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
    except:
        return []

# ============================================================================
# EOL ADAPTER
# ============================================================================
def fetch_eol(name):
    """Fetch from Encyclopedia of Life API"""
    try:
        # Search for species
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
        
        # Get page data with images
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
                            'description': obj.get('description', '')[:500]
                        }
                    })
        
        return imgs
    except:
        return []

# ============================================================================
# TROPICOS ADAPTER
# ============================================================================
def fetch_tropicos(name):
    """Fetch from Tropicos (Missouri Botanical Garden) API"""
    if not TROPICOS_API_KEY:
        return []
    
    try:
        # Search for species
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
        
        # Get images
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
    except:
        return []

# ============================================================================
# BHL ADAPTER (Biodiversity Heritage Library - Botanical Plates)
# ============================================================================
def fetch_bhl(name):
    """Fetch botanical plates from BHL API"""
    if not BHL_API_KEY:
        return []
    
    try:
        # Search for the name
        search_url = "https://www.biodiversitylibrary.org/api3"
        params = {'op': 'NameSearch', 'name': name, 'apikey': BHL_API_KEY, 'format': 'json'}
        resp = requests.get(search_url, params=params, timeout=15)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        if not data.get('Result') or len(data['Result']) == 0:
            return []
        
        imgs = []
        # Get first few results
        for result in data['Result'][:3]:
            page_id = result.get('PageID')
            if not page_id:
                continue
            
            # Get page metadata with image URL
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
            
            time.sleep(0.3)  # BHL rate limit
            
            if len(imgs) >= 3:  # Max 3 plates per species
                break
        
        return imgs
    except:
        return []

# ============================================================================
# ALA ADAPTER (Atlas of Living Australia - Australian Orchids)
# ============================================================================
def fetch_ala(name):
    """Fetch from Atlas of Living Australia API"""
    try:
        # ALA Biocache API
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
            # Get image URL
            img_url = occ.get('image')
            if not img_url:
                # Try images array
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
    except:
        return []

# ============================================================================
# INATURALIST ADAPTER (Community Observations - NO API KEY NEEDED)
# ============================================================================
def fetch_inaturalist(name):
    """Fetch from iNaturalist community observations"""
    try:
        # iNaturalist API - search by scientific name
        search_url = "https://api.inaturalist.org/v1/observations"
        params = {
            'taxon_name': name,
            'quality_grade': 'research',  # Only verified observations
            'photos': 'true',
            'per_page': 20
        }
        
        resp = requests.get(search_url, params=params, timeout=15)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        imgs = []
        
        for obs in data.get('results', []):
            # Get photos
            photos = obs.get('photos', [])
            if not photos:
                continue
            
            # Use first photo (usually best quality)
            photo = photos[0]
            img_url = photo.get('url')
            
            # Get large version
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
        
        return imgs[:10]  # Max 10 images from iNaturalist per species
    except:
        return []

# ============================================================================
# IDIGBIO ADAPTER (Digitized Herbarium Specimens - NO API KEY NEEDED)
# ============================================================================
def fetch_idigbio(name):
    """Fetch from iDigBio digitized herbarium collections"""
    try:
        # iDigBio Search API
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
            
            # Get media record for images
            media_url = f"https://search.idigbio.org/v2/view/records/{uuid}"
            media_resp = requests.get(media_url, timeout=10)
            
            if media_resp.status_code == 200:
                media_data = media_resp.json()
                
                # Extract image URL
                img_url = None
                if media_data.get('data', {}).get('ac:accessURI'):
                    img_url = media_data['data']['ac:accessURI']
                elif media_data.get('mediarecords'):
                    # Try media records
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
            
            time.sleep(0.2)  # Be nice to iDigBio
            
            if len(imgs) >= 5:  # Max 5 herbarium specimens per species
                break
        
        return imgs
    except:
        return []

# ============================================================================
# SAVE FUNCTION - Handles all sources with dynamic JSONB metadata
# ============================================================================
def save(img_data, tid):
    """Save image with source-specific metadata in JSONB columns"""
    c = get_conn()
    try:
        r = c.cursor()
        
        # JULIUS OPTIMIZATION: Use ON CONFLICT instead of SELECT then INSERT
        # This is faster and race-condition-proof
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
        
        # Extract values
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
        
        # JULIUS OPTIMIZATION: RETURNING id is None if conflict, not None if inserted
        result = r.fetchone()
        c.commit()
        return result is not None
    except Exception as e:
        c.rollback()
        return False
    finally:
        put_conn(c)

# ============================================================================
# WORKER LOGIC - Multi-source fetching
# ============================================================================
def work(job):
    """Process one job across multiple sources"""
    jid, tid, name = job
    try:
        all_imgs = []
        
        # 1. GBIF (baseline + regional)
        all_imgs.extend(fetch_gbif(name))
        for country in GBIF_COUNTRIES[:6]:  # Top 6 countries
            all_imgs.extend(fetch_gbif(name, country))
            time.sleep(0.08)
        
        # 2. EOL
        all_imgs.extend(fetch_eol(name))
        time.sleep(0.5)
        
        # 3. ALA (Atlas of Living Australia)
        all_imgs.extend(fetch_ala(name))
        time.sleep(0.5)
        
        # 4. iNaturalist (community observations)
        all_imgs.extend(fetch_inaturalist(name))
        time.sleep(0.5)
        
        # 5. iDigBio (herbarium specimens)
        all_imgs.extend(fetch_idigbio(name))
        time.sleep(0.5)
        
        # 6. Tropicos (if API key available)
        if TROPICOS_API_KEY:
            all_imgs.extend(fetch_tropicos(name))
            time.sleep(0.5)
        
        # 7. BHL (if API key available)
        if BHL_API_KEY:
            all_imgs.extend(fetch_bhl(name))
            time.sleep(0.5)
        
        # Save images and track by source
        saved = 0
        for img in all_imgs[:40]:  # Max 40 images per species per cycle
            if save(img, tid):
                saved += 1
                source = img['source']
                stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
        
        stats['added'] += saved
        
        # Mark job complete
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

# ============================================================================
# MAIN LOOP
# ============================================================================
print(f"🌺 MULTI-SOURCE WORKER: {WORKER_ID}")
sources_status = []
sources_status.append("GBIF (13 countries)")
sources_status.append("EOL")
sources_status.append("ALA (Australia)")
sources_status.append("iNaturalist")
sources_status.append("iDigBio (herbarium)")
sources_status.append(f"Tropicos{'✓' if TROPICOS_API_KEY else '✗'}")
sources_status.append(f"BHL{'✓' if BHL_API_KEY else '✗'}")
print(f"Sources: {', '.join(sources_status)}")
print(f"Started: {datetime.now().strftime('%I:%M:%S %p')}\n")

executor = ThreadPoolExecutor(max_workers=THREAD_COUNT)
cycle = 0

while True:
    cycle += 1
    jobs = lease(BATCH_SIZE)
    
    if not jobs:
        print(f"[{WORKER_ID}] No jobs, sleeping...")
        time.sleep(30)
        continue
    
    print(f"[{WORKER_ID}] Cycle {cycle}: Processing {len(jobs)} jobs...")
    results = [executor.submit(work, j).result() for j in jobs]
    print(f"[{WORKER_ID}] Cycle {cycle} done: {sum(results)} images\n")
    time.sleep(2)
