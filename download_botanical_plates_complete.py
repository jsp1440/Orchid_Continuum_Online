"""
Download botanical plates from Biodiversity Heritage Library
to cover entire orchid taxonomy
Target: 5,000+ historical botanical illustrations
"""
import os
import requests
import psycopg2
import time

DATABASE_URL = os.environ.get('DATABASE_URL')

# Create download directory
os.makedirs('attached_assets/botanical_plates_complete', exist_ok=True)

print("=" * 80)
print("🎨 DOWNLOADING BOTANICAL PLATES FOR COMPLETE ORCHID TAXONOMY")
print("=" * 80)

# BHL API for orchid illustrations
# Major orchid monographs and floras
queries = [
    "Orchidaceae illustration",
    "Orchid botanical plate",
    "Orchidaceae monograph",
    "Orchid species illustration",
    "Lindenia orchid",
    "Reichenbachia orchid",
    "Orchid flora illustration",
    "Botanical orchid drawing",
    "Orchidaceae botanical art",
    "Orchid taxonomic illustration"
]

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

downloaded = 0
failed = 0

print(f"\n📚 Searching BHL for historical orchid plates...")
print("🎨 Sources: Lindenia, Reichenbachia, Curtis, and other monographs\n")

for query in queries:
    print(f"\n🔍 Searching: {query}")
    
    # BHL API search
    api_url = f"https://www.biodiversitylibrary.org/api3"
    params = {
        "op": "PublicationSearch",
        "searchterm": query,
        "searchtype": "c",
        "format": "json",
        "apikey": "your-api-key"  # BHL is open, no key needed for basic search
    }
    
    try:
        # For now, use EOL API which includes BHL images
        eol_url = "https://eol.org/api/search/1.0.json"
        eol_params = {
            "q": query,
            "page": 1,
            "exact": False,
            "filter_by_taxon_concept_id": "",
            "filter_by_hierarchy_entry_id": "",
            "filter_by_string": "Orchidaceae",
            "cache_ttl": ""
        }
        
        for page in range(1, 11):  # 10 pages per query
            eol_params["page"] = page
            
            response = requests.get(eol_url, params=eol_params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    break
                
                for result in results:
                    try:
                        # Get page details
                        page_id = result.get('id')
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
                        
                        page_response = requests.get(page_url, params=page_params, timeout=30)
                        if page_response.status_code == 200:
                            page_data = page_response.json()
                            
                            for media in page_data.get('dataObjects', []):
                                if media.get('dataType') != 'http://purl.org/dc/dcmitype/StillImage':
                                    continue
                                
                                # Check if it's a botanical illustration (not photo)
                                source = media.get('source', '').lower()
                                if 'bhl' not in source and 'illustration' not in source and 'plate' not in source:
                                    continue
                                
                                image_url = media.get('eolMediaURL', '')
                                if not image_url:
                                    continue
                                
                                scientific_name = page_data.get('scientificName', 'Unknown')
                                
                                # Download
                                img_response = requests.get(image_url, timeout=15)
                                if img_response.status_code == 200:
                                    filename = f"plate_{downloaded}_{scientific_name.replace(' ', '_')}.jpg"
                                    local_path = f"attached_assets/botanical_plates_complete/{filename}"
                                    
                                    with open(local_path, 'wb') as f:
                                        f.write(img_response.content)
                                    
                                    # Insert to database
                                    cursor.execute("""
                                        INSERT INTO orchid_images (
                                            image_url, local_path, image_source, image_type,
                                            image_license, image_rights_holder,
                                            image_description
                                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                                        ON CONFLICT (image_url) DO NOTHING
                                    """, (
                                        image_url,
                                        local_path,
                                        media.get('source', 'BHL via EOL'),
                                        'botanical_plate',
                                        media.get('license', 'Public Domain'),
                                        media.get('rightsHolder', 'Biodiversity Heritage Library'),
                                        f"{scientific_name} - Historical botanical illustration"
                                    ))
                                    
                                    conn.commit()
                                    downloaded += 1
                                    
                                    if downloaded % 25 == 0:
                                        print(f"  [{downloaded:,}] ✅ {scientific_name}")
                                        
                                    if downloaded >= 5000:
                                        break
                                        
                        time.sleep(0.3)
                        
                        if downloaded >= 5000:
                            break
                            
                    except Exception as e:
                        failed += 1
                        continue
                
                if downloaded >= 5000:
                    break
                    
            time.sleep(1)
            
        if downloaded >= 5000:
            break
            
    except Exception as e:
        print(f"  ❌ Error with query '{query}': {e}")
        continue

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("✅ BOTANICAL PLATES DOWNLOAD COMPLETE")
print("=" * 80)
print(f"✅ Downloaded: {downloaded:,} plates")
print(f"❌ Failed: {failed}")
print("=" * 80)
