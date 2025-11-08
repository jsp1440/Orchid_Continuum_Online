"""
Download herbarium specimens from iDigBio
Target: 10,000 specimens from major herbaria worldwide
"""
import os
import requests
import psycopg2
import time

DATABASE_URL = os.environ.get('DATABASE_URL')
os.makedirs('attached_assets/idigbio_herbarium', exist_ok=True)

print("🔬 iDIGBIO HERBARIUM DOWNLOAD")
print("=" * 60)

api_url = "https://search.idigbio.org/v2/search/records/"

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

downloaded = 0
failed = 0
skipped = 0
target = 10000

print(f"🎯 Target: {target:,} specimens\n")

for offset in range(0, target, 100):
    try:
        params = {
            "rq": {
                "family": "Orchidaceae",
                "hasImage": True,
                "basisofrecord": "preservedspecimen"
            },
            "limit": 100,
            "offset": offset
        }
        
        response = requests.post(api_url, json=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                break
            
            for item in items:
                try:
                    record = item.get('indexTerms', {})
                    media_list = item.get('mediarecords', [])
                    
                    if not media_list:
                        continue
                    
                    image_url = media_list[0].get('accessuri', '')
                    if not image_url:
                        continue
                    
                    # Download
                    img_response = requests.get(image_url, timeout=15)
                    if img_response.status_code == 200:
                        genus = record.get('genus', 'Unknown')
                        filename = f"idigbio_{downloaded}_{genus}.jpg"
                        local_path = f"attached_assets/idigbio_herbarium/{filename}"
                        
                        with open(local_path, 'wb') as f:
                            f.write(img_response.content)
                        
                        # Check if already exists
                        cursor.execute("SELECT COUNT(*) FROM orchid_images WHERE image_url = %s", (image_url,))
                        if cursor.fetchone()[0] > 0:
                            skipped += 1
                            continue
                        
                        # Insert to database  
                        cursor.execute("""
                            INSERT INTO orchid_images (
                                image_url, local_path, image_source, image_type,
                                image_license, country, institution_code,
                                herbarium_catalog_number, collection_year,
                                image_description
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            image_url,
                            local_path,
                            'iDigBio',
                            'herbarium_sheet',
                            record.get('license', 'Unknown'),
                            record.get('country', ''),
                            record.get('institutioncode', ''),
                            record.get('catalognumber', ''),
                            int(record.get('year')) if record.get('year') else None,
                            f"{record.get('scientificname', 'Unknown')} - {record.get('institutioncode', 'Unknown')}"
                        ))
                        
                        if cursor.rowcount > 0:
                            conn.commit()
                            downloaded += 1
                            
                            if downloaded % 50 == 0:
                                print(f"  [{downloaded:,}/{target:,}] ✅ {record.get('genus', 'Unknown')}")
                    else:
                        failed += 1
                        
                except Exception as e:
                    failed += 1
                    continue
            
            time.sleep(0.5)
        else:
            time.sleep(2)
            
    except Exception as e:
        print(f"  ❌ Error at offset {offset}: {e}")
        time.sleep(2)

cursor.close()
conn.close()

print(f"\n✅ iDigBio download complete: {downloaded:,} specimens")
