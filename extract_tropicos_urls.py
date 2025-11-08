#!/usr/bin/env python3
"""
Tropicos Darwin Core Archive URL Extractor
Downloads and parses Tropicos specimen data to extract image URLs
"""
import os
import requests
import zipfile
import csv
from app import app, db
from models import OrchidTaxonomy, OrchidImages

print("🌿 TROPICOS IMAGE URL EXTRACTOR")
print("=" * 80)

TROPICOS_ARCHIVE_URL = "http://ipt.mobot.org:8080/ipt/archive.do?r=tropicosspecimens"
DOWNLOAD_PATH = "tropicos_data.zip"
EXTRACT_PATH = "tropicos_data"

def download_tropicos_archive():
    """Download the Tropicos Darwin Core Archive"""
    print("\n📥 Downloading Tropicos Darwin Core Archive...")
    print(f"   URL: {TROPICOS_ARCHIVE_URL}")
    print(f"   This may take a few minutes (4.7M+ records)...")
    
    try:
        response = requests.get(TROPICOS_ARCHIVE_URL, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(DOWNLOAD_PATH, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = (downloaded / total_size) * 100
                    print(f"\r   Progress: {pct:.1f}%", end='', flush=True)
        
        print("\n   ✅ Download complete!")
        return True
        
    except Exception as e:
        print(f"\n   ❌ Download failed: {e}")
        return False


def extract_archive():
    """Extract the Darwin Core Archive"""
    print("\n📦 Extracting archive...")
    
    try:
        with zipfile.ZipFile(DOWNLOAD_PATH, 'r') as zip_ref:
            zip_ref.extractall(EXTRACT_PATH)
        print("   ✅ Extraction complete!")
        return True
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        return False


def parse_dwca_for_orchids():
    """
    Parse Darwin Core Archive and extract Orchidaceae image URLs
    DwC-A typically has:
    - occurrence.txt (main data)
    - multimedia.txt (image URLs)
    - meta.xml (structure definition)
    """
    print("\n🔍 Parsing for Orchidaceae specimens with images...")
    
    occurrence_file = os.path.join(EXTRACT_PATH, "occurrence.txt")
    multimedia_file = os.path.join(EXTRACT_PATH, "multimedia.txt")
    
    if not os.path.exists(occurrence_file):
        print(f"   ⚠️  occurrence.txt not found in archive")
        return
    
    # Read occurrences and filter for Orchidaceae
    print("   Reading occurrence records...")
    orchid_occurrences = {}
    
    with open(occurrence_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for i, row in enumerate(reader):
            if i % 100000 == 0 and i > 0:
                print(f"   Processed {i:,} records...", end='\r')
            
            family = row.get('family', '').lower()
            if 'orchid' in family:
                occurrence_id = row.get('id') or row.get('occurrenceID')
                orchid_occurrences[occurrence_id] = {
                    'scientific_name': row.get('scientificName'),
                    'genus': row.get('genus'),
                    'species': row.get('specificEpithet'),
                    'country': row.get('country'),
                    'latitude': row.get('decimalLatitude'),
                    'longitude': row.get('decimalLongitude'),
                    'year': row.get('year'),
                    'institution': row.get('institutionCode'),
                    'catalog_number': row.get('catalogNumber')
                }
    
    print(f"\n   ✅ Found {len(orchid_occurrences):,} Orchidaceae occurrences")
    
    # Read multimedia and link to orchid occurrences
    if not os.path.exists(multimedia_file):
        print("   ⚠️  multimedia.txt not found - no images available")
        return
    
    print("   Reading multimedia records...")
    images_found = 0
    
    with app.app_context():
        with open(multimedia_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for i, row in enumerate(reader):
                if i % 10000 == 0 and i > 0:
                    print(f"   Processed {i:,} media records, found {images_found} orchid images...", end='\r')
                
                occurrence_id = row.get('id') or row.get('CoreId')
                
                if occurrence_id in orchid_occurrences:
                    media_url = row.get('identifier') or row.get('accessURI')
                    media_type = row.get('type', '')
                    
                    if media_url and 'image' in media_type.lower():
                        occ = orchid_occurrences[occurrence_id]
                        
                        # Try to match to our taxonomy
                        species_match = None
                        if occ['scientific_name']:
                            species_match = OrchidTaxonomy.query.filter_by(
                                scientific_name=occ['scientific_name']
                            ).first()
                        
                        # Check if URL already exists
                        existing = OrchidImages.query.filter_by(
                            image_url=media_url
                        ).first()
                        
                        if not existing:
                            new_image = OrchidImages(
                                taxonomy_id=species_match.id if species_match else None,
                                image_url=media_url,
                                image_type='herbarium_sheet',
                                source='tropicos',
                                photographer=occ.get('institution', 'Tropicos/MBG'),
                                license='CC-BY-4.0',
                                herbarium_catalog_number=occ.get('catalog_number'),
                                country=occ.get('country'),
                                latitude=float(occ['latitude']) if occ.get('latitude') else None,
                                longitude=float(occ['longitude']) if occ.get('longitude') else None,
                                collection_year=int(occ['year']) if occ.get('year') else None
                            )
                            db.session.add(new_image)
                            images_found += 1
                            
                            if images_found % 1000 == 0:
                                db.session.commit()
        
        # Final commit
        db.session.commit()
        
        print(f"\n\n   ✅ Added {images_found:,} Tropicos image URLs to database")


def main():
    # Download archive
    if not os.path.exists(DOWNLOAD_PATH):
        if not download_tropicos_archive():
            return
    else:
        print(f"\n✓ Archive already downloaded: {DOWNLOAD_PATH}")
    
    # Extract archive
    if not os.path.exists(EXTRACT_PATH):
        if not extract_archive():
            return
    else:
        print(f"✓ Archive already extracted: {EXTRACT_PATH}")
    
    # Parse and extract URLs
    parse_dwca_for_orchids()
    
    print("\n" + "=" * 80)
    print("✅ TROPICOS URL EXTRACTION COMPLETE!")


if __name__ == '__main__':
    main()
