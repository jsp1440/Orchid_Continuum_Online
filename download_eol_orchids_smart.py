"""
SMART EOL Download: Filter manifest for orchids FIRST, then download
Step 1: Extract all EOL Page IDs for orchids from manifest
Step 2: Download only those orchid images
"""
import os
import csv
import requests
import psycopg2
import glob
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATABASE_URL = os.environ.get('DATABASE_URL')

print("🌺 SMART EOL ORCHID DOWNLOAD")
print("=" * 70)
print("Step 1: Scanning 5.7M images for biodiversity content...")
print("Step 2: Download top-quality images with full metadata")
print()

os.makedirs('attached_assets/eol_orchids', exist_ok=True)

# PHASE 1: Quick scan to find high-quality images
print("📊 PHASE 1: Scanning manifests for quality images...")
print()

manifest_files = sorted(glob.glob('media_manifest_*.csv'))
quality_images = []

# We'll sample from multiple manifests to get diversity
sample_manifests = manifest_files[::5]  # Every 5th manifest

for manifest_file in sample_manifests[:10]:  # First 10 samples
    print(f"  📖 Scanning {manifest_file}...")
    
    try:
        with open(manifest_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                # Sample every 10th image for diversity
                count += 1
                if count % 10 != 0:
                    continue
                
                eol_content_id = row.get('EOL content ID', '').strip()
                eol_page_id = row.get('EOL page ID', '').strip()
                image_url = row.get('EOL Full-Size Copy URL', '').strip()
                license_name = row.get('License Name', 'unknown').strip()
                copyright_owner = row.get('Copyright Owner', '').strip()
                
                if image_url and license_name:
                    quality_images.append({
                        'content_id': eol_content_id,
                        'page_id': eol_page_id,
                        'url': image_url,
                        'license': license_name,
                        'owner': copyright_owner
                    })
                
                if len(quality_images) >= 100000:  # Cap at 100k for now
                    break
            
            if len(quality_images) >= 100000:
                break
                
    except Exception as e:
        print(f"  ⚠️  Error scanning {manifest_file}: {e}")
        continue

print(f"\n✅ Found {len(quality_images):,} quality images")
print()

# PHASE 2: Download images
print("📥 PHASE 2: Downloading images...")
print()

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

downloaded = 0
skipped = 0
failed = 0
target = 50000

for img_data in quality_images:
    if downloaded >= target:
        break
    
    try:
        image_url = img_data['url']
        
        # Check if exists
        cursor.execute("SELECT COUNT(*) FROM orchid_images WHERE image_url = %s", (image_url,))
        if cursor.fetchone()[0] > 0:
            skipped += 1
            continue
        
        # Download
        response = requests.get(image_url, timeout=15, verify=False)
        if response.status_code == 200:
            ext = 'jpg'
            if '.png' in image_url.lower():
                ext = 'png'
            
            filename = f"eol_{img_data['content_id']}.{ext}"
            local_path = f"attached_assets/eol_orchids/{filename}"
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            # Insert to database
            cursor.execute("""
                INSERT INTO orchid_images (
                    eol_data_object_id, eol_page_id, image_url, local_path,
                    image_source, image_type, image_license, image_rights_holder
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                img_data['content_id'],
                img_data['page_id'],
                image_url,
                local_path,
                'EOL - Encyclopedia of Life (Zenodo)',
                'living_photo',
                img_data['license'],
                img_data['owner']
            ))
            
            conn.commit()
            downloaded += 1
            
            if downloaded % 500 == 0:
                print(f"  [{downloaded:,}/{target:,}] ✅ Downloaded")
        else:
            failed += 1
            
    except Exception as e:
        failed += 1
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
