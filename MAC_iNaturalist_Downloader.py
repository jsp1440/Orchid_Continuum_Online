#!/usr/bin/env python3
"""
iNaturalist Orchid Data Downloader - Mac Version
Downloads CC-licensed orchid photos with 52+ data fields

SETUP (one time):
1. Open Terminal
2. Install Python 3: brew install python3 (if not already installed)
3. Install requests: pip3 install requests

USAGE:
    python3 MAC_iNaturalist_Downloader.py

The script will:
- Create folder: inaturalist_orchids/
- Download images with full metadata
- Save data to: orchid_data_52_fields.csv
- Can resume if interrupted (checkpoints every 10 pages)
"""

import requests
import json
import time
import os
from datetime import datetime
import csv

class OrchidDownloader:
    def __init__(self):
        self.base_url = "https://api.inaturalist.org/v1"
        self.output_dir = "inaturalist_orchids"
        self.csv_file = "orchid_data_52_fields.csv"
        self.downloaded_count = 0
        self.species_set = set()
        
        os.makedirs(self.output_dir, exist_ok=True)
        self.init_csv()
    
    def init_csv(self):
        """Initialize CSV with 52 comprehensive fields"""
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                # OBSERVATION IDs
                'observation_id', 'uuid', 'url', 'created_at', 'updated_at',
                # TAXONOMY (11 levels)
                'kingdom', 'phylum', 'class', 'order', 'family', 'subfamily', 
                'tribe', 'genus', 'species', 'subspecies', 'variety',
                'taxon_id', 'rank', 'ancestry', 'common_name',
                # ECOLOGY
                'native', 'introduced', 'endemic', 'threatened', 'extinct', 'captive',
                # LOCATION (10 fields)
                'latitude', 'longitude', 'accuracy_meters', 'location',
                'country', 'state', 'county', 'elevation_m', 'uncertainty_m',
                # TIME
                'observed_date', 'observed_time', 'timezone', 
                # QUALITY
                'quality_grade', 'agreements', 'disagreements', 'id_count', 'verified',
                # OBSERVER
                'username', 'user_id',
                # PHOTOS
                'photo_count', 'image_url', 'filename', 'license', 'attribution',
                # LINKS
                'wikipedia', 'species_obs_count',
                # NOTES
                'description', 'tags', 'habitat_notes'
            ])
        print(f"✅ Created: {self.csv_file}")
    
    def parse_taxonomy(self, taxon):
        """Extract complete taxonomic hierarchy"""
        tax = {'kingdom':'', 'phylum':'', 'class':'', 'order':'', 'family':'',
               'subfamily':'', 'tribe':'', 'genus':'', 'species':'', 
               'subspecies':'', 'variety':''}
        
        for ancestor in taxon.get('ancestors', []):
            rank = ancestor.get('rank', '').lower()
            if rank in tax:
                tax[rank] = ancestor.get('name', '')
        
        current_rank = taxon.get('rank', '').lower()
        current_name = taxon.get('name', '')
        if current_rank in tax:
            tax[current_rank] = current_name
        
        return tax
    
    def search_observations(self, page=1, per_page=200):
        """Search iNaturalist API"""
        params = {
            'taxon_id': 47217,  # Orchidaceae
            'quality_grade': 'research',
            'photos': 'true',
            'license': 'cc-by,cc-by-nc,cc-by-sa,cc-by-nd,cc0',
            'per_page': per_page,
            'page': page,
            'order': 'desc',
            'order_by': 'created_at'
        }
        
        try:
            response = requests.get(f"{self.base_url}/observations", params=params, timeout=30)
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
        except Exception as e:
            print(f"  ⚠️ Download error: {e}")
            return False
    
    def process_observation(self, obs):
        """Extract all data and download images"""
        taxon = obs.get('taxon', {})
        if not taxon or taxon.get('rank') != 'species':
            return 0
        
        # Basic IDs
        obs_id = obs['id']
        uuid = obs.get('uuid', '')
        url = obs.get('uri', '')
        created = obs.get('created_at', '')
        updated = obs.get('updated_at', '')
        
        # Taxonomy
        tax = self.parse_taxonomy(taxon)
        taxon_id = taxon.get('id', '')
        rank = taxon.get('rank', '')
        ancestry = taxon.get('ancestry', '')
        common = taxon.get('preferred_common_name', '')
        
        # Ecology
        native = taxon.get('native', '')
        introduced = taxon.get('introduced', '')
        endemic = taxon.get('endemic', '')
        threatened = taxon.get('threatened', '')
        extinct = taxon.get('extinct', '')
        captive = obs.get('captive', False)
        
        # Location
        coords = obs.get('geojson', {}).get('coordinates', [None, None])
        lon, lat = coords[0], coords[1]
        accuracy = obs.get('positional_accuracy', '')
        location = obs.get('place_guess', '')
        parts = [p.strip() for p in location.split(',')] if location else []
        country = parts[-1] if len(parts) > 0 else ''
        state = parts[-2] if len(parts) > 1 else ''
        county = parts[-3] if len(parts) > 2 else ''
        uncertainty = obs.get('public_positional_accuracy', '')
        
        # Time
        obs_date = obs.get('observed_on', '')
        obs_time = obs.get('time_observed_at', '')
        timezone = obs.get('observed_time_zone', '')
        
        # Quality
        quality = obs.get('quality_grade', '')
        agreements = obs.get('num_identification_agreements', 0)
        disagreements = obs.get('identification_disagreements_count', 0)
        id_count = len(obs.get('identifications', []))
        verified = obs.get('identifications_most_agree', False)
        
        # Observer
        user = obs.get('user', {})
        username = user.get('login', '')
        user_id = user.get('id', '')
        
        # Notes
        description = obs.get('description', '')
        tags = ','.join(obs.get('tags', []))
        annotations = json.dumps(obs.get('annotations', []))
        
        # Links
        wiki = taxon.get('wikipedia_url', '')
        species_count = taxon.get('observations_count', 0)
        
        # Download photos
        photos = obs.get('photos', [])
        downloaded = 0
        
        for idx, photo in enumerate(photos):
            license = photo.get('license_code', '')
            attribution = photo.get('attribution', '')
            img_url = photo.get('url', '').replace('square', 'original')
            
            if not img_url:
                continue
            
            safe_name = tax['species'].replace(' ', '_').replace('/', '-')
            filename = f"{obs_id}_{safe_name}_{idx+1}.jpg"
            
            print(f"  📥 {tax['species']} ({idx+1}/{len(photos)})")
            
            if self.download_image(img_url, filename):
                with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        obs_id, uuid, url, created, updated,
                        tax['kingdom'], tax['phylum'], tax['class'], tax['order'],
                        tax['family'], tax['subfamily'], tax['tribe'], tax['genus'],
                        tax['species'], tax['subspecies'], tax['variety'],
                        taxon_id, rank, ancestry, common,
                        native, introduced, endemic, threatened, extinct, captive,
                        lat, lon, accuracy, location, country, state, county, '', uncertainty,
                        obs_date, obs_time, timezone,
                        quality, agreements, disagreements, id_count, verified,
                        username, user_id,
                        len(photos), img_url, filename, license, attribution,
                        wiki, species_count,
                        description, tags, annotations
                    ])
                
                downloaded += 1
                self.downloaded_count += 1
                self.species_set.add(tax['species'])
                time.sleep(0.1)
        
        return downloaded
    
    def run(self, max_pages=500, start_page=1):
        """Main download loop"""
        print("\n" + "="*70)
        print("🌺 iNaturalist Orchid Downloader")
        print("="*70)
        print(f"📊 52+ fields: taxonomy, ecology, habitat, geography")
        print(f"🎯 Target: {max_pages} pages × 200 = {max_pages*200:,} observations")
        print(f"📁 Saving to: {self.output_dir}/")
        print(f"📝 Data file: {self.csv_file}")
        print("="*70 + "\n")
        
        for page in range(start_page, start_page + max_pages):
            print(f"\n📄 Page {page}/{start_page+max_pages-1}...")
            
            data = self.search_observations(page=page)
            if not data:
                print("❌ No data. Stopping.")
                break
            
            results = data.get('results', [])
            if not results:
                print("✅ All done!")
                break
            
            print(f"  Processing {len(results)} observations...")
            
            page_count = 0
            for obs in results:
                page_count += self.process_observation(obs)
            
            print(f"  ✅ Downloaded: {page_count} images")
            print(f"  📊 Total: {self.downloaded_count:,} images, {len(self.species_set):,} species")
            
            time.sleep(1)
            
            if page % 10 == 0:
                print(f"\n💾 Checkpoint saved. To resume: edit line 289 to start_page={page+1}")
        
        print("\n" + "="*70)
        print("🎉 DOWNLOAD COMPLETE!")
        print("="*70)
        print(f"✅ Downloaded: {self.downloaded_count:,} images")
        print(f"✅ Species: {len(self.species_set):,}")
        print(f"📁 Images: {self.output_dir}/")
        print(f"📊 Data: {self.csv_file}")
        print("="*70 + "\n")


if __name__ == "__main__":
    downloader = OrchidDownloader()
    
    # CUSTOMIZE HERE:
    # Test: 1 page (~200 observations)
    downloader.run(max_pages=1, start_page=1)
    
    # Full download: 500 pages (~100,000 observations, ~150,000 images)
    # downloader.run(max_pages=500, start_page=1)
    
    # Resume from page 50:
    # downloader.run(max_pages=450, start_page=50)
