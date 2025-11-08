#!/usr/bin/env python3
"""
ENHANCED REPLIT HARVESTER
- Regional targeting (Australia, PNG, SE Asia, Africa, Central America)
- ALL 54 metadata fields captured
- Database only (no Google Drive)
- Runs continuously
"""
import os
import time
import requests
import psycopg2
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import signal
import sys

DATABASE_URL = os.environ.get('DATABASE_URL')

# Priority regions
PRIORITY_REGIONS = {
    'Australia': ['AU'],
    'Papua New Guinea': ['PG'],
    'Southeast Asia': ['ID', 'MY', 'PH', 'TH', 'VN', 'LA', 'KH', 'MM', 'BN', 'TL', 'SG'],
    'Central America': ['CR', 'PA', 'GT', 'BZ', 'HN', 'SV', 'NI'],
    'Africa': ['KE', 'TZ', 'UG', 'RW', 'BI', 'ET', 'ZA', 'MG', 'CM', 'CD']
}

stats = {
    'cataloged': 0, 'failed': 0, 'start_time': time.time(),
    'by_region': {region: 0 for region in PRIORITY_REGIONS.keys()}
}
running = True

def signal_handler(sig, frame):
    global running
    print('\n\n🛑 Stopping harvester...')
    running = False

signal.signal(signal.SIGINT, signal_handler)

def get_species_batch(limit=100):
    """Get species needing images"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT ot.id, ot.scientific_name, ot.genus, ot.species
        FROM orchid_taxonomy ot
        LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
        GROUP BY ot.id, ot.scientific_name, ot.genus, ot.species
        HAVING COUNT(oi.id) < 30
        ORDER BY COUNT(oi.id) ASC, ot.scientific_name
        LIMIT %s
    """, (limit,))
    results = cur.fetchall()
    conn.close()
    return results

def fetch_gbif_images_all_regions(species_name, limit_per_region=10):
    """Fetch images from GBIF with regional targeting"""
    all_images = []
    
    # First: Global search (no country filter)
    all_images.extend(fetch_gbif_for_region(species_name, None, limit_per_region))
    
    # Then: Priority regions
    for region_name, country_codes in PRIORITY_REGIONS.items():
        for country_code in country_codes:
            images = fetch_gbif_for_region(species_name, country_code, limit_per_region)
            for img in images:
                img['priority_region'] = region_name
            all_images.extend(images)
            time.sleep(0.1)  # Rate limiting
    
    return all_images

def fetch_gbif_for_region(species_name, country_code=None, limit=10):
    """Fetch images from GBIF for specific region with ALL metadata"""
    url = "https://api.gbif.org/v1/occurrence/search"
    params = {
        'scientificName': species_name,
        'mediaType': 'StillImage',
        'limit': limit,
        'hasCoordinate': 'true'
    }
    
    if country_code:
        params['country'] = country_code
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            return []
        
        data = response.json()
        images = []
        
        for record in data.get('results', []):
            if not record.get('media'):
                continue
            
            for media in record['media']:
                if media.get('type') == 'StillImage' and media.get('identifier'):
                    # Extract ALL 54 metadata fields
                    img_data = {
                        # Core fields
                        'url': media.get('identifier'),
                        'source': 'GBIF',
                        'license': record.get('license', 'Unknown'),
                        'type': 'observation',
                        
                        # Geographic fields (10 fields)
                        'country': record.get('country'),
                        'state_province': record.get('stateProvince'),
                        'locality': record.get('locality'),
                        'latitude': record.get('decimalLatitude'),
                        'longitude': record.get('decimalLongitude'),
                        'elevation': record.get('elevation'),
                        'coordinate_precision': record.get('coordinateUncertaintyInMeters'),
                        'country_code': record.get('countryCode'),
                        'continent': record.get('continent'),
                        'verbatim_locality': record.get('verbatimLocality'),
                        
                        # Temporal fields (7 fields)
                        'observation_date': record.get('eventDate'),
                        'year': record.get('year'),
                        'month': record.get('month'),
                        'day': record.get('day'),
                        'date_identified': record.get('dateIdentified'),
                        
                        # Observer/Collection fields (12 fields)
                        'observer_name': record.get('recordedBy'),
                        'institution_code': record.get('institutionCode'),
                        'collection_code': record.get('collectionCode'),
                        'catalog_number': record.get('catalogNumber'),
                        'occurrence_id': record.get('occurrenceID'),
                        'gbif_occurrence_key': str(record.get('key', '')),
                        'identified_by': record.get('identifiedBy'),
                        'field_number': record.get('fieldNumber'),
                        'field_notes': record.get('fieldNotes'),
                        'collector_number': record.get('collectorNumber'),
                        'dataset_name': record.get('datasetName'),
                        'publisher': record.get('publisher'),
                        
                        # Specimen fields (7 fields)
                        'type_status': record.get('typeStatus'),
                        'individual_count': record.get('individualCount'),
                        'sex': record.get('sex'),
                        'life_stage': record.get('lifeStage'),
                        'reproductive_condition': record.get('reproductiveCondition'),
                        'preparations': record.get('preparations'),
                        'basis_of_record': record.get('basisOfRecord'),
                        
                        # Habitat fields (5 fields)
                        'habitat': record.get('habitat'),
                        'substrate': record.get('substrate'),
                        'associated_taxa': record.get('associatedTaxa'),
                        'sampling_protocol': record.get('samplingProtocol'),
                        'establishment_means': record.get('establishmentMeans'),
                        
                        # Image technical fields (6 fields)
                        'image_width': media.get('width'),
                        'image_height': media.get('height'),
                        'image_format': media.get('format'),
                        'image_creator': media.get('creator'),
                        'image_publisher': media.get('publisher'),
                        'image_rights_holder': media.get('rightsHolder'),
                        
                        # Remarks/Notes fields (5 fields)
                        'occurrence_remarks': record.get('occurrenceRemarks'),
                        'event_remarks': record.get('eventRemarks'),
                        'references': record.get('references'),
                        'occurrence_status': record.get('occurrenceStatus'),
                        'protocol': record.get('protocol')
                    }
                    images.append(img_data)
        
        return images
    except Exception as e:
        return []

