"""
Download EOL Orchid Images Directly from Manifest
Uses the extracted manifest files already on Replit
Filters for known orchid page IDs and downloads directly to database
"""
import os
import csv
import requests
import psycopg2
import glob
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATABASE_URL = os.environ.get('DATABASE_URL')

print("🌺 EOL DIRECT DOWNLOAD FROM MANIFEST")
print("=" * 70)

# Load known orchid EOL page IDs from database
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

print("📋 Loading known orchid EOL page IDs from database...")
cursor.execute("""
    SELECT DISTINCT eol_data_object_id 
    FROM orchid_images 
    WHERE eol_data_object_id IS NOT NULL 
    AND eol_data_object_id != ''
""")
orchid_page_ids = set(row[0] for row in cursor.fetchall())
print(f"✅ Loaded {len(orchid_page_ids):,} known orchid page IDs")
print()

# Find manifest files
manifest_files = sorted(glob.glob('media_manifest_*.csv'))
print(f"📦 Found {len(manifest_files)} manifest files")
print()

downloaded = 0
skipped = 0
failed = 0
target = 100000  # Download 100k images

os.makedirs('attached_assets/eol_manifest_orchids', exist_ok=True)

for manifest_file in manifest_files:
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
                    image_url = row.get('EOL Full-Size Copy URL', '').strip()
                    license_name = row.get('License Name', '').strip()
                    copyright_owner = row.get('Copyright Owner', '').strip()
                    
                    if not image_url:
                        continue
                    
                    # Check if this is an orchid (match by content ID or page ID)
                    if content_id not in orchid_page_ids and page_id not in orchid_page_ids:
                        continue
                    
                    # Check if already exists
                    cursor.execute("""
                        SELECT COUNT(*) FROM orchid_images 
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
                        
                        filename = f"eol_manifest_{content_id}.{ext}"
                        local_path = f"attached_assets/eol_manifest_orchids/{filename}"
                        
                        with open(local_path, 'wb') as img_file:
                            img_file.write(response.content)
                        
                        # Insert to database
                        cursor.execute("""
                            INSERT INTO orchid_images (
                                eol_data_object_id, image_url, local_path,
                                image_source, image_type, image_license,
                                image_rights_holder
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            content_id,
                            image_url,
                            local_path,
                            'EOL - Manifest',
                            'living_photo',
                            license_name,
                            copyright_owner
                        ))
                        
                        conn.commit()
                        downloaded += 1
                        
                        if downloaded % 100 == 0:
                            print(f"  [{downloaded:,}/{target:,}] ✅ Downloaded")
                    else:
                        failed += 1
                
                except Exception as e:
                    failed += 1
                    continue
    
    except Exception as e:
        print(f"  ⚠️  Error reading file: {e}")
        continue

cursor.close()
conn.close()

print()
print("=" * 70)
print(f"✅ DOWNLOAD COMPLETE!")
print(f"📥 Downloaded: {downloaded:,}")
print(f"⏭️  Skipped: {skipped:,}")
print(f"❌ Failed: {failed:,}")
print("=" * 70)
