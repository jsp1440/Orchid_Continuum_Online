"""
Complete GBIF Orchid Download
Download images for ALL 33,494 orchid species from GBIF
Target: ~60 images per species = 2 million total images
"""
import os
import requests
import psycopg2
import time
import json
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

print("🌺 COMPLETE GBIF ORCHID DOWNLOAD")
print("=" * 70)
print("Target: 2,000,000 images across ALL orchid species")
print("=" * 70)
print()

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Create download tracking table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS gbif_download_progress (
        id SERIAL PRIMARY KEY,
        taxonomy_id INTEGER UNIQUE,
        genus VARCHAR(255),
        species VARCHAR(255),
        images_downloaded INTEGER DEFAULT 0,
        last_attempt TIMESTAMP,
        status VARCHAR(50),
        gbif_key VARCHAR(50)
    )
""")
conn.commit()

# Get all orchid species from taxonomy
cursor.execute("""
    SELECT id, genus, species, scientific_name
    FROM orchid_taxonomy
    WHERE genus IS NOT NULL 
    AND species IS NOT NULL
    ORDER BY genus, species
""")
all_species = cursor.fetchall()

print(f"📊 Total Species in Taxonomy: {len(all_species):,}")
print()

# Check progress
cursor.execute("SELECT COUNT(*) FROM gbif_download_progress WHERE status = 'completed'")
completed_count = cursor.fetchone()[0]
print(f"✅ Already Completed: {completed_count:,} species")
print(f"⏳ Remaining: {len(all_species) - completed_count:,} species")
print()

os.makedirs('attached_assets/gbif_complete', exist_ok=True)

total_downloaded = 0
target_per_species = 60  # ~60 images per species = 2M total
batch_size = 100

gbif_api = "https://api.gbif.org/v1/occurrence/search"

for idx, (taxonomy_id, genus, species, sci_name) in enumerate(all_species):
    # Check if already completed
    cursor.execute("""
        SELECT images_downloaded, status 
        FROM gbif_download_progress 
        WHERE taxonomy_id = %s
    """, (taxonomy_id,))
    
    progress = cursor.fetchone()
    if progress and progress[1] == 'completed':
        total_downloaded += progress[0]
        continue
    
    print(f"[{idx+1:,}/{len(all_species):,}] {sci_name}")
    
    try:
        # Query GBIF for this species with images
        params = {
            'scientificName': sci_name,
            'mediaType': 'StillImage',
            'hasCoordinate': 'true',
            'limit': 300  # Get up to 300 results
        }
        
        response = requests.get(gbif_api, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"  ⚠️  GBIF API error: {response.status_code}")
            continue
        
        data = response.json()
        results = data.get('results', [])
        
        if not results:
            # Mark as completed with 0 images
            cursor.execute("""
                INSERT INTO gbif_download_progress (taxonomy_id, genus, species, images_downloaded, status, last_attempt)
                VALUES (%s, %s, %s, 0, 'no_images', NOW())
                ON CONFLICT (taxonomy_id) DO UPDATE SET
                    images_downloaded = 0,
                    status = 'no_images',
                    last_attempt = NOW()
            """, (taxonomy_id, genus, species))
            conn.commit()
            print(f"  ⏭️  No images available")
            continue
        
        downloaded_this_species = 0
        
        for occurrence in results[:target_per_species]:
            if downloaded_this_species >= target_per_species:
                break
            
            try:
                # Get image URL from media
                media = occurrence.get('media', [])
                if not media:
                    continue
                
                image_url = media[0].get('identifier')
                if not image_url:
                    continue
                
                # Check if already exists
                cursor.execute("""
                    SELECT COUNT(*) FROM orchid_images 
                    WHERE image_url = %s
                """, (image_url,))
                
                if cursor.fetchone()[0] > 0:
                    continue
                
                # Download image
                img_response = requests.get(image_url, timeout=15)
                if img_response.status_code == 200:
                    ext = 'jpg'
                    if '.png' in image_url.lower():
                        ext = 'png'
                    
                    filename = f"gbif_{taxonomy_id}_{downloaded_this_species}.{ext}"
                    local_path = f"attached_assets/gbif_complete/{filename}"
                    
                    with open(local_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    # Insert to database with taxonomy link
                    cursor.execute("""
                        INSERT INTO orchid_images (
                            taxonomy_id, image_url, local_path, image_source, 
                            image_type, image_license, image_rights_holder,
                            latitude, longitude, country, locality,
                            observer_name, observation_date, image_description
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        taxonomy_id,
                        image_url,
                        local_path,
                        'GBIF',
                        'living_photo',
                        occurrence.get('license', 'Unknown'),
                        occurrence.get('rightsHolder', 'Unknown'),
                        occurrence.get('decimalLatitude'),
                        occurrence.get('decimalLongitude'),
                        occurrence.get('country'),
                        occurrence.get('locality'),
                        occurrence.get('recordedBy'),
                        occurrence.get('eventDate'),
                        f"{sci_name} - GBIF occurrence {occurrence.get('gbifID')}"
                    ))
                    
                    conn.commit()
                    downloaded_this_species += 1
                    total_downloaded += 1
                    
            except Exception as e:
                continue
        
        # Update progress
        cursor.execute("""
            INSERT INTO gbif_download_progress (taxonomy_id, genus, species, images_downloaded, status, last_attempt)
            VALUES (%s, %s, %s, %s, 'completed', NOW())
            ON CONFLICT (taxonomy_id) DO UPDATE SET
                images_downloaded = %s,
                status = 'completed',
                last_attempt = NOW()
        """, (taxonomy_id, genus, species, downloaded_this_species, downloaded_this_species))
        conn.commit()
        
        if downloaded_this_species > 0:
            print(f"  ✅ {downloaded_this_species} images | Total: {total_downloaded:,}")
        else:
            print(f"  ⏭️  0 images found")
        
        # Progress update every 100 species
        if (idx + 1) % 100 == 0:
            print()
            print(f"{'='*70}")
            print(f"PROGRESS: {idx+1:,}/{len(all_species):,} species processed")
            print(f"IMAGES: {total_downloaded:,} downloaded")
            print(f"{'='*70}")
            print()
        
        time.sleep(0.2)  # Rate limiting
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        continue

cursor.close()
conn.close()

print()
print("=" * 70)
print(f"✅ DOWNLOAD COMPLETE!")
print(f"📥 Total Images Downloaded: {total_downloaded:,}")
print(f"📊 Species Processed: {len(all_species):,}")
print("=" * 70)
