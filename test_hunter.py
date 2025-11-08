#!/usr/bin/env python3
"""
Test version of targeted species hunter - tests with 3 species
"""
import os
import json
import time
import requests
import psycopg2
from datetime import datetime

INATURALIST_API = "https://api.inaturalist.org/v1"
GBIF_API = "https://api.gbif.org/v1"

def extract_inaturalist_metadata(observation):
    """Extract ALL metadata fields from iNaturalist observation"""
    images = []
    taxon = observation.get('taxon', {})
    location = observation.get('geojson', {}).get('coordinates', [None, None])
    
    for photo in observation.get('photos', []):
        metadata = {
            # Core identification
            'occurrence_key': str(observation.get('id')),
            'scientific_name': taxon.get('name'),
            
            # Image data
            'image_url': photo.get('url', '').replace('square', 'original'),
            'image_source': 'iNaturalist',
            'image_license': photo.get('license_code', 'CC-BY-NC'),
            
            # Location data (ALL fields)
            'latitude': location[1] if len(location) > 1 else None,
            'longitude': location[0] if len(location) > 0 else None,
            'coordinate_uncertainty': observation.get('positional_accuracy'),
            'country': observation.get('place_guess'),
            'locality': observation.get('place_guess'),
            
            # Temporal data
            'observation_date': observation.get('observed_on'),
            'year_observed': observation.get('observed_on_details', {}).get('year'),
            'month_observed': observation.get('observed_on_details', {}).get('month'),
            
            # Observer
            'observer_name': observation.get('user', {}).get('login'),
            
            # Specimen data
            'wild_specimen': observation.get('captive') == False,
            
            # Conservation
            'iucn_red_list_category': taxon.get('conservation_status', {}).get('status'),
            
            # Complete raw metadata (ALL remaining fields)
            'occurrence_metadata': json.dumps({
                'inat_id': observation.get('id'),
                'uuid': observation.get('uuid'),
                'taxon_id': taxon.get('id'),
                'quality_grade': observation.get('quality_grade'),
                'identifications_count': observation.get('identifications_count'),
                'num_identification_agreements': observation.get('num_identification_agreements'),
                'num_identification_disagreements': observation.get('num_identification_disagreements'),
                'comments_count': observation.get('comments_count'),
                'faves_count': observation.get('faves_count'),
            }),
            'media_metadata': json.dumps({
                'photo_id': photo.get('id'),
                'photo_uuid': photo.get('uuid'),
                'large_url': photo.get('url', '').replace('square', 'large'),
                'medium_url': photo.get('url', '').replace('square', 'medium'),
            })
        }
        images.append(metadata)
    
    return images

def clean_scientific_name(scientific_name):
    """Extract just genus and species (remove author citations)"""
    parts = scientific_name.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    return parts[0] if parts else scientific_name

def search_inaturalist(scientific_name, needed=10):
    """Search iNaturalist for species images"""
    clean_name = clean_scientific_name(scientific_name)
    print(f"   🔎 iNaturalist: {clean_name}...", end=" ", flush=True)
    
    try:
        response = requests.get(
            f"{INATURALIST_API}/observations",
            params={
                'taxon_name': clean_name,
                'photos': 'true',
                'quality_grade': 'research',
                'per_page': needed
            },
            timeout=10
        )
        response.raise_for_status()
        
        observations = response.json().get('results', [])
        images = []
        for obs in observations:
            images.extend(extract_inaturalist_metadata(obs))
        
        print(f"found {len(images)}")
        return images
    
    except Exception as e:
        print(f"error: {str(e)[:40]}")
        return []

def search_gbif(scientific_name, needed=10):
    """Search GBIF for species images with ALL metadata"""
    clean_name = clean_scientific_name(scientific_name)
    print(f"   🌍 GBIF: {clean_name}...", end=" ", flush=True)
    
    try:
        response = requests.get(
            f"{GBIF_API}/occurrence/search",
            params={
                'scientificName': clean_name,
                'mediaType': 'StillImage',
                'hasCoordinate': 'true',
                'limit': needed
            },
            timeout=10
        )
        response.raise_for_status()
        
        occurrences = response.json().get('results', [])
        images = []
        
        for occ in occurrences:
            for media in occ.get('media', []):
                if media.get('type') == 'StillImage':
                    metadata = {
                        # Core identification
                        'occurrence_key': str(occ.get('key')),
                        'scientific_name': occ.get('scientificName'),
                        
                        # Image data
                        'image_url': media.get('identifier'),
                        'image_source': 'GBIF',
                        'image_license': media.get('license'),
                        
                        # Location data (ALL fields)
                        'latitude': occ.get('decimalLatitude'),
                        'longitude': occ.get('decimalLongitude'),
                        'coordinate_uncertainty': occ.get('coordinateUncertaintyInMeters'),
                        'country': occ.get('country'),
                        'country_code': occ.get('countryCode'),
                        'state_province': occ.get('stateProvince'),
                        'locality': occ.get('locality'),
                        'continent': occ.get('continent'),
                        'elevation_meters': occ.get('elevation'),
                        
                        # Temporal data
                        'observation_date': occ.get('eventDate'),
                        'year_observed': occ.get('year'),
                        'month_observed': occ.get('month'),
                        
                        # Observer
                        'observer_name': occ.get('recordedBy'),
                        'institution_code': occ.get('institutionCode'),
                        
                        # Specimen data
                        'individual_count': occ.get('individualCount'),
                        'sex': occ.get('sex'),
                        'life_stage': occ.get('lifeStage'),
                        'reproductive_condition': occ.get('reproductiveCondition'),
                        'wild_specimen': occ.get('basisOfRecord') != 'PRESERVED_SPECIMEN',
                        
                        # Complete raw metadata
                        'occurrence_metadata': json.dumps({
                            'gbif_key': occ.get('key'),
                            'basis_of_record': occ.get('basisOfRecord'),
                            'catalog_number': occ.get('catalogNumber'),
                            'dataset_name': occ.get('datasetName'),
                            'publisher': occ.get('publisher'),
                        }),
                        'media_metadata': json.dumps(media)
                    }
                    images.append(metadata)
        
        print(f"found {len(images)}")
        return images
    
    except Exception as e:
        print(f"error: {str(e)[:40]}")
        return []

