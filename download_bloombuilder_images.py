"""
Download images specifically for the 10 BloomBuilder species
Using GBIF API for living photos and herbarium specimens
"""
import os
import requests
import time
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL')

# Get BloomBuilder species from database
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

cursor.execute("""
    SELECT bs.id, bs.genus, bs.species, bs.common_name, ot.id as taxonomy_id
    FROM bloombuilder_species bs
    JOIN orchid_taxonomy ot ON ot.scientific_name = bs.genus || ' ' || bs.species
    ORDER BY bs.genus, bs.species
""")

species_list = cursor.fetchall()
cursor.close()
conn.close()

print("=" * 70)
print("🌺 BLOOMBUILDER IMAGE DOWNLOADER")
print("=" * 70)
print(f"Downloading images for {len(species_list)} species\n")

GBIF_API = "https://api.gbif.org/v1/occurrence/search"

def download_gbif_images(scientific_name, taxonomy_id, limit=15):
    """Download images from GBIF for a species"""
    print(f"\n{'─' * 70}")
    print(f"🔍 {scientific_name}")
    print(f"{'─' * 70}")
    
    params = {
        'scientificName': scientific_name,
        'mediaType': 'StillImage',
        'hasCoordinate': 'true',
        'limit': limit
    }
    
    try:
        response = requests.get(GBIF_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = data.get('results', [])
        print(f"  Found {len(results)} GBIF records with images")
        
        saved = 0
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        for record in results:
            media = record.get('media', [])
            for img in media:
                image_url = img.get('identifier')
                if not image_url:
                    continue
                
                # Check if exists
                cursor.execute("SELECT id FROM orchid_images WHERE image_url = %s", (image_url,))
                if cursor.fetchone():
                    continue
                
                # Insert
                try:
                    cursor.execute("""
                        INSERT INTO orchid_images (
                            taxonomy_id, image_url, image_source, image_type,
                            gbif_occurrence_key, observer_name, institution_code,
                            latitude, longitude, country, locality,
                            observation_date, image_license
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        taxonomy_id,
                        image_url,
                        'GBIF',
                        'living_photo',
                        str(record.get('key', '')),
                        record.get('recordedBy', ''),
                        record.get('institutionCode', ''),
                        record.get('decimalLatitude'),
                        record.get('decimalLongitude'),
                        record.get('country', ''),
                        record.get('locality', ''),
                        record.get('eventDate'),
                        img.get('license', '')
                    ))
                    conn.commit()
                    saved += 1
                    print(f"    ✅ Saved image {saved}")
                except Exception as e:
                    conn.rollback()
                    print(f"    ⚠️  Error: {e}")
        
        cursor.close()
        conn.close()
        
        print(f"  📊 Total saved: {saved} images")
        return saved
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return 0


# Download for all species
total_images = 0
for species in species_list:
    scientific_name = f"{species['genus']} {species['species']}"
    count = download_gbif_images(scientific_name, species['taxonomy_id'], limit=20)
    total_images += count
    time.sleep(1)  # Rate limiting

print("\n" + "=" * 70)
print(f"✅ DOWNLOAD COMPLETE!")
print(f"📊 Total new images: {total_images}")
print("=" * 70)

# Show final counts
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

cursor.execute("""
    SELECT 
        bs.genus || ' ' || bs.species as scientific_name,
        COUNT(DISTINCT CASE WHEN oi.image_type = 'living_photo' THEN oi.id END) as photos,
        COUNT(DISTINCT CASE WHEN oi.image_type = 'herbarium_sheet' THEN oi.id END) as herbarium,
        COUNT(DISTINCT CASE WHEN oi.image_type = 'botanical_plate' THEN oi.id END) as plates
    FROM bloombuilder_species bs
    JOIN orchid_taxonomy ot ON ot.scientific_name = bs.genus || ' ' || bs.species
    LEFT JOIN orchid_images oi ON oi.taxonomy_id = ot.id
    GROUP BY bs.genus, bs.species
    ORDER BY bs.genus
""")

print("\n📋 BLOOMBUILDER IMAGE COUNTS:")
print(f"{'Species':<30} {'Photos':<10} {'Herbarium':<12} {'Plates':<10}")
print("=" * 65)
for row in cursor.fetchall():
    print(f"{row['scientific_name']:<30} {row['photos']:<10} {row['herbarium']:<12} {row['plates']:<10}")

cursor.close()
conn.close()
