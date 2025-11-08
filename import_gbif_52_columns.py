"""
Import 9,774 GBIF orchid images from ORCHID_COMPLETE_52_COLUMNS.csv
Downloads images and adds them to the database with full metadata
"""
import os
import csv
import requests
import psycopg2
from pathlib import Path
import time

DATABASE_URL = os.environ.get('DATABASE_URL')

# Create download directory
os.makedirs('attached_assets/gbif_52_columns', exist_ok=True)

print("=" * 80)
print("🌺 IMPORTING 9,774 GBIF ORCHID IMAGES WITH 52-COLUMN METADATA")
print("=" * 80)

# Read CSV
with open('attached_assets/ORCHID_COMPLETE_52_COLUMNS_1762231249570.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"\n✅ Loaded {len(rows):,} image records from CSV")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

imported = 0
skipped = 0
failed = 0

for idx, row in enumerate(rows, 1):
    try:
        image_url = row.get('Image_URL', '').strip()
        scientific_name = row.get('Scientific_Name', '').strip()
        
        if not image_url or not scientific_name:
            skipped += 1
            continue
        
        # Download image
        local_filename = f"gbif_{idx}.jpg"
        local_path = f"attached_assets/gbif_52_columns/{local_filename}"
        
        # Skip if already downloaded
        if os.path.exists(local_path):
            skipped += 1
            if idx % 100 == 0:
                print(f"  [{idx:,}/{len(rows):,}] ⏭️  Already exists: {scientific_name}")
            continue
        
        # Download
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            with open(local_path, 'wb') as img_file:
                img_file.write(response.content)
            
            # Insert to database with transaction management
            try:
                # Prepare date - handle empty strings
                obs_date = row.get('Observation_Date', '').strip()
                obs_date = obs_date if obs_date else None
                
                # Check if image already exists
                cursor.execute("SELECT COUNT(*) FROM orchid_images WHERE image_url = %s", (image_url,))
                if cursor.fetchone()[0] > 0:
                    skipped += 1
                    continue
                
                cursor.execute("""
                    INSERT INTO orchid_images (
                        image_url, local_path, image_source, image_type,
                        image_license, image_rights_holder,
                        latitude, longitude, country, state_province,
                        locality, observer_name, observation_date,
                        image_description
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    image_url,
                    local_path,
                    row.get('Image_Source', 'GBIF'),
                    'living_photo',
                    row.get('Image_License', ''),
                    row.get('Observer_Name', ''),
                    float(row.get('Latitude', 0)) if row.get('Latitude') else None,
                    float(row.get('Longitude', 0)) if row.get('Longitude') else None,
                    row.get('Country', ''),
                    row.get('State_Province', ''),
                    row.get('Locality', ''),
                    row.get('Observer_Name', ''),
                    obs_date,
                    f"{scientific_name} - {row.get('Country', 'Unknown location')}"
                ))
                
                conn.commit()
                imported += 1
                
                if idx % 50 == 0:
                    print(f"  [{idx:,}/{len(rows):,}] ✅ {imported:,} imported | ❌ {failed} failed | ⏭️  {skipped} skipped")
                    print(f"    Latest: {scientific_name[:50]}")
                    
            except Exception as db_error:
                conn.rollback()
                failed += 1
                print(f"  ❌ DB Error at row {idx}: {db_error}")
        else:
            failed += 1
            
    except Exception as e:
        conn.rollback()
        failed += 1
        if idx % 100 == 0:
            print(f"  ❌ Error at row {idx}: {e}")
    
    time.sleep(0.1)  # Be polite to servers

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("✅ IMPORT COMPLETE!")
print("=" * 80)
print(f"✅ Successfully imported: {imported:,}")
print(f"⏭️  Skipped (already exist): {skipped:,}")
print(f"❌ Failed: {failed}")
print(f"📊 Total processed: {len(rows):,}")
print("=" * 80)
