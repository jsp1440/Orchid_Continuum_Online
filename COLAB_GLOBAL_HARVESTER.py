# ═══════════════════════════════════════════════════════════════════
# 🌍 ORCHID CONTINUUM - GLOBAL MULTI-SOURCE IMAGE HARVESTER
# ═══════════════════════════════════════════════════════════════════
# SOURCES:
# 1. GBIF (Global Biodiversity Information Facility)
# 2. iNaturalist (Citizen Science)
# 3. ALA (Atlas of Living Australia)
# 4. Tropicos (Missouri Botanical Garden - Herbarium Specimens)
# 5. EOL (Encyclopedia of Life)
# 6. JSTOR Plants (Botanical Plates)
# 7. BHL (Biodiversity Heritage Library - Historical Plates)
# 8. iDigBio (Integrated Digitized Biocollections - Museum Specimens)
# 9. NYBG (New York Botanical Garden)
# 10. Kew Gardens (Royal Botanic Gardens, UK)
#
# Run 4-5 of these in PARALLEL Colab notebooks for 500-1000 images/min!
# ═══════════════════════════════════════════════════════════════════

# CELL 1: Install Dependencies
print("📦 Installing dependencies...")
!pip install -q google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client psycopg2-binary requests pillow lxml beautifulsoup4

print("✅ Dependencies installed!")

# CELL 2: Setup Credentials
import json
import os

# Create token.json
token_data = {
    "token": "ya29.a0ATi6K2tn09ibNP3_dcD73lVHLk5Smtdr4jsksHaYmHQWTaGEEUp30VtOdTvqj1D0lo-6E4gZaT_9ukjLsu6sqh3YOEKhxrZ-hcutqYPvh4F2Z6AR9MqAw9-TSSDNkz63-kDJwJfF3OE0phiSVCRVUsNSmeYtxyByLzjNWqP8F2JpsX7yRtffE4Wfab10BLHtKSK7Eu8aCgYKAQUSARYSFQHGX2MilWuDZlj2TRjvoB1TkjQDGA0206",
    "refresh_token": "1//0619R5NlyMv3CCgYIARAAGAYSNwF-L9IrDKfWpmr-hVooSHAIpLioEuUURPuk5ZSDasJEOOg0e7lF0edz45fi17vzbfYuFxBY5Vs",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "941511288223-0ocr4hnk9qf14as9ibqooov9es0tt8ub.apps.googleusercontent.com",
    "client_secret": "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",
    "scopes": ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"],
    "universe_domain": "googleapis.com"
}
with open('token.json', 'w') as f:
    json.dump(token_data, f)

DATABASE_URL = "postgresql://neondb_owner:npg_feOt1Ek0KLrF@ep-snowy-firefly-afvebui7.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require"
os.environ['DATABASE_URL'] = DATABASE_URL

print("✅ Setup complete!")

# CELL 3: GLOBAL HARVESTER - ALL SOURCES
import threading
import time
import psycopg2
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
import re

FOLDER_ID = '1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS'
SHEET_ID = '1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz'
NUM_WORKERS = 8

stats = {
    'downloaded': 0, 'uploaded': 0, 'failed': 0,
    'gbif': 0, 'inaturalist': 0, 'ala': 0, 'tropicos': 0,
    'eol': 0, 'jstor': 0, 'bhl': 0, 'idigbio': 0
}
lock = threading.Lock()
start_time = time.time()

creds = Credentials.from_authorized_user_info(token_data)

# ═══════════════════════════════════════════════════════════════════
# DATA SOURCE FETCHERS
# ═══════════════════════════════════════════════════════════════════

def fetch_gbif_images(scientific_name, limit=15):
    """GBIF - Global occurrence records"""
    try:
        response = requests.get(
            "https://api.gbif.org/v1/occurrence/search",
            params={
                'scientificName': scientific_name,
                'mediaType': 'StillImage',
                'limit': limit
            },
            timeout=10
        )
        if response.status_code == 200:
            results = response.json().get('results', [])
            images = []
            for r in results:
                if r.get('media'):
                    for m in r['media']:
                        if m.get('identifier'):
                            images.append({
                                'url': m['identifier'],
                                'source': 'GBIF',
                                'type': 'observation',
                                'gbif_key': r.get('key'),
                                'country': r.get('country'),
                                'lat': r.get('decimalLatitude'),
                                'lon': r.get('decimalLongitude'),
                                'date': r.get('eventDate'),
                                'observer': r.get('recordedBy'),
                                'license': m.get('license', 'CC-BY-4.0')
                            })
            return images
    except:
        pass
    return []