def insert_images(conn, taxonomy_id, images):
    """Insert images with ALL metadata fields"""
    cur = conn.cursor()
    inserted = 0
    
    for img in images:
        try:
            cur.execute("""
                INSERT INTO orchid_images (
                    taxonomy_id, gbif_occurrence_key, image_url, image_source,
                    wild_specimen, image_license, latitude, longitude,
                    coordinate_uncertainty, country, country_code, state_province,
                    locality, continent, elevation_meters, observation_date,
                    year_observed, month_observed, observer_name, institution_code,
                    individual_count, sex, life_stage, reproductive_condition,
                    iucn_red_list_category, occurrence_metadata, media_metadata,
                    created_at
                )
                SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                       %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                WHERE NOT EXISTS (
                    SELECT 1 FROM orchid_images WHERE image_url = %s
                )
            """, (
                taxonomy_id,
                img.get('occurrence_key'),
                img.get('image_url'),
                img.get('image_source'),
                img.get('wild_specimen'),
                img.get('image_license'),
                img.get('latitude'),
                img.get('longitude'),
                img.get('coordinate_uncertainty'),
                img.get('country'),
                img.get('country_code'),
                img.get('state_province'),
                img.get('locality'),
                img.get('continent'),
                img.get('elevation_meters'),
                img.get('observation_date'),
                img.get('year_observed'),
                img.get('month_observed'),
                img.get('observer_name'),
                img.get('institution_code'),
                img.get('individual_count'),
                img.get('sex'),
                img.get('life_stage'),
                img.get('reproductive_condition'),
                img.get('iucn_red_list_category'),
                img.get('occurrence_metadata'),
                img.get('media_metadata'),
                datetime.now(),
                img.get('image_url')  # for WHERE NOT EXISTS
            ))
            
            if cur.rowcount > 0:
                inserted += 1
        except Exception as e:
            conn.rollback()
            print(f"\n      ⚠️  Error inserting: {str(e)[:50]}")
            continue
    
    conn.commit()
    cur.close()
    return inserted

def main():
    print("\n" + "="*80)
    print("🌺 TESTING TARGETED HUNTER WITH ALL METADATA FIELDS")
    print("="*80)
    
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Get 3 species with no images
    cur.execute("""
        SELECT ot.id, ot.scientific_name
        FROM orchid_taxonomy ot
        LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
        WHERE ot.scientific_name IS NOT NULL
        AND ot.scientific_name != ''
        GROUP BY ot.id, ot.scientific_name
        HAVING COUNT(oi.id) = 0
        ORDER BY ot.scientific_name
        LIMIT 3
    """)
    
    species_list = cur.fetchall()
    print(f"\n📋 Testing with {len(species_list)} species:\n")
    
    total_inserted = 0
    
    for i, (tax_id, sci_name) in enumerate(species_list, 1):
        print(f"[{i}/3] 🎯 {sci_name}")
        
        all_images = []
        
        # Search iNaturalist
        inat_images = search_inaturalist(sci_name, needed=10)
        all_images.extend(inat_images)
        time.sleep(1)
        
        # Search GBIF
        gbif_images = search_gbif(sci_name, needed=10)
        all_images.extend(gbif_images)
        time.sleep(1)
        
        # Insert to database
        if all_images:
            print(f"   📊 Total found: {len(all_images)} images")
            inserted = insert_images(conn, tax_id, all_images)
            total_inserted += inserted
            print(f"   ✅ Inserted: {inserted} new images to database\n")
        else:
            print(f"   ⚠️  No images found\n")
    
    cur.close()
    conn.close()
    
    print("="*80)
    print(f"📊 TEST COMPLETE - Inserted {total_inserted} images with ALL metadata fields!")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
