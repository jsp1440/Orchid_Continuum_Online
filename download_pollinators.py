"""
Download orchid pollinator images from EOL Zenodo manifest
Target: Bees, hummingbirds, moths, butterflies, flies, wasps, beetles
"""
import os
import csv
import requests
import psycopg2
import glob
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATABASE_URL = os.environ.get('DATABASE_URL')

print("🐝 ORCHID POLLINATOR IMAGE DOWNLOAD")
print("=" * 70)
print("Searching 5.7M EOL images for pollinators...")
print()

# Create table for pollinator images if not exists
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS pollinator_images (
        id SERIAL PRIMARY KEY,
        eol_content_id VARCHAR(50),
        eol_page_id VARCHAR(50),
        image_url TEXT UNIQUE NOT NULL,
        local_path TEXT,
        pollinator_type VARCHAR(100),
        image_source TEXT,
        image_license TEXT,
        image_rights_holder TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

os.makedirs('attached_assets/pollinators', exist_ok=True)

# Pollinator keywords to search for
pollinator_keywords = {
    'bee': ['bee', 'bombus', 'apis', 'xylocopa', 'euglossa', 'anthophora'],
    'hummingbird': ['hummingbird', 'trochilidae', 'colibri'],
    'moth': ['moth', 'sphinx', 'hawk moth', 'lepidoptera'],
    'butterfly': ['butterfly', 'papilio', 'pieris', 'lycaenidae'],
    'fly': ['fly', 'diptera', 'syrphidae', 'tachinidae'],
    'wasp': ['wasp', 'vespidae', 'ichneumon'],
    'beetle': ['beetle', 'coleoptera', 'scarab']
}

downloaded = 0
skipped = 0
target = 10000

print(f"🎯 Target: {target:,} pollinator images")
print(f"📋 Pollinator types: {len(pollinator_keywords)}")
print()

manifest_files = sorted(glob.glob('media_manifest_*.csv'))

# Sample from multiple manifests for diversity
sample_manifests = manifest_files[::3]  # Every 3rd manifest

for manifest_file in sample_manifests[:20]:  # First 20 samples
    if downloaded >= target:
        break
    
    print(f"📖 Scanning {manifest_file}...")
    
    try:
        with open(manifest_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                if downloaded >= target:
                    break
                
                try:
                    content_id = row.get('EOL content ID', '').strip()
                    page_id = row.get('EOL page ID', '').strip()
                    source_url = row.get('Medium Source URL', '').strip().lower()
                    image_url = row.get('EOL Full-Size Copy URL', '').strip()
                    license_name = row.get('License Name', '').strip()
                    copyright_owner = row.get('Copyright Owner', '').strip()
                    
                    if not image_url:
                        continue
                    
                    # Check if URL mentions any pollinator keywords
                    pollinator_type = None
                    for p_type, keywords in pollinator_keywords.items():
                        if any(keyword in source_url for keyword in keywords):
                            pollinator_type = p_type
                            break
                    
                    if not pollinator_type:
                        continue
                    
                    # Check if already exists
                    cursor.execute("""
                        SELECT COUNT(*) FROM pollinator_images 
                        WHERE image_url = %s
                    """, (image_url,))
                    
                    if cursor.fetchone()[0] > 0:
                        skipped += 1
                        continue
                    
                    # Download image
                    response = requests.get(image_url, timeout=10, verify=False)
                    if response.status_code == 200:
                        ext = 'jpg'
                        if '.png' in image_url.lower():
                            ext = 'png'
                        
                        filename = f"{pollinator_type}_{content_id}.{ext}"
                        local_path = f"attached_assets/pollinators/{filename}"
                        
                        with open(local_path, 'wb') as img_file:
                            img_file.write(response.content)
                        
                        # Insert to database
                        cursor.execute("""
                            INSERT INTO pollinator_images (
                                eol_content_id, eol_page_id, image_url, local_path,
                                pollinator_type, image_source, image_license, 
                                image_rights_holder
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            content_id, page_id, image_url, local_path,
                            pollinator_type, 'EOL - Encyclopedia of Life',
                            license_name, copyright_owner
                        ))
                        
                        conn.commit()
                        downloaded += 1
                        
                        if downloaded % 50 == 0:
                            print(f"  [{downloaded:,}/{target:,}] ✅ {pollinator_type}")
                
                except Exception as e:
                    continue
    
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        continue

cursor.close()
conn.close()

print()
print("=" * 70)
print(f"✅ POLLINATOR DOWNLOAD COMPLETE!")
print(f"📥 Downloaded: {downloaded:,}")
print(f"⏭️  Skipped: {skipped:,}")
print("=" * 70)
