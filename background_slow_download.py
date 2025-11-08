"""
Background Slow Download - Runs continuously, downloads ~500 images/hour
Safe, won't timeout, just keeps running forever
"""
import os
import time
import requests
import psycopg2
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATABASE_URL = os.environ.get('DATABASE_URL')

# Download settings
IMAGES_PER_BATCH = 10
DELAY_BETWEEN_BATCHES = 60  # 60 seconds = ~600 images/hour
MAX_PER_RUN = 5000  # Stop after 5000 to avoid running forever

print("🌺 BACKGROUND SLOW DOWNLOAD STARTED")
print(f"⏱️  {datetime.now()}")
print("=" * 70)

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Get GBIF images that need local copies
cursor.execute("""
    SELECT id, image_url, image_source
    FROM orchid_images
    WHERE local_path IS NULL
    AND image_url IS NOT NULL
    AND image_source LIKE 'GBIF%'
    LIMIT %s
""", (MAX_PER_RUN,))

to_download = cursor.fetchall()
total = len(to_download)

print(f"📋 Found {total:,} images to download")
print(f"📥 Downloading {IMAGES_PER_BATCH} every {DELAY_BETWEEN_BATCHES}s")
print()

os.makedirs('attached_assets/gbif_background', exist_ok=True)

downloaded = 0
failed = 0

for i, (img_id, url, source) in enumerate(to_download, 1):
    try:
        response = requests.get(url, timeout=10, verify=False)
        
        if response.status_code == 200:
            # Determine file extension
            ext = 'jpg'
            if '.png' in url.lower():
                ext = 'png'
            
            filename = f"gbif_bg_{img_id}.{ext}"
            local_path = f"attached_assets/gbif_background/{filename}"
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            # Update database
            cursor.execute("""
                UPDATE orchid_images 
                SET local_path = %s
                WHERE id = %s
            """, (local_path, img_id))
            
            conn.commit()
            downloaded += 1
            
        else:
            failed += 1
    
    except Exception as e:
        failed += 1
        continue
    
    # Progress update every batch
    if i % IMAGES_PER_BATCH == 0:
        print(f"[{i:,}/{total:,}] ✅ {downloaded:,} | ❌ {failed:,} | {datetime.now().strftime('%H:%M:%S')}")
        
        # Delay between batches to keep load low
        if i < total:
            time.sleep(DELAY_BETWEEN_BATCHES)

cursor.close()
conn.close()

print()
print("=" * 70)
print(f"✅ BATCH COMPLETE - {datetime.now()}")
print(f"📥 Downloaded: {downloaded:,}")
print(f"❌ Failed: {failed:,}")
print("=" * 70)
