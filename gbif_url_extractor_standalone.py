#!/usr/bin/env python3
"""
GBIF Image URL Extractor - Standalone Version
Extracts image URLs from GBIF for all orchid species we have GBIF keys for
"""
import os
import psycopg2
import requests
import time
from datetime import datetime

print("🌍 GBIF IMAGE URL EXTRACTOR")
print("=" * 80)

# Connect to database directly
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# GBIF API configuration
GBIF_API = "https://api.gbif.org/v1"
BATCH_SIZE = 100  # Process in batches
MAX_IMAGES_PER_SPECIES = 50  # Limit per species

def get_gbif_occurrences_with_media(taxon_key, limit=50):
    """Get GBIF occurrence records that have media (images)"""
    url = f"{GBIF_API}/occurrence/search"
    params = {
        'taxonKey': taxon_key,
        'mediaType': 'StillImage',
        'limit': limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for record in data.get('results', []):
            media_urls = []
            for media in record.get('media', []):
                if media.get('type') == 'StillImage':
                    media_urls.append(media.get('identifier'))
            
            if media_urls:
                results.append({
                    'gbif_occurrence_id': str(record.get('key')),
                    'media_urls': media_urls,
                    'latitude': record.get('decimalLatitude'),
                    'longitude': record.get('decimalLongitude'),
                    'country': record.get('country'),
                    'year': record.get('year'),
                    'basis_of_record': record.get('basisOfRecord'),
                    'institution': record.get('institutionCode'),
                    'license': record.get('license', 'CC-BY-4.0')
                })
        
        return results
        
    except Exception as e:
        print(f"   ⚠️  Error fetching GBIF data for taxon {taxon_key}: {e}")
        return []


# Get all species with GBIF taxon keys
cur.execute("""
    SELECT id, scientific_name, gbif_taxon_key
    FROM orchid_taxonomy
    WHERE gbif_taxon_key IS NOT NULL
    ORDER BY id
    LIMIT 100
""")  # Start with first 100 species

species_list = cur.fetchall()
print(f"\n📊 Found {len(species_list):,} species with GBIF taxon keys (testing first 100)")
print(f"⏱️  Processing...")
print()

total_images_added = 0
total_urls_extracted = 0
species_with_images = 0

for i, (taxonomy_id, scientific_name, gbif_key) in enumerate(species_list, 1):
    try:
        # Get occurrences with media
        occurrences = get_gbif_occurrences_with_media(gbif_key, limit=MAX_IMAGES_PER_SPECIES)
        
        if occurrences:
            species_with_images += 1
            
            # Add each image URL to database
            for occ in occurrences:
                for media_url in occ['media_urls']:
                    # Check if URL already exists
                    cur.execute("SELECT id FROM orchid_images WHERE image_url = %s", (media_url,))
                    existing = cur.fetchone()
                    
                    if not existing:
                        # Insert new image record
                        cur.execute("""
                            INSERT INTO orchid_images (
                                taxonomy_id, image_url, image_type, source,
                                photographer, license, latitude, longitude, country,
                                collection_year, gbif_occurrence_id, basis_of_record
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            taxonomy_id,
                            media_url,
                            'living_photo',
                            'gbif',
                            occ.get('institution', 'GBIF Contributor'),
                            occ.get('license', 'CC-BY-4.0'),
                            occ.get('latitude'),
                            occ.get('longitude'),
                            occ.get('country'),
                            occ.get('year'),
                            occ.get('gbif_occurrence_id'),
                            occ.get('basis_of_record')
                        ))
                        total_images_added += 1
                    
                    total_urls_extracted += 1
            
            # Commit every batch
            if i % 10 == 0:
                conn.commit()
                print(f"   ✅ Progress {i}/{len(species_list)}: "
                      f"+{total_images_added:,} new images | "
                      f"{species_with_images} species with images")
        
        # Rate limiting
        time.sleep(0.2)
        
    except Exception as e:
        print(f"   ⚠️  Error processing {scientific_name}: {e}")
        conn.rollback()
        continue

# Final commit
conn.commit()

# Final report
print()
print("=" * 80)
print("✅ GBIF URL EXTRACTION COMPLETE (First 100 Species)!")
print()
print(f"📊 Statistics:")
print(f"   Species processed: {len(species_list):,}")
print(f"   Species with images: {species_with_images:,}")
print(f"   Total URLs extracted: {total_urls_extracted:,}")
print(f"   New image records added: {total_images_added:,}")
print()

# Database totals
cur.execute("SELECT COUNT(*) FROM orchid_images")
total_images = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM orchid_taxonomy")
total_species = cur.fetchone()[0]

print(f"🌺 Updated Database Totals:")
print(f"   Total images in database: {total_images:,}")
print(f"   Total species in taxonomy: {total_species:,}")
print()

cur.close()
conn.close()

print("🎯 Next step: Run this script again to process all 8,390 species!")
