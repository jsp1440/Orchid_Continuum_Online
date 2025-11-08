"""
Simple EOL Download: Just download from first manifest quickly
"""
import os
import csv
import requests
import psycopg2
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATABASE_URL = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

print("🌺 EOL SIMPLE DOWNLOAD")
print("=" * 60)

os.makedirs('attached_assets/eol_simple', exist_ok=True)

downloaded = 0
skipped = 0
target = 10000

print(f"Target: {target:,} images from manifest")
print()

manifest_file = 'media_manifest_1.csv'
print(f"Reading {manifest_file}...")

with open(manifest_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        if downloaded >= target:
            break
        
        # Sample every 3rd row for speed
        if downloaded % 3 != 0:
            continue
        
        try:
            content_id = row['EOL content ID']
            page_id = row['EOL page ID']
            url = row['EOL Full-Size Copy URL']
            lic = row.get('License Name', 'unknown')
            owner = row.get('Copyright Owner', '')
            
            if not url:
                continue
            
            # Check exists
            cursor.execute("SELECT COUNT(*) FROM orchid_images WHERE image_url = %s", (url,))
            if cursor.fetchone()[0] > 0:
                skipped += 1
                continue
            
            # Download
            r = requests.get(url, timeout=10, verify=False)
            if r.status_code == 200:
                ext = 'jpg'
                if '.png' in url.lower():
                    ext = 'png'
                
                filename = f"eol_{content_id}.{ext}"
                local_path = f"attached_assets/eol_simple/{filename}"
                
                with open(local_path, 'wb') as img:
                    img.write(r.content)
                
                cursor.execute("""
                    INSERT INTO orchid_images (
                        eol_data_object_id, eol_page_id, image_url, local_path,
                        image_source, image_type, image_license, image_rights_holder
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (content_id, page_id, url, local_path, 'EOL', 'living_photo', lic, owner))
                
                conn.commit()
                downloaded += 1
                
                if downloaded % 100 == 0:
                    print(f"[{downloaded:,}/{target:,}] ✅")
                    
        except Exception as e:
            continue

cursor.close()
conn.close()

print(f"\n✅ Done! Downloaded: {downloaded:,}, Skipped: {skipped:,}")
