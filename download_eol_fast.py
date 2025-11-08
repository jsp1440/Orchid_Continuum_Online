"""
FAST EOL Download: Batch insert without checking duplicates
Let the database handle duplicates via error handling
"""
import os
import csv
import requests
import psycopg2
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATABASE_URL = os.environ.get('DATABASE_URL')

print("🌺 FAST EOL DOWNLOAD FROM ZENODO MANIFEST")
print("=" * 60)

os.makedirs('attached_assets/eol_fast', exist_ok=True)

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

downloaded = 0
skipped = 0
target = 50000

print(f"🎯 Target: {target:,} images")
print(f"📁 Reading: media_manifest_1.csv")
print()

with open('media_manifest_1.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    for idx, row in enumerate(reader):
        if downloaded >= target:
            break
        
        # Process every 2nd row for diversity
        if idx % 2 != 0:
            continue
        
        try:
            content_id = row['EOL content ID']
            page_id = row['EOL page ID']
            url = row['EOL Full-Size Copy URL']
            lic = row.get('License Name', 'unknown')
            owner = row.get('Copyright Owner', '')
            
            if not url:
                continue
            
            # Download first, insert later
            r = requests.get(url, timeout=8, verify=False)
            if r.status_code != 200:
                continue
            
            ext = 'jpg'
            if '.png' in url.lower():
                ext = 'png'
            
            filename = f"eol_{content_id}.{ext}"
            local_path = f"attached_assets/eol_fast/{filename}"
            
            with open(local_path, 'wb') as img:
                img.write(r.content)
            
            # Try to insert - skip if duplicate
            try:
                cursor.execute("""
                    INSERT INTO orchid_images (
                        eol_data_object_id, eol_page_id, image_url, local_path,
                        image_source, image_type, image_license, image_rights_holder
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (content_id, page_id, url, local_path, 'EOL - Zenodo', 'living_photo', lic, owner))
                conn.commit()
                downloaded += 1
                
                if downloaded % 200 == 0:
                    print(f"  [{downloaded:,}/{target:,}] ✅ {downloaded:,} downloaded")
                    
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                skipped += 1
                os.remove(local_path)  # Remove duplicate file
                
        except Exception as e:
            conn.rollback()
            continue

cursor.close()
conn.close()

print(f"\n{'='*60}")
print(f"✅ COMPLETE!")
print(f"📥 Downloaded: {downloaded:,}")
print(f"⏭️  Skipped: {skipped:,}")
