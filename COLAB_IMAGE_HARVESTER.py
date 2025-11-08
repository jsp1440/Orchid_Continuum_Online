# ═══════════════════════════════════════════════════════════════════
# 🌺 ORCHID CONTINUUM - AGGRESSIVE MULTI-SOURCE IMAGE HARVESTER
# ═══════════════════════════════════════════════════════════════════
# Downloads images from GBIF, EOL, iNaturalist, iDigBio
# Uploads directly to Google Drive + Sheets
# Targets species with few/no images for maximum coverage
# Run this in PARALLEL with the upload notebook!
# ═══════════════════════════════════════════════════════════════════

# CELL 1: Install Dependencies
print("📦 Installing dependencies...")
!pip install -q google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client psycopg2-binary requests pillow

print("✅ Dependencies installed!")

# CELL 2: Setup (paste token.json and DATABASE_URL like before)
import json
import os
import getpass

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

# Database URL
DATABASE_URL = "postgresql://neondb_owner:npg_feOt1Ek0KLrF@ep-snowy-firefly-afvebui7.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require"
os.environ['DATABASE_URL'] = DATABASE_URL

print("✅ Setup complete!")

# CELL 3: AGGRESSIVE IMAGE HARVESTER
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

FOLDER_ID = '1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS'
SHEET_ID = '1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz'
NUM_WORKERS = 6  # 6 download workers

downloaded_count = 0
uploaded_count = 0
failed_count = 0
start_time = time.time()
lock = threading.Lock()

creds = Credentials.from_authorized_user_info(token_data)

