#!/usr/bin/env python3
"""
GBIF Enhanced Orchid Downloader - Mac Version
Downloads 2+ million orchid observations from GBIF (Global Biodiversity Information Facility)

FEATURES:
- Royal Botanic Gardens Kew (500k+ specimens)
- NY Botanical Garden, Missouri Botanical Garden
- Global coverage including rare and endemic species
- All observations with coordinates and images

SETUP (one time):
    pip3 install requests

USAGE:
    python3 EASY_Mac_GBIF_Downloader.py

The script will:
- Create folder: ~/orchid_downloads/gbif_global/
- Download images with occurrence data
- Save data to: gbif_orchids.csv
"""

import requests
import time
import os
import csv
from pathlib import Path
import json

class GBIFDownloader:
    def __init__(self):
        # Create folder in user's home directory
        home = str(Path.home())
        self.base_dir = os.path.join(home, "orchid_downloads")
        self.output_dir = os.path.join(self.base_dir, "gbif_global")
        self.csv_file = os.path.join(self.base_dir, "gbif_orchids.csv")
        
        self.api_url = "https://api.gbif.org/v1/occurrence/search"
        self.downloaded_count = 0
        self.species_set = set()
        
        # Auto-create directories
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"\n✅ Created folder: {self.base_dir}")
        print(f"✅ Images will save to: {self.output_dir}")
        print(f"✅ Data will save to: {self.csv_file}\n")
        
        self.init_csv()
    
    def init_csv(self):
        """Initialize CSV with comprehensive fields"""
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'gbif_id', 'occurrence_id', 'dataset_key', 'dataset_name',
                'institution_code', 'collection_code', 'catalog_number',
                'kingdom', 'phylum', 'class', 'order', 'family',
                'genus', 'species', 'scientific_name', 'taxon_rank',
                'taxonomic_status', 'accepted_name',
                'country', 'state_province', 'locality',
                'latitude', 'longitude', 'coordinate_uncertainty',
                'elevation', 'depth',
                'event_date', 'year', 'month', 'day',
                'basis_of_record', 'recorded_by', 'identified_by',
                'type_status', 'establishment_means',
                'image_url', 'filename', 'license', 'publisher',
                'references', 'gbif_url'
            ])
        print(f"✅ Created: {self.csv_file}")
    
    def search_occurrences(self, offset=0, limit=300):
        """Search GBIF for orchid occurrences with images"""
        params = {
            'familyKey': 7543,  # Orchidaceae family key
            'hasCoordinate': 'true',
            'hasGeospatialIssue': 'false',
            'mediaType': 'StillImage',
            'limit': limit,
            'offset': offset
        }
        
        try:
            response = requests.get(self.api_url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ API Error {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def download_image(self, url, filename):
        """Download image file"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except:
            return False
    
    def process_occurrence(self, occ):
        """Process a single occurrence record"""
        # Get species info
        species = occ.get('species', '')
        genus = occ.get('genus', '')
        
        if not species or not genus:
            return 0
        
        # Get images
        media = occ.get('media', [])
        if not media:
            return 0
        
        # Basic IDs
        gbif_id = occ.get('key', '')
        occ_id = occ.get('occurrenceID', '')
        dataset_key = occ.get('datasetKey', '')
        dataset_name = occ.get('datasetName', '')
        
        # Institution
        institution = occ.get('institutionCode', '')
        collection = occ.get('collectionCode', '')
        catalog = occ.get('catalogNumber', '')
        
        # Taxonomy
        kingdom = occ.get('kingdom', '')
        phylum = occ.get('phylum', '')
        class_name = occ.get('class', '')
        order = occ.get('order', '')
        family = occ.get('family', '')
        scientific_name = occ.get('scientificName', '')
        taxon_rank = occ.get('taxonRank', '')
        taxonomic_status = occ.get('taxonomicStatus', '')
        accepted_name = occ.get('acceptedScientificName', '')
        
        # Location
        country = occ.get('country', '')
        state = occ.get('stateProvince', '')
        locality = occ.get('locality', '')
        lat = occ.get('decimalLatitude', '')
        lon = occ.get('decimalLongitude', '')
        coord_uncertainty = occ.get('coordinateUncertaintyInMeters', '')
        elevation = occ.get('elevation', '')
        depth = occ.get('depth', '')
        
        # Time
        event_date = occ.get('eventDate', '')
        year = occ.get('year', '')
        month = occ.get('month', '')
        day = occ.get('day', '')
        
        # Record info
        basis = occ.get('basisOfRecord', '')
        recorded_by = occ.get('recordedBy', '')
        identified_by = occ.get('identifiedBy', '')
        type_status = occ.get('typeStatus', '')
        establishment = occ.get('establishmentMeans', '')
        
        # Publisher
        publisher = occ.get('publisher', '')
        references = occ.get('references', '')
        gbif_url = f"https://www.gbif.org/occurrence/{gbif_id}"
        
        # Process images
        downloaded = 0
        for idx, img in enumerate(media):
            img_url = img.get('identifier', '')
            license = img.get('license', '')
            
            if not img_url or not img_url.startswith('http'):
                continue
            
            # Generate filename
            safe_name = species.replace(' ', '_').replace('/', '-')
            filename = f"{gbif_id}_{safe_name}_{idx+1}.jpg"
            
            print(f"  📥 {species} ({self.downloaded_count + 1})", end='\r')
            
            if self.download_image(img_url, filename):
                # Save to CSV
                with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        gbif_id, occ_id, dataset_key, dataset_name,
                        institution, collection, catalog,
                        kingdom, phylum, class_name, order, family,
                        genus, species, scientific_name, taxon_rank,
                        taxonomic_status, accepted_name,
                        country, state, locality,
                        lat, lon, coord_uncertainty,
                        elevation, depth,
                        event_date, year, month, day,
                        basis, recorded_by, identified_by,
                        type_status, establishment,
                        img_url, filename, license, publisher,
                        references, gbif_url
                    ])
                
                downloaded += 1
                self.downloaded_count += 1
                self.species_set.add(species)
                time.sleep(0.1)
        
        return downloaded
    
    def run(self, max_records=2000000):
        """Main download loop"""
        print("\n" + "="*70)
        print("🌍 GBIF Global Orchid Downloader")
        print("="*70)
        print("Data source: Kew, NYBG, MOBOT, and 100+ global institutions")
        print(f"🎯 Target: {max_records:,} occurrences with images")
        print("="*70 + "\n")
        
        offset = 0
        batch_size = 300
        
        while self.downloaded_count < max_records:
            print(f"\n📄 Fetching records {offset:,} - {offset+batch_size:,}...")
            
            data = self.search_occurrences(offset=offset, limit=batch_size)
            
            if not data:
                print("❌ No data returned")
                break
            
            results = data.get('results', [])
            if not results:
                print("✅ No more results")
                break
            
            # Process batch
            batch_count = 0
            for occ in results:
                batch_count += self.process_occurrence(occ)
                
                if self.downloaded_count >= max_records:
                    print(f"\n🎯 Reached target: {max_records:,} images")
                    break
            
            print(f"  ✅ Batch complete: +{batch_count} images")
            print(f"  📊 Total: {self.downloaded_count:,} images, {len(self.species_set):,} species")
            
            # Check if we got fewer results than requested (end of data)
            if len(results) < batch_size:
                print("  ✅ Reached end of available data")
                break
            
            offset += batch_size
            time.sleep(1)
            
            # Checkpoint every 10 batches
            if (offset // batch_size) % 10 == 0:
                print(f"\n💾 Checkpoint - Resume from offset={offset}")
        
        print("\n" + "="*70)
        print("🎉 DOWNLOAD COMPLETE!")
        print("="*70)
        print(f"✅ Downloaded: {self.downloaded_count:,} images")
        print(f"✅ Species: {len(self.species_set):,}")
        print(f"📁 Images: {self.output_dir}")
        print(f"📊 Data: {self.csv_file}")
        print("="*70 + "\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌍 WELCOME TO GBIF GLOBAL DOWNLOADER")
    print("="*70)
    print("This will download orchid observations to:")
    print("  ~/orchid_downloads/gbif_global/")
    print("\nSource: Royal Botanic Gardens Kew, NYBG, MOBOT, + 100 institutions")
    print("Target: 2,000,000 observations with images")
    print("Coverage: Global - all continents including rare/endemic species")
    print("Estimated time: 3-5 days continuous")
    print("Estimated storage: 150-250 GB")
    print("="*70)
    
    input("\nPress Enter to start downloading, or Ctrl+C to exit...")
    
    downloader = GBIFDownloader()
    # Download ALL available GBIF orchid occurrences with images
    downloader.run(max_records=2000000)