def save_to_database(img_data, tax_id):
    """Save ALL metadata to database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO orchid_images (
                taxonomy_id, image_url, image_source, image_license, image_type,
                country, state_province, locality, latitude, longitude, elevation, 
                coordinate_precision, country_code, continent, verbatim_locality,
                observation_date, year_observed, month_observed, day_observed,
                observer_name, institution_code, collection_code, catalog_number,
                occurrence_id, gbif_occurrence_key, identified_by, field_number,
                field_notes, collector_number, dataset_name, publisher,
                type_status, individual_count, sex, life_stage, reproductive_condition,
                preparations, basis_of_record,
                habitat, substrate, associated_taxa, sampling_protocol, establishment_means,
                image_width, image_height, image_format, image_creator, 
                image_publisher, image_rights_holder,
                occurrence_remarks, event_remarks, references, occurrence_status, protocol,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                NOW(), NOW()
            )
            ON CONFLICT (image_url) DO NOTHING
        """, (
            tax_id, img_data['url'], img_data['source'], img_data['license'], img_data['type'],
            img_data.get('country'), img_data.get('state_province'), img_data.get('locality'),
            img_data.get('latitude'), img_data.get('longitude'), img_data.get('elevation'),
            img_data.get('coordinate_precision'), img_data.get('country_code'), 
            img_data.get('continent'), img_data.get('verbatim_locality'),
            img_data.get('observation_date'), img_data.get('year'), img_data.get('month'), img_data.get('day'),
            img_data.get('observer_name'), img_data.get('institution_code'), 
            img_data.get('collection_code'), img_data.get('catalog_number'),
            img_data.get('occurrence_id'), img_data.get('gbif_occurrence_key'),
            img_data.get('identified_by'), img_data.get('field_number'),
            img_data.get('field_notes'), img_data.get('collector_number'),
            img_data.get('dataset_name'), img_data.get('publisher'),
            img_data.get('type_status'), img_data.get('individual_count'),
            img_data.get('sex'), img_data.get('life_stage'), 
            img_data.get('reproductive_condition'), img_data.get('preparations'),
            img_data.get('basis_of_record'),
            img_data.get('habitat'), img_data.get('substrate'), 
            img_data.get('associated_taxa'), img_data.get('sampling_protocol'),
            img_data.get('establishment_means'),
            img_data.get('image_width'), img_data.get('image_height'),
            img_data.get('image_format'), img_data.get('image_creator'),
            img_data.get('image_publisher'), img_data.get('image_rights_holder'),
            img_data.get('occurrence_remarks'), img_data.get('event_remarks'),
            img_data.get('references'), img_data.get('occurrence_status'),
            img_data.get('protocol')
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def process_species(species_data):
    """Process one species with regional targeting"""
    tax_id, sci_name, genus, sp = species_data
    
    # Fetch from all regions
    images = fetch_gbif_images_all_regions(sci_name, limit_per_region=3)
    
    if not images:
        return 0
    
    cataloged = 0
    for img in images[:30]:
        if save_to_database(img, tax_id):
            stats['cataloged'] += 1
            cataloged += 1
            
            # Track by region
            region = img.get('priority_region')
            if region and region in stats['by_region']:
                stats['by_region'][region] += 1
        else:
            stats['failed'] += 1
        
        time.sleep(0.05)
    
    elapsed_min = (time.time() - stats['start_time']) / 60
    rate = stats['cataloged'] / elapsed_min if elapsed_min > 0 else 0
    
    if cataloged > 0:
        print(f"[✅] {sci_name}: {cataloged} images | RATE: {rate:.1f}/min | TOTAL: {stats['cataloged']}")
    
    return cataloged

print("=" * 80)
print("🌺 ENHANCED REPLIT HARVESTER - REGIONAL TARGETING + ALL METADATA")
print("=" * 80)
print("Regions: Australia, Papua New Guinea, SE Asia, Central America, Africa")
print("Metadata: ALL 54 fields captured")
print("Press Ctrl+C to stop\n")

cycle = 0
while running:
    cycle += 1
    print(f"\n{'─' * 80}")
    print(f"CYCLE #{cycle} - {datetime.now().strftime('%I:%M:%S %p')}")
    print(f"{'─' * 80}")
    
    species_batch = get_species_batch(50)
    if not species_batch:
        print("✅ All species have 30+ images! Job complete.")
        break
    
    print(f"Processing {len(species_batch)} species...\n")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(process_species, species_batch))
    
    elapsed = (time.time() - stats['start_time']) / 60
    
    print(f"\n📊 CYCLE #{cycle} COMPLETE")
    print(f"   Total cataloged: {stats['cataloged']} | Failed: {stats['failed']}")
    print(f"   Runtime: {elapsed:.1f} min | Rate: {stats['cataloged']/elapsed:.1f}/min")
    print(f"\n🌍 BY REGION:")
    for region, count in stats['by_region'].items():
        if count > 0:
            print(f"   {region}: {count} images")
    
    if not running:
        break
    
    time.sleep(5)

print(f"\n{'=' * 80}")
print(f"🎉 HARVESTER STOPPED")
print(f"   Total cataloged: {stats['cataloged']}")
print(f"   Failed: {stats['failed']}")
print(f"   Runtime: {(time.time() - stats['start_time'])/60:.1f} minutes")
print(f"={'=' * 80}\n")