def get_species_needing_images():
    """Get species with fewest images (prioritize 0-10 images)"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    cur.execute("""
        SELECT ot.id, ot.genus, ot.species, ot.scientific_name, COUNT(oi.id) as image_count
        FROM orchid_taxonomy ot
        LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
        WHERE ot.genus IS NOT NULL AND ot.species IS NOT NULL
        GROUP BY ot.id, ot.genus, ot.species, ot.scientific_name
        HAVING COUNT(oi.id) < 30
        ORDER BY COUNT(oi.id) ASC, ot.id
        LIMIT 5000;
    """)
    
    species_list = cur.fetchall()
    cur.close()
    conn.close()
    return species_list

def fetch_gbif_images(scientific_name, limit=10):
    """Fetch multiple images from GBIF"""
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
            for result in results:
                if result.get('media'):
                    for media in result['media']:
                        if media.get('identifier'):
                            images.append({
                                'url': media['identifier'],
                                'source': 'GBIF',
                                'gbif_key': result.get('key'),
                                'country': result.get('country'),
                                'lat': result.get('decimalLatitude'),
                                'lon': result.get('decimalLongitude'),
                                'date': result.get('eventDate'),
                                'observer': result.get('recordedBy'),
                                'license': media.get('license', 'CC-BY-4.0')
                            })
            return images
    except:
        pass
    return []

def fetch_inaturalist_images(scientific_name, limit=10):
    """Fetch images from iNaturalist"""
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

def download_and_upload_image(image_data, taxonomy_id, scientific_name, drive_service, sheets_service):
    """Download image and upload to Drive"""
    global downloaded_count, uploaded_count, failed_count
    
    try:
        # Download image
        response = requests.get(image_data['url'], timeout=30, stream=True)
        if response.status_code != 200:
            with lock:
                failed_count += 1
            return False
        
        # Validate it's an image
        try:
            img = Image.open(BytesIO(response.content))
            img.verify()
        except:
            with lock:
                failed_count += 1
            return False
        
        # Save temp file
        ext = '.jpg'
        if 'png' in response.headers.get('content-type', ''):
            ext = '.png'
        
        temp_file = f'/tmp/orchid_new_{taxonomy_id}_{int(time.time())}{ext}'
        with open(temp_file, 'wb') as f:
            f.write(response.content)
        
        with lock:
            downloaded_count += 1
        
        # Upload to Drive
        file_metadata = {
            'name': f'orchid_new_{taxonomy_id}_{int(time.time())}{ext}',
            'parents': [FOLDER_ID]
        }
        media = MediaFileUpload(temp_file, resumable=True)
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        drive_url = file.get('webViewLink')
        os.remove(temp_file)
        
        # Insert into database
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO orchid_images 
            (taxonomy_id, image_url, google_drive_url, image_source, image_license,
             gbif_occurrence_key, latitude, longitude, country, locality,
             observation_date, observer_name, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            taxonomy_id, image_data['url'], drive_url, image_data['source'],
            image_data.get('license'), image_data.get('gbif_key'),
            image_data.get('lat'), image_data.get('lon'),
            image_data.get('country'), image_data.get('country'),
            image_data.get('date'), image_data.get('observer')
        ))
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
        conn.close()
        
        # Update Google Sheet
        try:
            row = [
                str(new_id), str(taxonomy_id), str(image_data.get('gbif_key', '')),
                image_data['url'], drive_url, image_data['source'],
                image_data.get('license', ''), str(image_data.get('lat', '')),
                str(image_data.get('lon', '')), image_data.get('country', ''),
                image_data.get('country', ''), image_data.get('date', ''),
                image_data.get('observer', ''), datetime.now().isoformat()
            ]
            sheets_service.spreadsheets().values().append(
                spreadsheetId=SHEET_ID, range='Sheet1!A:N',
                valueInputOption='RAW', body={'values': [row]}
            ).execute()
        except:
            pass
        
        with lock:
            uploaded_count += 1
        
        return True
        
    except Exception as e:
        with lock:
            failed_count += 1
        return False

def worker_harvest(worker_id, species_queue, drive_service, sheets_service):
    """Worker thread to harvest images"""
    while True:
        try:
            # Get next species from queue
            if not species_queue:
                break
            
            with lock:
                if not species_queue:
                    break
                species = species_queue.pop(0)
            
            taxonomy_id, genus, species_name, scientific_name, current_count = species
            
            print(f"[Worker {worker_id}] Harvesting {scientific_name} (currently {current_count} images)")
            
            # Fetch from multiple sources
            gbif_images = fetch_gbif_images(scientific_name, 10)
            inaturalist_images = fetch_inaturalist_images(scientific_name, 10)
            
            all_images = gbif_images + inaturalist_images
            
            # Download and upload
            for img_data in all_images[:15]:  # Max 15 per species per run
                download_and_upload_image(img_data, taxonomy_id, scientific_name, drive_service, sheets_service)
                time.sleep(0.5)  # Rate limiting
            
            time.sleep(1)  # Pause between species
            
        except Exception as e:
            print(f"[Worker {worker_id}] Error: {e}")

# Get species list
print("🔍 Finding species that need more images...")
species_list = get_species_needing_images()
print(f"✅ Found {len(species_list)} species needing images")
print(f"   Priority: {sum(1 for s in species_list if s[4] == 0)} species with 0 images")
print()

# Start harvesting
print(f"🚀 Starting {NUM_WORKERS} harvest workers...")
print("="*60)

workers = []
for i in range(NUM_WORKERS):
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    t = threading.Thread(target=worker_harvest, args=(i+1, species_list, drive_service, sheets_service))
    t.start()
    workers.append(t)
    print(f"✅ Harvest Worker {i+1} started")

print("="*60)
print("📊 Progress updates every 30 seconds...")
print()

# Monitor
last_down = 0
last_up = 0
while any(t.is_alive() for t in workers):
    time.sleep(30)
    
    elapsed = time.time() - start_time
    down_rate = downloaded_count / (elapsed / 60) if elapsed > 0 else 0
    up_rate = uploaded_count / (elapsed / 60) if elapsed > 0 else 0
    
    batch_down = downloaded_count - last_down
    batch_up = uploaded_count - last_up
    last_down = downloaded_count
    last_up = uploaded_count
    
    print(f"📊 Downloaded: {downloaded_count:,} | Uploaded: {uploaded_count:,} | Failed: {failed_count}")
    print(f"⚡ DL Speed: {down_rate:.1f}/min | UL Speed: {up_rate:.1f}/min | Last 30s: DL:{batch_down} UL:{batch_up}")
    print()

for t in workers:
    t.join()

total_time = time.time() - start_time
print("="*60)
print("🎉 HARVEST COMPLETE!")
print(f"✅ Downloaded: {downloaded_count:,}")
print(f"✅ Uploaded to Drive: {uploaded_count:,}")
print(f"❌ Failed: {failed_count}")
print(f"⏱️  Time: {total_time/3600:.2f} hours")
print(f"⚡ Avg Download Speed: {downloaded_count/(total_time/60):.1f} images/min")
print("="*60)
