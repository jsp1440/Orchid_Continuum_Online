"""
Simple Manifest Processor - No APIs, Just Read CSV and Download
"""
import csv
import requests
import psycopg2
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATABASE_URL = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Load known orchid page IDs
cursor.execute("""
    SELECT DISTINCT eol_data_object_id 
    FROM orchid_images 
    WHERE eol_data_object_id IS NOT NULL
""")
orchid_ids = set(row[0] for row in cursor.fetchall())

print(f"Known orchid IDs: {len(orchid_ids):,}")
print("Processing media_manifest_1.csv...")

os.makedirs('attached_assets/eol_direct', exist_ok=True)

downloaded = 0
checked = 0

with open('media_manifest_1.csv', 'r') as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        checked += 1
        
        content_id = row['EOL content ID']
        page_id = row['EOL page ID']
        url = row['EOL Full-Size Copy URL']
        
        # Check if orchid
        if content_id not in orchid_ids and page_id not in orchid_ids:
            continue
        
        # Check if exists
        cursor.execute("SELECT COUNT(*) FROM orchid_images WHERE image_url = %s", (url,))
        if cursor.fetchone()[0] > 0:
            continue
        
        # Download
        try:
            r = requests.get(url, timeout=8, verify=False)
            if r.status_code == 200:
                filename = f"eol_{content_id}.jpg"
                local_path = f"attached_assets/eol_direct/{filename}"
                
                with open(local_path, 'wb') as img:
                    img.write(r.content)
                
                cursor.execute("""
                    INSERT INTO orchid_images (
                        eol_data_object_id, image_url, local_path,
                        image_source, image_type, image_license, image_rights_holder
                    ) VALUES (%s, %s, %s, 'EOL-Manifest', 'living_photo', %s, %s)
                """, (content_id, url, local_path, row.get('License Name'), row.get('Copyright Owner')))
                
                conn.commit()
                downloaded += 1
                
                if downloaded % 10 == 0:
                    print(f"  Downloaded: {downloaded}")
                
                if downloaded >= 100:  # Test with 100 first
                    break
        except:
            continue
        
        if checked % 10000 == 0:
            print(f"  Checked: {checked:,}")

print(f"\nDone! Downloaded: {downloaded}, Checked: {checked:,}")
cursor.close()
conn.close()