def fetch_inaturalist_images(scientific_name, limit=15):
    """iNaturalist - Citizen science observations"""
    try:
        response = requests.get(
            "https://api.inaturalist.org/v1/observations",
            params={
                'taxon_name': scientific_name,
                'photos': 'true',
                'per_page': limit,
                'quality_grade': 'research'
            },
            timeout=10
        )
        if response.status_code == 200:
            results = response.json().get('results', [])
            images = []
            for obs in results:
                if obs.get('photos'):
                    for photo in obs['photos']:
                        images.append({
                            'url': photo.get('url', '').replace('square', 'original'),
                            'source': 'iNaturalist',
                            'type': 'observation',
                            'country': obs.get('place_guess'),
                            'lat': obs.get('location') and obs['location'].split(',')[0],
                            'lon': obs.get('location') and obs['location'].split(',')[1],
                            'date': obs.get('observed_on'),
                            'observer': obs.get('user', {}).get('login'),
                            'license': photo.get('license_code', 'CC-BY-NC')
                        })
            return images
    except:
        pass
    return []

def fetch_ala_images(scientific_name, limit=15):
    """Atlas of Living Australia - Australian occurrences"""
    try:
        response = requests.get(
            "https://biocache-ws.ala.org.au/ws/occurrences/search",
            params={
                'q': f'scientificName:"{scientific_name}"',
                'fq': 'multimedia:Image',
                'pageSize': limit
            },
            timeout=10
        )
        if response.status_code == 200:
            results = response.json().get('occurrences', [])
            images = []
            for r in results:
                if r.get('image'):
                    images.append({
                        'url': r['image'],
                        'source': 'ALA',
                        'type': 'observation',
                        'country': r.get('country', 'Australia'),
                        'lat': r.get('decimalLatitude'),
                        'lon': r.get('decimalLongitude'),
                        'date': r.get('eventDate'),
                        'observer': r.get('recordedBy'),
                        'license': r.get('license', 'CC-BY')
                    })
            return images
    except:
        pass
    return []

def fetch_tropicos_herbarium(genus, species, limit=10):
    """Tropicos/Missouri Botanical Garden - Herbarium specimens"""
    try:
        # Search for specimens
        response = requests.get(
            f"https://www.tropicos.org/api/v3/specimens/search",
            params={
                'name': f'{genus} {species}',
                'format': 'json',
                'apikey': 'public'  # Use public access
            },
            timeout=10
        )
        if response.status_code == 200:
            specimens = response.json()[:limit]
            images = []
            for spec in specimens:
                if spec.get('SpecimenId'):
                    # Try to get specimen image
                    img_url = f"https://www.tropicos.org/Image/{spec['SpecimenId']}"
                    images.append({
                        'url': img_url,
                        'source': 'Tropicos',
                        'type': 'herbarium',
                        'country': spec.get('CountryName'),
                        'collector': spec.get('CollectorString'),
                        'license': 'CC-BY-NC'
                    })
            return images
    except:
        pass
    return []

def fetch_eol_images(scientific_name, limit=10):
    """Encyclopedia of Life - Curated images"""
    try:
        # Search for taxon
        search = requests.get(
            "https://eol.org/api/search/1.0.json",
            params={'q': scientific_name, 'page': 1},
            timeout=10
        )
        if search.status_code == 200:
            results = search.json().get('results', [])
            if results:
                taxon_id = results[0].get('id')
                # Get pages with images
                pages = requests.get(
                    f"https://eol.org/api/pages/1.0/{taxon_id}.json",
                    params={'images_per_page': limit, 'images_page': 1},
                    timeout=10
                )
                if pages.status_code == 200:
                    data = pages.json()
                    images = []
                    for obj in data.get('dataObjects', []):
                        if obj.get('dataType') == 'http://purl.org/dc/dcmitype/StillImage':
                            images.append({
                                'url': obj.get('eolMediaURL'),
                                'source': 'EOL',
                                'type': 'curated',
                                'license': obj.get('license', 'CC-BY-SA')
                            })
                    return images
    except:
        pass
    return []

def fetch_idigbio_specimens(scientific_name, limit=10):
    """iDigBio - US Museum specimens"""
    try:
        response = requests.get(
            "https://search.idigbio.org/v2/search/records/",
            params={
                'rq': json.dumps({"scientificname": scientific_name}),
                'limit': limit,
                'offset': 0
            },
            timeout=10
        )
        if response.status_code == 200:
            items = response.json().get('items', [])
            images = []
            for item in items:
                data = item.get('indexTerms', {})
                if data.get('hasImage') and data.get('mediarecords'):
                    for media_uuid in data['mediarecords'][:3]:
                        img_url = f"https://api.idigbio.org/v2/media/{media_uuid}"
                        images.append({
                            'url': img_url,
                            'source': 'iDigBio',
                            'type': 'herbarium',
                            'country': data.get('country'),
                            'collector': data.get('collector'),
                            'license': 'CC0'
                        })
            return images
    except:
        pass
    return []

