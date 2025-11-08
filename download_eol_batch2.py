"""
Download EOL Batch 2: Additional 95,000 orchid images
Continues from where the first 95,000 left off
"""
import os
import requests
import psycopg2
import time
import csv
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATABASE_URL = os.environ.get('DATABASE_URL')
os.makedirs('attached_assets/eol_batch2', exist_ok=True)

print("🌍 EOL BATCH 2 DOWNLOAD")
print("=" * 60)
print("Target: 95,000 additional EOL images (95,001-190,000)")
print("=" * 60)

# EOL API endpoint
eol_api = "https://eol.org/api/search/1.0.json"

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Get list of orchid species we need images for
cursor.execute("""
    SELECT genus, species, scientific_name
    FROM (
        SELECT DISTINCT genus, species, scientific_name
        FROM orchid_taxonomy 
        WHERE genus IS NOT NULL 
        AND species IS NOT NULL
    ) AS distinct_species
    ORDER BY RANDOM()
    LIMIT 5000
""")
species_list = cursor.fetchall()

downloaded = 0
failed = 0
target = 95000
start_offset = 95001

# Open CSV for metadata
csv_file = open('EOL_BATCH2_COMPLETE.csv', 'w', newline='', encoding='utf-8')
csv_writer = csv.writer(csv_file)
csv_writer.writerow([
    'Image_ID', 'EOL_Page_ID', 'Image_URL', 'Scientific_Name',
    'Genus', 'Species', 'License', 'Rights_Holder', 'Source',
    'Description', 'Local_Path'
])

print(f"\n📚 Searching {len(species_list):,} species for images...\n")

for genus, species, sci_name in species_list:
    if downloaded >= target:
        break
    
    try:
        # Search EOL for this species
        search_query = f"{genus} {species}"
        
        params = {
            "q": search_query,
            "page": 1,
            "exact": True,
            "filter_by_taxon_concept_id": "",
            "filter_by_hierarchy_entry_id": "",
            "filter_by_string": "",
            "cache_ttl": ""
        }
        
        response = requests.get(eol_api, params=params, timeout=30, verify=False)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            for result in results[:5]:  # Max 5 results per search
                if downloaded >= target:
                    break
                
                try:
                    page_id = result.get('id')
                    
                    # Get page details with images
                    page_url = f"https://eol.org/api/pages/1.0/{page_id}.json"
                    page_params = {
                        "images_per_page": 10,
                        "videos_per_page": 0,
                        "sounds_per_page": 0,
                        "text_per_page": 0,
                        "iucn": False,
                        "subjects": "overview",
                        "licenses": "all",
                        "details": True,
                        "common_names": False,
                        "synonyms": False,
                        "references": False,
                        "taxonomy": True,
                        "vetted": 0,
                        "cache_ttl": ""
                    }
                    
                    page_response = requests.get(page_url, params=page_params, timeout=30, verify=False)
                    if page_response.status_code == 200:
                        page_data = page_response.json()
                        
                        for media in page_data.get('dataObjects', []):
                            if downloaded >= target:
                                break
                                
                            if media.get('dataType') != 'http://purl.org/dc/dcmitype/StillImage':
                                continue
                            
                            image_url = media.get('eolMediaURL', '')
                            if not image_url:
                                continue
                            
                            # Download image
                            img_response = requests.get(image_url, timeout=15, verify=False)
                            if img_response.status_code == 200:
                                image_id = start_offset + downloaded
                                filename = f"eol_batch2_{image_id}_{genus}_{species}.jpg"
                                local_path = f"attached_assets/eol_batch2/{filename}"
                                
                                with open(local_path, 'wb') as f:
                                    f.write(img_response.content)
                                
                                # Check if already exists
                                cursor.execute("SELECT COUNT(*) FROM orchid_images WHERE image_url = %s", (image_url,))
                                if cursor.fetchone()[0] > 0:
                                    continue
                                
                                # Insert to database
                                cursor.execute("""
                                    INSERT INTO orchid_images (
                                        eol_data_object_id, image_url, local_path,
                                        image_source, image_type, image_license,
                                        image_rights_holder, image_description
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                """, (
                                    media.get('identifier', ''),
                                    image_url,
                                    local_path,
                                    'EOL - Encyclopedia of Life',
                                    'living_photo',
                                    media.get('license', 'Unknown'),
                                    media.get('rightsHolder', 'Unknown'),
                                    f"{sci_name} - {media.get('description', 'Photo')}"
                                ))
                                
                                if cursor.rowcount > 0:
                                    conn.commit()
                                    downloaded += 1
                                    
                                    # Write to CSV
                                    csv_writer.writerow([
                                        image_id,
                                        page_id,
                                        image_url,
                                        sci_name,
                                        genus,
                                        species,
                                        media.get('license', ''),
                                        media.get('rightsHolder', ''),
                                        media.get('source', ''),
                                        media.get('description', ''),
                                        local_path
                                    ])
                                    
                                    if downloaded % 100 == 0:
                                        csv_file.flush()
                                        print(f"  [{downloaded:,}/{target:,}] ✅ {sci_name}")
                            else:
                                failed += 1
                                
                except Exception as e:
                    failed += 1
                    continue
                
                time.sleep(0.3)
                
        time.sleep(0.2)
        
    except Exception as e:
        failed += 1
        continue

csv_file.close()
cursor.close()
conn.close()

print(f"\n✅ EOL Batch 2 complete: {downloaded:,} images")
print(f"📄 Metadata saved to: EOL_BATCH2_COMPLETE.csv")
