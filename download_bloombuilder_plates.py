"""
Download botanical illustration plates from EOL for BloomBuilder species
Focus on BHL (Biodiversity Heritage Library) historical plates
"""
import os
import requests
import time
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')

# EOL API
EOL_API = "https://eol.org/api/search/1.0.json"
EOL_PAGES_API = "https://eol.org/api/pages/1.0.json"

def search_eol_species(scientific_name):
    """Search EOL for a species page"""
    try:
        response = requests.get(EOL_API, params={'q': scientific_name}, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        results = data.get('results', [])
        if results:
            return results[0].get('id')  # Return first page ID
        return None
    except:
        return None

def get_eol_images(page_id, taxonomy_id, scientific_name):
    """Get images for an EOL page, focusing on botanical illustrations"""
    try:
        response = requests.get(EOL_PAGES_API, params={
            'id': page_id,
            'images_per_page': 20,
            'images_page': 1,
            'details': 'true'
        }, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        objects = data.get('dataObjects', [])
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        saved = 0
        for obj in objects:
            # Only get images
            if obj.get('dataType') != 'http://purl.org/dc/dcmitype/StillImage':
                continue
            
            image_url = obj.get('eolMediaURL') or obj.get('mediaURL')
            if not image_url:
                continue
            
            # Check for BHL source (historical plates)
            source = obj.get('source', '')
            rights_holder = obj.get('rightsHolder', '')
            
            is_plate = 'biodiversity' in source.lower() or 'bhl' in source.lower() or 'heritage' in rights_holder.lower()
            image_type = 'botanical_plate' if is_plate else 'living_photo'
            
            # Check if exists
            cursor.execute("SELECT id FROM orchid_images WHERE image_url = %s", (image_url,))
            if cursor.fetchone():
                continue
            
            # Insert
            try:
                cursor.execute("""
                    INSERT INTO orchid_images (
                        taxonomy_id, image_url, image_source, image_type,
                        eol_data_object_id, image_rights_holder,
                        image_license, image_description
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    taxonomy_id,
                    image_url,
                    'EOL - Encyclopedia of Life',
                    image_type,
                    obj.get('identifier', ''),
                    rights_holder,
                    obj.get('license', ''),
                    f"{scientific_name} - EOL plate"
                ))
                conn.commit()
                saved += 1
                symbol = "🎨" if is_plate else "📸"
                print(f"    {symbol} Saved {image_type}: {saved}")
            except Exception as e:
                conn.rollback()
        
        cursor.close()
        conn.close()
        return saved
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return 0

# Get species
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()
cursor.execute("""
    SELECT bs.genus || ' ' || bs.species as name, ot.id
    FROM bloombuilder_species bs
    JOIN orchid_taxonomy ot ON ot.scientific_name = bs.genus || ' ' || bs.species
""")
species = cursor.fetchall()
cursor.close()
conn.close()

print("=" * 70)
print("🎨 DOWNLOADING BOTANICAL PLATES FROM EOL")
print("=" * 70)

total_saved = 0
for name, taxonomy_id in species:
    print(f"\n🔍 {name}")
    
    # Search EOL
    page_id = search_eol_species(name)
    if not page_id:
        print(f"  ❌ Not found on EOL")
        continue
    
    print(f"  ✅ Found EOL page: {page_id}")
    
    # Get images
    saved = get_eol_images(page_id, taxonomy_id, name)
    print(f"  📊 Saved: {saved} images")
    total_saved += saved
    
    time.sleep(1)

print("\n" + "=" * 70)
print(f"✅ Total saved: {total_saved} images")
print("=" * 70)
