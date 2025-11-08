#!/usr/bin/env python3
"""
SIMPLE EOL DOWNLOADER - Using correct EOL content URLs
Downloads directly from https://content.eol.org/data/media/
"""
import os
import requests
import time
from pathlib import Path
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')
OUT_DIR = Path("attached_assets/orchid_images")
OUT_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({'User-Agent': 'OrchidContinuum/1.0'})

print("="*80)
print("🌍 EOL DOWNLOADER - Using EOL Content URLs")
print("="*80)

# Connect to database to get EOL URLs already stored
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Get EOL image URLs from database
    cursor.execute("""
        SELECT image_url, taxonomy_id, eol_data_object_id
        FROM orchid_images 
        WHERE image_source = 'EOL' 
        AND download_status = 'pending'
        AND image_url LIKE 'https://content.eol.org%'
        LIMIT 1000
    """)
    
    rows = cursor.fetchall()
    print(f"Found {len(rows)} EOL images to download\n")
    
    downloaded = 0
    for idx, (img_url, tax_id, eol_id) in enumerate(rows, 1):
        try:
            # Download image
            resp = session.get(img_url, timeout=15)
            if resp.status_code == 200:
                filename = f"eol_{eol_id or idx}.jpg"
                filepath = OUT_DIR / filename
                
                with open(filepath, 'wb') as f:
                    f.write(resp.content)
                
                # Update database
                cursor.execute("""
                    UPDATE orchid_images 
                    SET download_status = 'downloaded',
                        local_path = %s,
                        downloaded_at = NOW()
                    WHERE image_url = %s
                """, (str(filepath), img_url))
                conn.commit()
                
                downloaded += 1
                if downloaded % 50 == 0:
                    print(f"✅ Downloaded: {downloaded}/{len(rows)}")
            
            time.sleep(0.1)
            
        except Exception as e:
            print(f"⚠️ Error on image {idx}: {e}")
            continue
    
    print(f"\n🎉 Complete! Downloaded {downloaded} images")
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")

print("="*80)