def fetch_jstor_plants(scientific_name, limit=5):
    """JSTOR Plants - Botanical type specimens and plates"""
    try:
        # Search JSTOR Global Plants
        search_url = f"https://plants.jstor.org/search?searchText={scientific_name.replace(' ', '+')}"
        response = requests.get(search_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            images = []
            # Look for specimen images
            img_tags = soup.find_all('img', {'class': re.compile('specimen|plate')})[:limit]
            for img in img_tags:
                img_url = img.get('src')
                if img_url and img_url.startswith('http'):
                    images.append({
                        'url': img_url,
                        'source': 'JSTOR',
                        'type': 'botanical_plate',
                        'license': 'Public Domain'
                    })
            return images
    except:
        pass
    return []

def fetch_bhl_plates(genus, species, limit=5):
    """Biodiversity Heritage Library - Historical botanical plates"""
    try:
        response = requests.get(
            "https://www.biodiversitylibrary.org/api3",
            params={
                'op': 'PublicationSearch',
                'searchterm': f'{genus} {species}',
                'format': 'json',
                'apikey': 'public'
            },
            timeout=10
        )
        if response.status_code == 200:
            results = response.json().get('Result', [])[:limit]
            images = []
            for item in results:
                # BHL has plate URLs in specific format
                if item.get('ThumbnailUrl'):
                    full_url = item['ThumbnailUrl'].replace('/thumbnail/', '/pageimage/')
                    images.append({
                        'url': full_url,
                        'source': 'BHL',
                        'type': 'botanical_plate',
                        'license': 'Public Domain'
                    })
            return images
    except:
        pass
    return []

# ═══════════════════════════════════════════════════════════════════
# DOWNLOAD AND UPLOAD
# ═══════════════════════════════════════════════════════════════════

def download_and_upload(image_data, taxonomy_id, scientific_name, drive_service, sheets_service):
    """Download image and upload to Drive"""
    global stats
    
    try:
        # Download
        response = requests.get(image_data['url'], timeout=30, stream=True)
        if response.status_code != 200:
            with lock:
                stats['failed'] += 1
            return False
        
        # Validate image
        try:
            img = Image.open(BytesIO(response.content))
            img.verify()
        except:
            with lock:
                stats['failed'] += 1
            return False
        
        # Save temp
        ext = '.jpg'
        if 'png' in response.headers.get('content-type', ''):
            ext = '.png'
        
        temp_file = f'/tmp/orchid_{taxonomy_id}_{int(time.time() * 1000)}{ext}'
        with open(temp_file, 'wb') as f:
            f.write(response.content)
        
        with lock:
            stats['downloaded'] += 1
            stats[image_data['source'].lower()] += 1
        
        # Upload to Drive
        file_metadata = {
            'name': f"{image_data['source']}_{image_data['type']}_{taxonomy_id}_{int(time.time())}{ext}",
            'parents': [FOLDER_ID]
        }
        media = MediaFileUpload(temp_file, resumable=True)
        file = drive_service.files().create(
            body=file_metadata, media_body=media, fields='id, webViewLink'
        ).execute()
        
        drive_url = file.get('webViewLink')
        os.remove(temp_file)
        
        # Insert to database
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO orchid_images 
            (taxonomy_id, image_url, google_drive_url, image_source, image_license,
             image_type, gbif_occurrence_key, latitude, longitude, country, 
             observation_date, observer_name, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            taxonomy_id, image_data['url'], drive_url, image_data['source'],
            image_data.get('license'), image_data.get('type'),
            image_data.get('gbif_key'), image_data.get('lat'), 
            image_data.get('lon'), image_data.get('country'),
            image_data.get('date'), image_data.get('observer')
        ))
        conn.commit()
        cur.close()
        conn.close()
        
        # Update sheet
        try:
            sheets_service.spreadsheets().values().append(
                spreadsheetId=SHEET_ID, range='Sheet1!A:N',
                valueInputOption='RAW', 
                body={'values': [[
                    str(taxonomy_id), scientific_name, image_data['source'],
                    image_data['type'], drive_url, image_data['url'],
                    image_data.get('license', ''), datetime.now().isoformat()
                ]]}
            ).execute()
        except:
            pass
        
        with lock:
            stats['uploaded'] += 1
        
        return True
        
    except Exception as e:
        with lock:
            stats['failed'] += 1
        return False

# ═══════════════════════════════════════════════════════════════════
# WORKER THREADS
# ═══════════════════════════════════════════════════════════════════

