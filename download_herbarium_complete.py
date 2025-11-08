"""
Download herbarium specimens from iDigBio to cover entire orchid taxonomy
Target: 10,000+ herbarium sheets from major institutions
"""
import os
import requests
import psycopg2
import time
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

# Create download directory
os.makedirs('attached_assets/herbarium_complete', exist_ok=True)

print("=" * 80)
print("🔬 DOWNLOADING HERBARIUM SHEETS FOR COMPLETE ORCHID TAXONOMY")
print("=" * 80)

# iDigBio API - Orchidaceae family herbarium specimens
# Target diverse genera to cover taxonomy
api_url = "https://search.idigbio.org/v2/search/records/"

# Query for Orchidaceae herbarium specimens with images
params = {
    "rq": {
        "family": "Orchidaceae",
        "hasImage": True,
        "basisofrecord": "preservedspecimen"
    },
    "limit": 100,
    "offset": 0
}

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

downloaded = 0
failed = 0
target = 10000

print(f"\n🎯 Target: {target:,} herbarium specimens")
print("📡 Downloading from iDigBio (major herbaria worldwide)...\n")

for offset in range(0, target, 100):
    params["offset"] = offset
    
    try:
        response = requests.post(api_url, json=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                print(f"\n✅ No more records found at offset {offset}")
                break
            
            for item in items:
                try:
                    record = item.get('indexTerms', {})
                    media = item.get('mediarecords', [])
                    
                    if not media:
                        continue
                    
                    # Get first image
                    image_url = media[0].get('accessuri', '')
                    if not image_url:
                        continue
                    
                    scientific_name = record.get('scientificname', 'Unknown')
                    genus = record.get('genus', '')
                    species = record.get('specificepithet', '')
                    
                    # Download image
                    img_response = requests.get(image_url, timeout=15)
                    if img_response.status_code == 200:
                        filename = f"herbarium_{offset + len(items)}_{genus}_{species}.jpg"
                        local_path = f"attached_assets/herbarium_complete/{filename}"
                        
                        with open(local_path, 'wb') as f:
                            f.write(img_response.content)
                        
                        # Insert to database
                        cursor.execute("""
                            INSERT INTO orchid_images (
                                image_url, local_path, image_source, image_type,
                                image_license, country, state_province,
                                locality, institution_code,
                                herbarium_catalog_number, collection_year,
                                image_description
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (image_url) DO NOTHING
                        """, (
                            image_url,
                            local_path,
                            'iDigBio',
                            'herbarium_sheet',
                            record.get('license', 'Unknown'),
                            record.get('country', ''),
                            record.get('stateprovince', ''),
                            record.get('locality', ''),
                            record.get('institutioncode', ''),
                            record.get('catalognumber', ''),
                            record.get('year', None),
                            f"{scientific_name} - Herbarium specimen from {record.get('institutioncode', 'Unknown institution')}"
                        ))
                        
                        conn.commit()
                        downloaded += 1
                        
                        if downloaded % 50 == 0:
                            print(f"  [{downloaded:,}/{target:,}] ✅ {scientific_name}")
                            print(f"    Latest: {genus} {species} - {record.get('institutioncode', '')}")
                    else:
                        failed += 1
                        
                except Exception as e:
                    failed += 1
                    continue
            
            time.sleep(0.5)  # Be polite
        else:
            print(f"  ❌ API error at offset {offset}: {response.status_code}")
            time.sleep(2)
            
    except Exception as e:
        print(f"  ❌ Error at offset {offset}: {e}")
        time.sleep(2)

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("✅ HERBARIUM DOWNLOAD COMPLETE")
print("=" * 80)
print(f"✅ Downloaded: {downloaded:,} specimens")
print(f"❌ Failed: {failed}")
print("=" * 80)
