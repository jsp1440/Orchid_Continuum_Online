"""
Download pollinator images by searching ALL manifest fields for keywords
"""
import os
import csv
import requests
import psycopg2
import glob
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATABASE_URL = os.environ.get('DATABASE_URL')

print("🐝 POLLINATOR IMAGE DOWNLOAD (Fixed)")
print("=" * 70)

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

# Search keywords
keywords = {
    'bee': ['bee', 'bombus', 'apis', 'bumble'],
    'hummingbird': ['hummingbird', 'trochil', 'colibri'],
    'moth': ['moth', 'sphinx', 'hawk-moth'],
    'butterfly': ['butterfly', 'swallowtail', 'monarch'],
    'fly': ['fly', 'hover', 'syrphid'],
    'wasp': ['wasp', 'hornet'],
    'beetle': ['beetle', 'scarab']
}

downloaded = 0
target = 5000

print(f"🎯 Target: {target:,} images\n")

# Search first 5 manifests thoroughly
for manifest_num in range(1, 6):
    if downloaded >= target:
        break
    
    manifest_file = f'media_manifest_{manifest_num}.csv'
    print(f"📖 Searching {manifest_file}...")
    
    try:
        with open(manifest_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                if downloaded >= target:
                    break
                
                # Convert entire row to lowercase string for searching
                row_text = ' '.join(str(v).lower() for v in row.values())
                
                # Check for pollinator keywords
                pollinator_type = None
                for p_type, kw_list in keywords.items():
                    if any(kw in row_text for kw in kw_list):
                        pollinator_type = p_type
                        break
                
                if not pollinator_type:
                    continue
                
                try:
                    content_id = row['EOL content ID']
                    page_id = row['EOL page ID']
                    url = row['EOL Full-Size Copy URL']
                    lic = row.get('License Name', 'unknown')
                    owner = row.get('Copyright Owner', '')
                    
                    if not url:
                        continue
                    
                    # Check if exists
                    cursor.execute("SELECT COUNT(*) FROM pollinator_images WHERE image_url = %s", (url,))
                    if cursor.fetchone()[0] > 0:
                        continue
                    
                    # Download
                    r = requests.get(url, timeout=8, verify=False)
                    if r.status_code == 200:
                        ext = 'jpg' if '.jpg' in url.lower() else 'png'
                        filename = f"{pollinator_type}_{content_id}.{ext}"
                        local_path = f"attached_assets/pollinators/{filename}"
                        
                        with open(local_path, 'wb') as img:
                            img.write(r.content)
                        
                        cursor.execute("""
                            INSERT INTO pollinator_images (
                                eol_content_id, eol_page_id, image_url, local_path,
                                pollinator_type, image_source, image_license,
                                image_rights_holder
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (content_id, page_id, url, local_path, pollinator_type,
                              'EOL', lic, owner))
                        
                        conn.commit()
                        downloaded += 1
                        
                        if downloaded % 100 == 0:
                            print(f"  [{downloaded:,}/{target:,}] ✅ {pollinator_type}")
                
                except Exception as e:
                    continue
    
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        continue

cursor.close()
conn.close()

print(f"\n{'='*70}")
print(f"✅ Downloaded {downloaded:,} pollinator images!")