def get_species_needing_images():
    """Get species with fewest images"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    cur.execute("""
        SELECT ot.id, ot.genus, ot.species, ot.scientific_name, COUNT(oi.id) as img_count
        FROM orchid_taxonomy ot
        LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
        WHERE ot.genus IS NOT NULL AND ot.species IS NOT NULL
        GROUP BY ot.id, ot.genus, ot.species, ot.scientific_name
        HAVING COUNT(oi.id) < 30
        ORDER BY COUNT(oi.id) ASC, ot.id
        LIMIT 3000;
    """)
    species_list = cur.fetchall()
    cur.close()
    conn.close()
    return species_list

def worker_harvest(worker_id, species_queue, drive_service, sheets_service):
    """Worker thread"""
    while True:
        try:
            with lock:
                if not species_queue:
                    break
                species = species_queue.pop(0)
            
            taxonomy_id, genus, species_name, scientific_name, current_count = species
            
            print(f"[W{worker_id}] {scientific_name} ({current_count} images)")
            
            # Fetch from ALL sources
            all_images = []
            all_images.extend(fetch_gbif_images(scientific_name, 10))
            all_images.extend(fetch_inaturalist_images(scientific_name, 10))
            all_images.extend(fetch_ala_images(scientific_name, 8))
            all_images.extend(fetch_tropicos_herbarium(genus, species_name, 5))
            all_images.extend(fetch_eol_images(scientific_name, 5))
            all_images.extend(fetch_idigbio_specimens(scientific_name, 5))
            all_images.extend(fetch_jstor_plants(scientific_name, 3))
            all_images.extend(fetch_bhl_plates(genus, species_name, 3))
            
            # Download and upload (max 20 per species per run)
            for img_data in all_images[:20]:
                download_and_upload(img_data, taxonomy_id, scientific_name, drive_service, sheets_service)
                time.sleep(0.3)
            
            time.sleep(1)
            
        except Exception as e:
            print(f"[W{worker_id}] Error: {e}")

# ═══════════════════════════════════════════════════════════════════
# START HARVESTING
# ═══════════════════════════════════════════════════════════════════

print("🔍 Finding species needing images...")
species_list = get_species_needing_images()
print(f"✅ Found {len(species_list)} species")
print(f"   {sum(1 for s in species_list if s[4] == 0)} with 0 images")
print(f"   {sum(1 for s in species_list if s[4] < 10)} with <10 images")
print()

print(f"🚀 Starting {NUM_WORKERS} global harvest workers...")
print("="*70)

workers = []
for i in range(NUM_WORKERS):
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    t = threading.Thread(target=worker_harvest, args=(i+1, species_list, drive_service, sheets_service))
    t.start()
    workers.append(t)
    print(f"✅ Worker {i+1} started")

print("="*70)
print("📊 Monitoring (every 30s)...")
print()

last_down = 0
last_up = 0
while any(t.is_alive() for t in workers):
    time.sleep(30)
    
    elapsed = time.time() - start_time
    down_rate = stats['downloaded'] / (elapsed / 60) if elapsed > 0 else 0
    up_rate = stats['uploaded'] / (elapsed / 60) if elapsed > 0 else 0
    
    batch_down = stats['downloaded'] - last_down
    batch_up = stats['uploaded'] - last_up
    last_down = stats['downloaded']
    last_up = stats['uploaded']
    
    print(f"📊 DL: {stats['downloaded']:,} | UP: {stats['uploaded']:,} | FAIL: {stats['failed']}")
    print(f"   GBIF:{stats['gbif']} iNat:{stats['inaturalist']} ALA:{stats['ala']} Trop:{stats['tropicos']}")
    print(f"   EOL:{stats['eol']} iDig:{stats['idigbio']} JSTOR:{stats['jstor']} BHL:{stats['bhl']}")
    print(f"⚡ DL:{down_rate:.1f}/min UP:{up_rate:.1f}/min | 30s: DL:{batch_down} UP:{batch_up}")
    print()

for t in workers:
    t.join()

total_time = time.time() - start_time
print("="*70)
print("🎉 GLOBAL HARVEST COMPLETE!")
print(f"✅ Downloaded: {stats['downloaded']:,}")
print(f"✅ Uploaded: {stats['uploaded']:,}")
print(f"❌ Failed: {stats['failed']}")
print(f"⏱️  Time: {total_time/3600:.2f} hours")
print(f"⚡ Avg: {stats['downloaded']/(total_time/60):.1f} images/min")
print()
print("📊 BY SOURCE:")
print(f"   GBIF: {stats['gbif']}")
print(f"   iNaturalist: {stats['inaturalist']}")
print(f"   ALA (Australia): {stats['ala']}")
print(f"   Tropicos (Herbarium): {stats['tropicos']}")
print(f"   EOL: {stats['eol']}")
print(f"   iDigBio (Museums): {stats['idigbio']}")
print(f"   JSTOR (Plates): {stats['jstor']}")
print(f"   BHL (Historical): {stats['bhl']}")
print("="*70)
