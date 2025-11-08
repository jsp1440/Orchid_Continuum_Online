#!/usr/bin/env python3
"""
Quick test: Show how many GBIF image URLs we can extract
"""
import os
import psycopg2
import requests

print("🌍 GBIF URL EXTRACTION TEST")
print("=" * 70)

# Connect to database
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Get total count of species with GBIF keys
cur.execute("SELECT COUNT(*) FROM orchid_taxonomy WHERE gbif_taxon_key IS NOT NULL")
total_with_gbif = cur.fetchone()[0]

print(f"\n📊 Species with GBIF taxon keys: {total_with_gbif:,}")

# Test with first 5 species
cur.execute("""
    SELECT id, scientific_name, gbif_taxon_key
    FROM orchid_taxonomy
    WHERE gbif_taxon_key IS NOT NULL
    LIMIT 5
""")

species = cur.fetchall()
print(f"\n🧪 Testing with 5 species:\n")

total_images_found = 0

for taxonomy_id, name, gbif_key in species:
    url = f"https://api.gbif.org/v1/occurrence/search"
    params = {
        'taxonKey': gbif_key,
        'mediaType': 'StillImage',
        'limit': 20
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        image_count = 0
        for record in data.get('results', []):
            for media in record.get('media', []):
                if media.get('type') == 'StillImage':
                    image_count += 1
        
        total_images_found += image_count
        print(f"   {name[:40]:<40} → {image_count} images")
        
    except Exception as e:
        print(f"   {name[:40]:<40} → Error: {e}")

print(f"\n✅ Found {total_images_found} images from 5 species")
print(f"\n🎯 PROJECTION:")
print(f"   If average holds across all {total_with_gbif:,} species with GBIF keys:")
print(f"   Estimated total: ~{(total_images_found / 5) * total_with_gbif:,.0f} images from GBIF!")
print()

cur.close()
conn.close()
